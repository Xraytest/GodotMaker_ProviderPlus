#!/usr/bin/env python3
"""PreToolUse hook: validate stage outputs and remind orchestrator of next stage.

When the orchestrator writes .godotmaker/stage.json (recording stage completion),
this hook:
  1. VALIDATES that the completed stage's required outputs exist. Blocks if not.
  2. Injects an additionalContext reminder pointing to the next stage's detail file.

Only the path is injected — the orchestrator decides whether to read it (it may
have already loaded the file).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import record_event, EventType

STAGE_FILES = {
    1: "stages/stage1_requirements.md",
    2: "stages/stage2_architecture.md",
    3: "stages/stage3_scaffold.md",
    4: "stages/stage4_assets.md",
    5: "stages/stage5_risk_impl.md",
    6: "stages/stage6_main_impl.md",
    7: "stages/stage7_integration.md",
    8: "stages/stage8_final.md",
}

MAX_STAGE = 8


SCHEMA_PATH = os.path.join(".godotmaker", "stage_schemas.json")


def load_schemas() -> dict | None:
    if not os.path.isfile(SCHEMA_PATH):
        return None
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Programmatic check functions
# ---------------------------------------------------------------------------

def check_references_has_images() -> str | None:
    """Stage 4: references/ must have at least 1 .png file."""
    refs_dir = "references"
    if not os.path.isdir(refs_dir):
        return "references/ directory not found"
    pngs = [f for f in os.listdir(refs_dir) if f.lower().endswith(".png")]
    if not pngs:
        return "references/ has no .png files — generate scene reference images first"
    return None


def check_metrics_has_worker_done() -> str | None:
    """Stage 5/6: metrics must have at least 1 worker_done event."""
    from metrics import read_current_events
    events = read_current_events()
    worker_dones = [e for e in events if e.get("event") == "worker_done"]
    if not worker_dones:
        return "No worker_done events in metrics — no workers completed successfully"
    return None


def check_plan_has_non_pending() -> str | None:
    """Stage 5: PLAN.md must have at least one non-pending task."""
    if not os.path.isfile("PLAN.md"):
        return "PLAN.md not found"
    with open("PLAN.md", encoding="utf-8", errors="replace") as f:
        content = f.read()
    # Look for task status table rows with non-pending status
    statuses = re.findall(r"\|\s*(?:completed|in_progress|failed)\s*\|", content, re.IGNORECASE)
    if not statuses:
        return "PLAN.md has no tasks marked as completed/in_progress — no work done"
    return None


def check_plan_no_pending() -> str | None:
    """Stage 6: PLAN.md must have no pending tasks."""
    if not os.path.isfile("PLAN.md"):
        return "PLAN.md not found"
    with open("PLAN.md", encoding="utf-8", errors="replace") as f:
        content = f.read()
    pending = re.findall(r"\|\s*pending\s*\|", content, re.IGNORECASE)
    if pending:
        return f"PLAN.md still has {len(pending)} pending task(s) — all tasks must be completed"
    return None


def check_metrics_has_verifier() -> str | None:
    """Stage 7: metrics must have at least 1 verifier event."""
    from metrics import read_current_events
    events = read_current_events()
    verifier_events = [e for e in events
                       if e.get("event") in ("verifier_pass", "verifier_fail", "verifier_partial")]
    if not verifier_events:
        return "No verifier events in metrics — no verification was performed"
    return None


def check_screenshots_match_scenes() -> str | None:
    """Stage 8: screenshots/ must have >= N .png files where N = scene count in SCENES.md."""
    if not os.path.isfile("SCENES.md"):
        return "SCENES.md not found — cannot verify screenshot coverage"
    with open("SCENES.md", encoding="utf-8", errors="replace") as f:
        content = f.read()
    scene_count = len(re.findall(r"^## Scene:", content, re.MULTILINE))
    if scene_count == 0:
        return None  # No scenes defined, skip check

    # Check screenshots/ directory
    ss_dir = "screenshots"
    if not os.path.isdir(ss_dir):
        return (
            f"screenshots/ directory not found — need {scene_count} screenshots "
            f"for {scene_count} scenes"
        )
    pngs = [f for f in os.listdir(ss_dir) if f.lower().endswith(".png")]
    if len(pngs) < scene_count:
        return (
            f"screenshots/ has {len(pngs)} images but SCENES.md defines {scene_count} scenes "
            f"— each scene needs a screenshot"
        )
    return None


PROGRAMMATIC_CHECKS = {
    "references_has_images": check_references_has_images,
    "metrics_has_worker_done": check_metrics_has_worker_done,
    "plan_has_non_pending": check_plan_has_non_pending,
    "metrics_has_new_worker_done": check_metrics_has_worker_done,
    "plan_no_pending": check_plan_no_pending,
    "metrics_has_verifier": check_metrics_has_verifier,
    "screenshots_match_scenes": check_screenshots_match_scenes,
}


# ---------------------------------------------------------------------------
# Reminder helper
# ---------------------------------------------------------------------------

def get_next_stage_reminder(completed_stage: int) -> str | None:
    """Return a reminder string for the next stage, or None if pipeline is done."""
    next_stage = completed_stage + 1
    if next_stage > MAX_STAGE:
        return None

    stage_file = STAGE_FILES.get(next_stage)
    if not stage_file:
        return None

    return (
        f"[Stage {completed_stage} complete] "
        f"Next: Stage {next_stage}. "
        f"Read the detail file before proceeding: {stage_file}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Normalize path separators for cross-platform
    normalized = file_path.replace("\\", "/")
    if not normalized.endswith(".godotmaker/stage.json"):
        sys.exit(0)

    # Parse the content being written to extract completed_stage
    content = tool_input.get("content", "")
    if not content:
        # Edit tool uses old_string/new_string, try new_string
        content = tool_input.get("new_string", "")

    try:
        stage_data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        sys.exit(0)

    # Support both formats:
    # Old: {"completed_stage": N}
    # New: {"completed_stages": {"1": "...", "2": "..."}}
    completed_stage = stage_data.get("completed_stage")
    if completed_stage is None:
        stages = stage_data.get("completed_stages", {})
        if stages:
            completed_stage = max(int(k) for k in stages)
    if not isinstance(completed_stage, int):
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Validate stage outputs before allowing completion
    # -----------------------------------------------------------------------
    schemas = load_schemas()
    if schemas:
        stage_key = str(completed_stage)
        stage_schema = schemas.get(stage_key, {})
        issues = []

        # Check file existence
        for filepath in stage_schema.get("files", []):
            if not os.path.exists(filepath):
                issues.append(f"Required file missing: {filepath}")

        # Run programmatic checks
        for check_name in stage_schema.get("checks", []):
            check_fn = PROGRAMMATIC_CHECKS.get(check_name)
            if check_fn:
                result = check_fn()
                if result:
                    issues.append(result)

        if issues:
            reason = (
                f"Cannot mark Stage {completed_stage} as complete — validation failed:\n"
                + "\n".join(f"  - {i}" for i in issues)
            )
            record_event(EventType.GATE_CHECK, gate=f"stage_{completed_stage}",
                         result="fail", issues=issues)
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
            sys.exit(0)

    # -----------------------------------------------------------------------
    # Validation passed — record completion and inject next-stage reminder
    # -----------------------------------------------------------------------
    record_event(EventType.GATE_CHECK, gate=f"stage_{completed_stage}",
                 result="complete")

    reminder = get_next_stage_reminder(completed_stage)
    if reminder:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": reminder,
            }
        }
        json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
