#!/usr/bin/env python3
"""PreToolUse hook: block the dispatching role from directly reading image
files in assets/.

The dispatching role (the active /gm-* skill in the main session) must delegate
asset analysis to an analyst subagent. Subagents are allowed to read assets —
only the main agent (empty agent_id) is blocked.
"""
import json
import os
import sys


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".bmp", ".tga"}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Only check PreToolUse for Read tool
    if data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)
    if data.get("tool_name") != "Read":
        sys.exit(0)

    # Only block the main agent (the dispatching role), not subagents
    agent_id = data.get("agent_id", "")
    if agent_id:
        sys.exit(0)  # Subagent — allow

    # Check if the file path is an image in assets/
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Normalize path separators
    normalized = file_path.replace("\\", "/").lower()

    # Check if path contains assets/ directory
    if "/assets/" not in normalized and not normalized.startswith("assets/"):
        sys.exit(0)

    # Check file extension
    _, ext = os.path.splitext(normalized)
    if ext not in IMAGE_EXTENSIONS:
        sys.exit(0)  # Non-image files (e.g., .json, .ogg) are OK

    # Block — dispatching role trying to read image in assets/
    reason = (
        f"The dispatching role cannot read image files in assets/ directly. "
        f"Dispatch an analyst subagent to analyze '{os.path.basename(file_path)}' instead. "
        f"See analyst-dispatch.md for the protocol."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


if __name__ == "__main__":
    main()
