#!/usr/bin/env python3
"""Append a stage event to .godotmaker/stage.jsonl with a server-generated UTC timestamp.

Used in SKILL "When Done" sections instead of having the agent hand-write the
event JSON. Moving timestamp generation off the agent eliminates the corruption
pattern observed in 2026-05-09 e2e (every fixgap and late-iter evaluate event
had a fabricated `ts`; verify events written under simpler agent contexts were
honest) — the root cause was agents producing `ts` from model output under
context pressure rather than calling the system clock.

Usage:
    python tools/append_stage_event.py <role> [--key=value ...]

Examples:
    python tools/append_stage_event.py scaffold
    python tools/append_stage_event.py gdd --tag=v0.1.0
    python tools/append_stage_event.py accept --decision=accept
    python tools/append_stage_event.py rescue --conclusion=defect

Exit codes:
    0  appended successfully
    1  .godotmaker/ directory does not exist under project root
    2  bad CLI usage (malformed extra arg)
"""
import argparse
import datetime
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append a stage event to .godotmaker/stage.jsonl",
    )
    parser.add_argument(
        "role",
        help="role name (scaffold, gdd, asset, build, verify, evaluate, "
             "fixgap, accept, finalize, rescue)",
    )
    parser.add_argument(
        "--project-path",
        default=None,
        help="project root containing .godotmaker/ (default: cwd)",
    )
    args, extras = parser.parse_known_args(argv)

    # Field order matches the convention prior SKILLs hand-wrote: role, ts,
    # then any role-specific extras (tag, decision, conclusion). Python dicts
    # preserve insertion order so the JSON output is stable.
    event: dict[str, object] = {"role": args.role}

    # Server-generated UTC timestamp — the whole point of moving this off
    # the agent. Format matches what SKILLs previously asked the agent to
    # write: ISO-8601 seconds precision, trailing Z.
    event["ts"] = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # --key=value extras land verbatim after ts. partition('=') keeps any
    # later '=' in the value (rare for stage events but harmless).
    for extra in extras:
        if not extra.startswith("--") or "=" not in extra:
            print(
                f"error: extra args must be in --key=value form (got: {extra!r})",
                file=sys.stderr,
            )
            return 2
        key, _, value = extra[2:].partition("=")
        if not key:
            print(f"error: empty key in {extra!r}", file=sys.stderr)
            return 2
        event[key] = value

    project_path = Path(args.project_path) if args.project_path else Path.cwd()
    stage_dir = project_path / ".godotmaker"
    stage_path = stage_dir / "stage.jsonl"

    if not stage_dir.is_dir():
        print(f"error: {stage_dir} does not exist", file=sys.stderr)
        return 1

    # O_APPEND-mode write: the kernel guarantees the line lands at EOF
    # without a read-modify-write race. Also eliminates the "I'll regenerate
    # the ts from memory before re-writing the file" failure mode that the
    # prior SKILL prose ("read the existing file, append, write back")
    # implicitly invited.
    with open(stage_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
