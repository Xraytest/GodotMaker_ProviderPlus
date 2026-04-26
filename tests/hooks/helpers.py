"""Test helpers for hook scripts."""
import json
import os
import subprocess
import sys

# tests/hooks/ → project_root/hooks/
HOOKS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "hooks"
)


def run_hook(script_name: str, input_data: dict) -> tuple[str, int, dict | None]:
    """Run a hook script with JSON input, return (stdout, exit_code, parsed_json).

    Args:
        script_name: Hook script filename (e.g., "check_file_permissions.py")
        input_data: Dict to serialize as JSON stdin

    Returns:
        (stdout_text, exit_code, parsed_json_or_None)
    """
    script_path = os.path.join(HOOKS_DIR, script_name)
    result = subprocess.run(
        [sys.executable, script_path],
        input=json.dumps(input_data),
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    stdout = result.stdout.strip()
    parsed = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            pass
    return stdout, result.returncode, parsed


def is_blocked(parsed: dict | None) -> bool:
    """Check if hook response indicates a block.

    Supports both formats:
    - Top-level: {"decision": "block"} (SubagentStop, Stop)
    - PreToolUse: {"hookSpecificOutput": {"permissionDecision": "deny"}}
    """
    if parsed is None:
        return False
    if parsed.get("decision") == "block":
        return True
    hso = parsed.get("hookSpecificOutput", {})
    if hso.get("permissionDecision") == "deny":
        return True
    return False


def write_stage_json(max_stage: int):
    """Write .godotmaker/stage.json with completed stages up to max_stage."""
    os.makedirs(".godotmaker", exist_ok=True)
    stages = {str(i): f"2026-01-01T{i:02d}:00:00Z" for i in range(1, max_stage + 1)}
    with open(os.path.join(".godotmaker", "stage.json"), "w") as f:
        json.dump({"completed_stages": stages}, f)


def cleanup_metrics():
    """Remove test metrics artifacts."""
    import shutil
    metrics_dir = os.path.join(os.getcwd(), ".godotmaker")
    if os.path.exists(metrics_dir):
        shutil.rmtree(metrics_dir)
