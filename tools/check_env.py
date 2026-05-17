#!/usr/bin/env python3
"""Check that the GodotMaker development environment is correctly set up.

Verifies: Git, Python, Node.js, Godot, selected coding agent, API keys, pip
packages.

Usage:
    python tools/check_env.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from agent_runtime import AGENT_CLAUDE_CODE, AGENT_CODEX, detect_agent, read_godot_path


class EnvCheck:
    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.warnings: list[str] = []

    def ok(self, msg: str):
        self.passed.append(msg)
        print(f"  [PASS] {msg}")

    def fail(self, msg: str):
        self.failed.append(msg)
        print(f"  [FAIL] {msg}")

    def warn(self, msg: str):
        self.warnings.append(msg)
        print(f"  [WARN] {msg}")


def get_version(cmd: str, pattern: str = r"(\d+(?:\.\d+)+)") -> str | None:
    """Run `cmd --version` and extract version number."""
    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout + result.stderr
        match = re.search(pattern, output)
        return match.group(1) if match else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def parse_version(v: str) -> tuple[int, ...]:
    """Parse '4.4.1' to (4, 4, 1)."""
    return tuple(int(x) for x in v.split(".")[:3])


# ── Individual checks ──────────────────────────────────────────


def check_git(r: EnvCheck):
    print("\n--- Git ---")
    version = get_version("git")
    if not version:
        r.fail("Git not found. Install: https://git-scm.com/downloads")
        return

    if parse_version(version) >= (2, 30):
        r.ok(f"Git {version} (>= 2.30)")
    else:
        r.fail(f"Git {version} too old (>= 2.30 required)")

    # Check identity config
    for key, label in [("user.name", "user.name"), ("user.email", "user.email")]:
        try:
            res = subprocess.run(
                ["git", "config", key],
                capture_output=True, text=True, timeout=5,
            )
            val = res.stdout.strip()
            if val:
                r.ok(f"Git {label}: {val}")
            else:
                r.warn(f"Git {label} not set. Run: git config --global {key} \"...\"")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


def check_python(r: EnvCheck):
    print("\n--- Python ---")
    v = sys.version_info
    version = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 9):
        r.ok(f"Python {version} (>= 3.9)")
    else:
        r.fail(f"Python {version} too old (>= 3.9 required)")

    # Check key packages
    packages = {
        "google-genai": "google.genai",
        "requests": "requests",
        "pillow": "PIL",
        "numpy": "numpy",
    }
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
            r.ok(f"Package '{pkg_name}' installed")
        except ImportError:
            r.fail(f"Package '{pkg_name}' missing. Run: pip install {pkg_name}")


def check_node(r: EnvCheck):
    print("\n--- Node.js ---")
    version = get_version("node")
    if not version:
        r.fail("Node.js not found. Install: https://nodejs.org")
        return

    if int(version.split(".")[0]) >= 18:
        r.ok(f"Node.js {version} (>= 18)")
    else:
        r.fail(f"Node.js {version} too old (>= 18 required)")

    if shutil.which("npx"):
        r.ok("npx available")
    else:
        r.fail("npx not found (should come with Node.js)")


def _get_version_from_path(path: str, pattern: str = r"(\d+(?:\.\d+)+)") -> str | None:
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout + result.stderr
        match = re.search(pattern, output)
        return match.group(1) if match else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def check_godot(r: EnvCheck, project_dir: Path):
    print("\n--- Godot ---")
    configured = read_godot_path(project_dir)
    if configured:
        version = _get_version_from_path(configured)
        if version and parse_version(version)[:2] >= (4, 4):
            r.ok(f"Godot {version}, configured path: {configured}")
            return
        if version:
            r.fail(f"Configured Godot {version} too old at {configured}")
            return
        r.fail(f"Configured Godot path does not run: {configured}")
        return

    for cmd in ("godot", "godot4"):
        version = get_version(cmd)
        if version and parse_version(version)[:2] >= (4, 4):
            r.ok(f"Godot {version}, command: {cmd}")
            return
        elif version:
            r.fail(f"Godot {version} too old (>= 4.4 required)")
            return

    r.warn(
        "Godot not found on PATH. Provide the full path when running publish, "
        "or add it to PATH."
    )


def check_claude(r: EnvCheck):
    print("\n--- Claude Code ---")
    cmd = (
        shutil.which("claude")
        or shutil.which("claude.cmd")
        or shutil.which("claude.exe")
    )
    if cmd:
        r.ok(f"Claude Code found: {cmd}")
    else:
        r.fail("Claude Code not found. Install: npm install -g @anthropic-ai/claude-code")


def check_codex(r: EnvCheck, project_dir: Path):
    print("\n--- Codex ---")
    cmd = (
        shutil.which("codex")
        or shutil.which("codex.cmd")
        or shutil.which("codex.exe")
    )
    if not cmd:
        r.fail("Codex CLI not found. Install Codex before using agent: codex.")
        return
    version = get_version(cmd, pattern=r"(\d+(?:\.\d+)+)")
    r.ok(f"Codex CLI found: {cmd}" + (f" ({version})" if version else ""))

    mapping = project_dir / ".agents" / "references" / "runtime-mapping.md"
    skills = project_dir / ".agents" / "skills"
    config = project_dir / ".agents" / "godotmaker.yaml"
    for path, label in [
        (skills, ".agents/skills"),
        (mapping, ".agents/references/runtime-mapping.md"),
        (config, ".agents/godotmaker.yaml"),
    ]:
        if path.exists():
            r.ok(f"{label} present")
        else:
            r.fail(f"{label} missing; re-run publish with --agent codex")

    try:
        result = subprocess.run(
            [cmd, "mcp", "list"],
            cwd=str(project_dir),
            capture_output=True, text=True, timeout=15,
        )
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode == 0 and "godot" in output:
            r.ok("Codex MCP server 'godot' configured")
        elif result.returncode == 0:
            r.fail("Codex MCP server 'godot' missing; re-run publish")
        else:
            r.fail("Could not list Codex MCP servers")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        r.fail("Could not list Codex MCP servers")


def check_selected_agent(r: EnvCheck, project_dir: Path):
    agent = detect_agent(project_dir)
    print(f"\n--- Selected Agent ({agent}) ---")
    if agent == AGENT_CODEX:
        check_codex(r, project_dir)
    elif agent == AGENT_CLAUDE_CODE:
        check_claude(r)
    else:
        r.fail(f"Unsupported GodotMaker agent: {agent}")


def check_api_keys(r: EnvCheck):
    print("\n--- API Keys ---")
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if google_key:
        masked = google_key[:8] + "..." + google_key[-4:] if len(google_key) > 12 else "***"
        r.ok(f"GOOGLE_API_KEY set ({masked})")

        # Quick connectivity test
        try:
            from google import genai  # noqa: F401
            r.ok("google-genai import OK")
        except Exception as e:
            r.warn(f"google-genai import failed: {e}")
    else:
        r.fail(
            "GOOGLE_API_KEY not set (required for image gen + VQA). "
            "Get one: https://aistudio.google.com/apikey"
        )

    # Optional keys
    if os.environ.get("XAI_API_KEY"):
        r.ok("XAI_API_KEY set (optional)")
    else:
        r.warn("XAI_API_KEY not set (optional, cheaper image generation)")

    if os.environ.get("TRIPO3D_API_KEY"):
        r.ok("TRIPO3D_API_KEY set (optional)")
    else:
        r.warn("TRIPO3D_API_KEY not set (optional, 3D model generation)")


# ── Main ───────────────────────────────────────────────────────


def main():
    print("GodotMaker Environment Check")
    print("=" * 40)

    r = EnvCheck()
    project_dir = Path(__file__).resolve().parent.parent

    check_git(r)
    check_python(r)
    check_node(r)
    check_godot(r, project_dir)
    check_selected_agent(r, project_dir)
    check_api_keys(r)

    # Summary
    total = len(r.passed) + len(r.failed) + len(r.warnings)
    print(f"\n{'=' * 40}")
    print(f"Total: {total} checks")
    print(f"  PASS: {len(r.passed)}")
    print(f"  FAIL: {len(r.failed)}")
    print(f"  WARN: {len(r.warnings)}")

    if r.failed:
        print("\nFailed checks:")
        for f in r.failed:
            print(f"  - {f}")
        print("\nFix the above issues before using GodotMaker.")
        sys.exit(1)
    else:
        print("\nAll required checks passed! Ready to use GodotMaker.")
        sys.exit(0)


if __name__ == "__main__":
    main()
