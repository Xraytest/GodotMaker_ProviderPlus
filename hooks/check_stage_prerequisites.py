#!/usr/bin/env python3
"""PreToolUse hook (Agent tool): verify stage prerequisites before worker dispatch.

Reads config/stage_schemas.json to determine what files each completed stage
should have produced. Blocks if any are missing.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import record_event, EventType, get_current_stage


SCHEMA_PATH = os.path.join(".godotmaker", "stage_schemas.json")


def load_schemas() -> dict | None:
    if not os.path.isfile(SCHEMA_PATH):
        return None
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if data.get("tool_name") != "Agent":
        sys.exit(0)

    # Only check main agent (orchestrator)
    if data.get("agent_id", ""):
        sys.exit(0)

    schemas = load_schemas()
    if not schemas:
        sys.exit(0)  # No schema file, can't check

    completed = get_current_stage()

    missing = []
    for stage_num in range(1, completed + 1):
        stage_key = str(stage_num)
        stage_schema = schemas.get(stage_key, {})
        for filepath in stage_schema.get("files", []):
            if not os.path.exists(filepath):
                missing.append(f"Stage {stage_num}: {filepath} not found")

    if missing:
        reason = (
            "Cannot dispatch worker — prerequisite stage outputs missing:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\nComplete earlier stages first. See SKILL.md Mandatory Pipeline."
        )
        record_event(EventType.HOOK_BLOCK, hook="check_stage_prerequisites",
                     missing=[m.split(": ", 1)[1] for m in missing])
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
        sys.exit(0)

    record_event(EventType.HOOK_ALLOW, hook="check_stage_prerequisites")


if __name__ == "__main__":
    main()
