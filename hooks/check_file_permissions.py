#!/usr/bin/env python3
"""PreToolUse hook: enforce file write permissions.

Rules:
- Main agent (orchestrator) MUST NOT write .gd/.tscn/.tres files.
- Subagents (workers) MUST NOT write planning docs (PLAN.md, STRUCTURE.md, ASSETS.md).

Receives: JSON on stdin with tool_name, tool_input, agent_id (if subagent).
Blocks: JSON with decision: "block" on stdout.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import record_event, EventType

GAME_CODE_EXTENSIONS = {".gd", ".tscn", ".tres"}
PLANNING_DOCS = {"plan.md", "structure.md", "assets.md"}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    file_path_lower = file_path.replace("\\", "/").lower()
    file_name = os.path.basename(file_path_lower)
    _, ext = os.path.splitext(file_path_lower)

    agent_id = data.get("agent_id", "")
    is_subagent = bool(agent_id)

    # Record file operation metric
    record_event(
        EventType.FILE_WRITE if tool_name == "Write" else EventType.FILE_EDIT,
        file=file_name,
        agent_id=agent_id or "orchestrator",
        is_subagent=is_subagent,
    )

    if not is_subagent:
        # Main agent (orchestrator) — block game code writes
        if ext in GAME_CODE_EXTENSIONS:
            reason = (
                f"Orchestrator cannot write game code directly ({file_name}). "
                "Dispatch a Worker subagent to implement this."
            )
            record_event(EventType.HOOK_BLOCK, hook="check_file_permissions",
                         reason=reason, file=file_name)
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
            sys.exit(0)
    else:
        # Subagent (worker/verifier) — block planning doc writes
        if file_name in PLANNING_DOCS:
            reason = (
                f"Workers cannot modify planning documents ({file_name}). "
                "Report changes in your Report Notes section."
            )
            record_event(EventType.HOOK_BLOCK, hook="check_file_permissions",
                         reason=reason, file=file_name, agent_id=agent_id)
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
            sys.exit(0)

    record_event(EventType.HOOK_ALLOW, hook="check_file_permissions",
                 file=file_name, agent_id=agent_id or "orchestrator")


if __name__ == "__main__":
    main()
