#!/usr/bin/env python3
"""PreToolUse hook: enforce file write permissions per pipeline role.

Reads .godotmaker/current_role and applies the role's write rules. See the
gm-*/SKILL.md files for the canonical per-role rules; this hook enforces
them. When no role is set, falls back to legacy rules (main agent blocked
from game code, subagents blocked from planning docs).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import record_event, EventType, get_current_role, WORKER_DISPATCH_ROLES

GAME_CODE_EXTENSIONS = {".gd", ".tscn", ".tres"}
PLANNING_DOCS = {"plan.md", "structure.md", "assets.md", "gap.md"}
E2E_DIR_PREFIX = "e2e/"
ASSETS_DIR_PREFIX = "assets/"
GODOTMAKER_DIR = ".godotmaker/"
EVAL_FILE = ".godotmaker/evaluation.json"


def _is_e2e_path(path_lower: str) -> bool:
    return path_lower.startswith(E2E_DIR_PREFIX) or f"/{E2E_DIR_PREFIX}" in path_lower


def _is_assets_path(path_lower: str) -> bool:
    return path_lower.startswith(ASSETS_DIR_PREFIX) or f"/{ASSETS_DIR_PREFIX}" in path_lower


def _is_godotmaker_path(path_lower: str) -> bool:
    return path_lower.startswith(GODOTMAKER_DIR) or f"/{GODOTMAKER_DIR}" in path_lower


def _is_eval_file(path_lower: str) -> bool:
    return path_lower.endswith(EVAL_FILE) or path_lower == EVAL_FILE


def _block(reason: str, file_name: str, agent_id: str = "") -> None:
    record_event(EventType.HOOK_BLOCK, hook="check_file_permissions",
                 reason=reason, file=file_name, agent_id=agent_id or "main")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def _check_main(role: str, path_lower: str, file_name: str, ext: str) -> None:
    """Apply main-agent rules for the active role. Calls _block on violation."""
    is_e2e = _is_e2e_path(path_lower)
    is_code = ext in GAME_CODE_EXTENSIONS
    is_eval = _is_eval_file(path_lower)
    is_godotmaker = _is_godotmaker_path(path_lower)
    is_assets = _is_assets_path(path_lower)

    if role == "evaluate":
        if not (is_e2e or is_godotmaker):
            _block(f"Evaluator can only write to e2e/ or .godotmaker/ "
                   f"(attempted: {file_name}).", file_name)
        return

    if role == "verify":
        if not is_godotmaker:
            _block(f"Verify role is read-only — cannot write {file_name}.", file_name)
        return

    if role == "scaffold":
        return

    if is_e2e:
        _block(f"{role.capitalize()} role cannot write to e2e/ ({file_name}). "
               "E2E tests are owned by the Evaluator.", file_name)

    if role == "asset":
        if path_lower == "assets.md" or is_godotmaker:
            return
        _block(f"Asset orchestrator can only write the project-root ASSETS.md "
               f"or .godotmaker/ (attempted: {file_name}). Image files go "
               f"through tools/asset_gen.py (Bash) or the analyst subagent.",
               file_name)

    if role == "gdd":
        if is_assets:
            _block(f"GDD role cannot write to assets/ ({file_name}). "
                   "Asset files are produced during /gm-asset.", file_name)
        if ext == ".md" or file_name == "project.godot" or is_godotmaker:
            return
        _block(f"GDD role may only write planning docs, project.godot, or "
               f".godotmaker/ (attempted: {file_name}).", file_name)

    if is_code:
        if role in WORKER_DISPATCH_ROLES:
            _block(f"{role.capitalize()} orchestrator cannot write game code directly "
                   f"({file_name}). Dispatch a Worker subagent.", file_name)
        else:
            _block(f"{role.capitalize()} role cannot modify game code "
                   f"({file_name}).", file_name)


def _check_subagent(path_lower: str, file_name: str, agent_id: str) -> None:
    """Apply subagent rules. Calls _block on violation."""
    if _is_e2e_path(path_lower):
        _block(f"Workers cannot write to e2e/ ({file_name}). "
               "E2E tests are owned by the Evaluator.", file_name, agent_id)
    if file_name in PLANNING_DOCS:
        _block(f"Workers cannot modify planning documents ({file_name}). "
               "Report changes in your Report Notes section.", file_name, agent_id)


def _check_legacy(is_subagent: bool, path_lower: str, file_name: str,
                  ext: str, agent_id: str) -> None:
    """Fallback rules when no current_role is set."""
    if is_subagent:
        if file_name in PLANNING_DOCS:
            _block(f"Workers cannot modify planning documents ({file_name}).",
                   file_name, agent_id)
    else:
        if ext in GAME_CODE_EXTENSIONS:
            _block(f"Orchestrator cannot write game code directly ({file_name}). "
                   "Dispatch a Worker subagent.", file_name)


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

    path_lower = file_path.replace("\\", "/").lower()
    file_name = os.path.basename(path_lower)
    _, ext = os.path.splitext(path_lower)

    agent_id = data.get("agent_id", "")
    is_subagent = bool(agent_id)

    record_event(
        EventType.FILE_WRITE if tool_name == "Write" else EventType.FILE_EDIT,
        file=file_name,
        agent_id=agent_id or "main",
        is_subagent=is_subagent,
    )

    role = get_current_role()

    if not role:
        _check_legacy(is_subagent, path_lower, file_name, ext, agent_id)
    elif is_subagent:
        _check_subagent(path_lower, file_name, agent_id)
    else:
        _check_main(role, path_lower, file_name, ext)

    record_event(EventType.HOOK_ALLOW, hook="check_file_permissions",
                 file=file_name, agent_id=agent_id or "main", role=role)


if __name__ == "__main__":
    main()
