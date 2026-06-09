#!/usr/bin/env python3
"""Visual QA — analyze game screenshots via Gemini or OpenAI models.

Three modes:
  Static:   visual_qa.py --model <selector> [--context "..."] reference.png screenshot.png
  Dynamic:  visual_qa.py --model <selector> [--context "..."] reference.png frame1.png frame2.png ...
  Question: visual_qa.py --model <selector> --question "what's wrong?" screenshot.png [frame2.png ...]

Static mode (2 images): reference + single game screenshot. For static scenes.
Dynamic mode (3+ images): reference + frame sequence at 2 FPS cadence. For motion.
Question mode: free-form question + any number of screenshots. No reference needed.

--context: Task context (Goal, Requirements, Verify) for goal verification.
--question: Free-form question about the screenshots (replaces reference-based modes).
--model: Required model selector, e.g. gemini:<model> or openai:<model>.
--log: Path to JSONL log file for debug logging.
Requires: GEMINI_API_KEY / GOOGLE_API_KEY for Gemini, or OPENAI_API_KEY for OpenAI.
Supports OpenAI-compatible providers via config in .godotmaker/config.yaml:
  openai_base_url: https://your-provider.com/v1
  openai_api_key_env: YOUR_API_KEY_ENV
"""

import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent
STATIC_PROMPT = PROMPTS_DIR / "static_prompt.md"
DYNAMIC_PROMPT = PROMPTS_DIR / "dynamic_prompt.md"
QUESTION_PROMPT = PROMPTS_DIR / "question_prompt.md"
CRITERIA_PROMPT = PROMPTS_DIR / "criteria.md"
CONFIG_FILE = Path(__file__).resolve().parents[4] / ".godotmaker" / "config.yaml"


def _load_project_config() -> dict[str, str]:
    """Read simple top-level scalar values from .godotmaker/config.yaml."""
    if not CONFIG_FILE.exists():
        return {}
    config = {}
    try:
        for raw_line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
            if raw_line.startswith((" ", "\t")):
                continue
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and value:
                config[key] = value
    except OSError:
        return {}
    return config


def _get_openai_client_config(config: dict[str, str]) -> dict:
    """Build OpenAI client configuration from project config."""
    client_config = {}
    
    # Get base URL if configured
    base_url = config.get("openai_base_url")
    if base_url:
        client_config["base_url"] = base_url
    
    # Get API key from environment variable if configured
    api_key_env = config.get("openai_api_key_env")
    if api_key_env:
        api_key = os.environ.get(api_key_env)
        if api_key:
            client_config["api_key"] = api_key
    
    return client_config

def _mime_for_image(path: Path) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/png")


def _image_data_url(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{_mime_for_image(path)};base64,{b64}"


def _split_model_selector(selector: str | None) -> tuple[str, str]:
    raw = (selector or "").strip()
    if not raw:
        print("Error: --model is required", file=sys.stderr)
        sys.exit(1)
    if ":" in raw:
        provider, model = raw.split(":", 1)
        if provider and model:
            return provider, model
    if raw == "gemini":
        return "gemini", "gemini-2.5-flash"
    if raw == "openai":
        return "openai", "gpt-5.5"
    if raw in {"native", "codex"}:
        print(
            f"Error: {raw} VQA is handled by the agent runtime, not visual_qa.py",
            file=sys.stderr,
        )
        sys.exit(1)
    return "gemini", raw


def log_entry(log_path, *, mode, model, query, files, output):
    """Append a JSONL log entry."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "model": model,
        "query": query,
        "files": files,
        "output": output,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    args = sys.argv[1:]
    context = None
    question = None
    model_selector = None
    log_path = None

    # Parse named flags
    while len(args) >= 2:
        if args[0] == "--context":
            context = args[1]
            args = args[2:]
        elif args[0] == "--question":
            question = args[1]
            args = args[2:]
        elif args[0] == "--model":
            model_selector = args[1]
            args = args[2:]
        elif args[0] == "--log":
            log_path = args[1]
            args = args[2:]
        else:
            break

    if question:
        # Question mode: just screenshots, no reference
        if len(args) < 1:
            print(f"Usage: {sys.argv[0]} --question \"...\" <screenshot.png> [frame2.png ...]", file=sys.stderr)
            sys.exit(1)
        paths = [Path(p) for p in args]
        for p in paths:
            if not p.exists():
                print(f"Error: {p} not found", file=sys.stderr)
                sys.exit(1)

        prompt = QUESTION_PROMPT.read_text(encoding="utf-8")
        prompt += f"\n\n## Question\n\n{question}\n"
        if context:
            prompt += f"\n## Additional Context\n\n{context}\n"

        mode = "question"
        query = question
        desc = f"question ({len(paths)} image{'s' if len(paths) != 1 else ''})"
    else:
        # Reference-based modes (static/dynamic)
        if len(args) < 2:
            print(f"Usage: {sys.argv[0]} [--context \"...\"] <reference.png> <screenshot.png> [frame2.png ...]", file=sys.stderr)
            print(f"       {sys.argv[0]} --question \"...\" <screenshot.png> [frame2.png ...]", file=sys.stderr)
            sys.exit(1)

        paths = [Path(p) for p in args]
        for p in paths:
            if not p.exists():
                print(f"Error: {p} not found", file=sys.stderr)
                sys.exit(1)

        static = len(paths) == 2
        prompt = (STATIC_PROMPT if static else DYNAMIC_PROMPT).read_text(
            encoding="utf-8"
        )
        prompt += "\n\n" + CRITERIA_PROMPT.read_text(encoding="utf-8")
        if context:
            prompt += f"\n\n## Task Context\n\n{context}\n"

        if static:
            mode = "static"
            desc = "static (reference + screenshot)"
        else:
            mode = "dynamic"
            desc = f"dynamic (reference + {len(paths) - 1} frames)"

        query = context or ""

    provider, model = _split_model_selector(model_selector)
    full_model = f"{provider}:{model}"
    print(f"Analyzing {desc} with {full_model}...", file=sys.stderr)
    try:
        if provider == "gemini":
            from google import genai
            from google.genai import types

            client = genai.Client()
            contents: list[types.Part | str] = [prompt]
            if question:
                for i, p in enumerate(paths, 1):
                    label = "Screenshot:" if len(paths) == 1 else f"Frame {i}:"
                    contents.append(label)
                    contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=_mime_for_image(p)))
            else:
                contents.append("Reference (visual target):")
                contents.append(types.Part.from_bytes(data=paths[0].read_bytes(), mime_type=_mime_for_image(paths[0])))
                if mode == "static":
                    contents.append("Game screenshot:")
                    contents.append(types.Part.from_bytes(data=paths[1].read_bytes(), mime_type=_mime_for_image(paths[1])))
                else:
                    for i, p in enumerate(paths[1:], 1):
                        contents.append(f"Frame {i}:")
                        contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=_mime_for_image(p)))
            response = client.models.generate_content(
                model=model,
                contents=contents,  # type: ignore[arg-type]
                config=types.GenerateContentConfig(
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                ),
            )
            output = response.text or ""
        elif provider == "openai":
            from openai import OpenAI

            config = _load_project_config()
            client_config = _get_openai_client_config(config)
            client = OpenAI(**client_config) if client_config else OpenAI()
            content = [{"type": "input_text", "text": prompt}]
            if question:
                for i, p in enumerate(paths, 1):
                    label = "Screenshot:" if len(paths) == 1 else f"Frame {i}:"
                    content.append({"type": "input_text", "text": label})
                    content.append({"type": "input_image", "image_url": _image_data_url(p)})
            else:
                content.append({"type": "input_text", "text": "Reference (visual target):"})
                content.append({"type": "input_image", "image_url": _image_data_url(paths[0])})
                if mode == "static":
                    content.append({"type": "input_text", "text": "Game screenshot:"})
                    content.append({"type": "input_image", "image_url": _image_data_url(paths[1])})
                else:
                    for i, p in enumerate(paths[1:], 1):
                        content.append({"type": "input_text", "text": f"Frame {i}:"})
                        content.append({"type": "input_image", "image_url": _image_data_url(p)})
            response = client.responses.create(
                model=model,
                input=[{"role": "user", "content": content}],
            )
            output = getattr(response, "output_text", "") or ""
        else:
            print(f"Error: unsupported VQA provider: {provider}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {provider} API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not output:
        print(f"Error: {provider} returned no text (possible safety block)", file=sys.stderr)
        sys.exit(1)

    print(output)

    if log_path:
        log_entry(log_path, mode=mode, model=full_model, query=query,
                  files=[str(p) for p in paths], output=output)


if __name__ == "__main__":
    main()
