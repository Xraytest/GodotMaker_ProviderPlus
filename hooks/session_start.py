#!/usr/bin/env python3
"""SessionStart hook: initialize metrics for new session.

Clears current session metrics log and resets runtime state.
Displays deployed GodotMaker version.
Never blocks.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import start_session, state


def read_deployed_version() -> str | None:
    """Read the deployed GodotMaker version from .godotmaker/version."""
    version_file = os.path.join(".godotmaker", "version")
    if not os.path.isfile(version_file):
        return None
    try:
        with open(version_file, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def main():
    start_session()
    state.reset()

    version = read_deployed_version()
    if version:
        # Inject version info as additional context for the orchestrator
        result = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"[GodotMaker v{version}]",
            }
        }
        print(json.dumps(result))

    sys.exit(0)

if __name__ == "__main__":
    main()
