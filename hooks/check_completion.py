#!/usr/bin/env python3
"""Stop hook: verify project completeness and orchestrator diligence.

Three checks (only enforced at stage >= ENFORCEMENT_STAGE):
1. Forced self-review (first Stop only) — unconditionally block to force
   the orchestrator to verify E2E completion and screenshot coverage.
2. Static project check (check_project.py --all) — are all artifacts present?
3. Orchestrator diligence — did it actually dispatch verifiers and reviewers?

Stage-aware: at stages < ENFORCEMENT_STAGE, the orchestrator may stop freely
(e.g., to wait for user input). Full checks only apply when the pipeline
reaches integration/final stages.

Only blocks the main agent (orchestrator), not subagents.

Anti-deadloop: if this hook has blocked 5+ times in the same session,
allow with a warning instead of blocking again.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import record_event, read_current_events, EventType, state, event_has_role, get_current_stage

BLOCK_LIMIT = 5  # Max blocks before allowing to prevent deadloop
ENFORCEMENT_STAGE = 7  # Only enforce full checks at this stage or later


def find_project_root() -> str | None:
    """Find the game project root containing project.godot.

    Searches CWD first, then immediate subdirectories.
    Returns absolute path or None.
    """
    if os.path.exists("project.godot"):
        return os.getcwd()
    try:
        for entry in os.scandir("."):
            if entry.is_dir() and not entry.name.startswith("."):
                if os.path.exists(os.path.join(entry.path, "project.godot")):
                    return os.path.abspath(entry.path)
    except OSError:
        pass
    return None


def _gather_e2e_state(events: list[dict]) -> tuple[int, int, int | None, int]:
    """Return (e2e_run_count, screenshot_event_count, png_file_count, scene_count).

    png_file_count is None when screenshots/ directory does not exist.
    """
    e2e_run_count = len([e for e in events if e.get("event") == EventType.E2E_RUN])
    screenshot_event_count = len([e for e in events if e.get("event") == EventType.SCREENSHOT_CAPTURE])

    ss_dir = "screenshots"
    if os.path.isdir(ss_dir):
        png_file_count = len([f for f in os.listdir(ss_dir) if f.lower().endswith(".png")])
    else:
        png_file_count = None

    scene_count = 0
    if os.path.isfile("SCENES.md"):
        with open("SCENES.md", encoding="utf-8", errors="replace") as f:
            content = f.read()
        scene_count = len(re.findall(r"^## Scene:", content, re.MULTILINE))

    return (e2e_run_count, screenshot_event_count, png_file_count, scene_count)


def check_diligence(events: list[dict]) -> list[str]:
    """Check that orchestrator dispatched verifiers and reviewers in current session."""
    if not events:
        return []  # No metrics yet, don't block

    # Primary detection: role field from SubagentStart (parsed from description)
    worker_starts = [e for e in events
                     if e.get("event") == EventType.SUBAGENT_START
                     and event_has_role(e, "worker")]
    verifier_starts = [e for e in events
                       if e.get("event") == EventType.SUBAGENT_START
                       and event_has_role(e, "verifier")]
    reviewer_starts = [e for e in events
                       if e.get("event") == EventType.SUBAGENT_START
                       and event_has_role(e, "reviewer")]

    # Secondary detection: role or report_type from SubagentStop (fallback)
    verifier_stops = [e for e in events
                      if e.get("event") == EventType.SUBAGENT_STOP
                      and event_has_role(e, "verifier")]
    reviewer_stops = [e for e in events
                      if e.get("event") == EventType.SUBAGENT_STOP
                      and event_has_role(e, "reviewer")]

    issues = []
    worker_count = len(worker_starts)

    if worker_count > 0:
        if len(verifier_starts) == 0 and len(verifier_stops) == 0:
            issues.append(
                f"Dispatched {worker_count} workers but 0 verifiers. "
                "Verification is mandatory — dispatch a verifier (subagent_type: 'verifier') "
                "to run build + unit tests + E2E tests for each worker's deliverables."
            )
        if len(reviewer_starts) == 0 and len(reviewer_stops) == 0:
            issues.append(
                f"Dispatched {worker_count} workers but 0 reviewers. "
                "Review is mandatory — dispatch a reviewer (subagent_type: 'reviewer') "
                "for each completed worker task to check code quality and ECS patterns."
            )

    return issues


def check_project_completeness(project_root: str) -> list[str]:
    """Run check_project.py --all and return FAIL lines."""
    check_script = os.path.join("tools", "check_project.py")
    if not os.path.exists(check_script):
        check_script = os.path.join(".claude", "tools", "check_project.py")
        if not os.path.exists(check_script):
            return []  # Can't check

    try:
        result = subprocess.run(
            [sys.executable, check_script, project_root, "--all"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    if "[FAIL]" not in result.stdout:
        return []

    return [
        line.strip() for line in result.stdout.split("\n")
        if "[FAIL]" in line
    ]


def check_e2e_and_screenshots(events: list[dict]) -> str:
    """Gather E2E and screenshot status for the forced self-review message."""
    lines = []
    e2e_run_count, screenshot_event_count, png_file_count, scene_count = _gather_e2e_state(events)

    lines.append(f"  - E2E test runs recorded: {e2e_run_count}")
    lines.append(f"  - Screenshot captures recorded: {screenshot_event_count}")

    if png_file_count is not None:
        lines.append(f"  - Files in screenshots/: {png_file_count}")
    else:
        lines.append("  - screenshots/ directory: NOT FOUND")

    if scene_count > 0:
        lines.append(f"  - Scenes defined in SCENES.md: {scene_count}")
    else:
        lines.append("  - SCENES.md: NOT FOUND")

    return "\n".join(lines)


def check_e2e_coverage(project_root: str | None, events: list[dict]) -> list[str]:
    """Check E2E and screenshot coverage on subsequent Stop attempts.

    Only runs inside a game project (project_root is known).
    """
    if not project_root:
        return []

    issues = []
    e2e_run_count, _screenshot_event_count, png_file_count, scene_count = _gather_e2e_state(events)

    # Check for any E2E runs
    if e2e_run_count == 0:
        issues.append("No E2E test runs recorded in metrics — every system should have E2E tests")

    # Check screenshot coverage vs SCENES.md
    if scene_count > 0:
        if png_file_count is None:
            issues.append(
                f"screenshots/ directory not found — need screenshots for {scene_count} scenes"
            )
        elif png_file_count < scene_count:
            issues.append(
                f"screenshots/ has {png_file_count} images but SCENES.md defines "
                f"{scene_count} scenes — each scene needs a screenshot"
            )

    return issues


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Only check main agent
    agent_id = data.get("agent_id", "")
    if agent_id:
        sys.exit(0)

    # Stage-aware: only enforce full checks at integration/final stages.
    # Before that, the orchestrator may stop freely (e.g., to wait for user input).
    current_stage = get_current_stage()
    if current_stage < ENFORCEMENT_STAGE:
        record_event(EventType.GATE_CHECK, gate="completion",
                     result="early_allow", stage=current_stage)
        sys.exit(0)

    # Anti-deadloop: if blocked too many times in this session, allow with warning
    block_count = state.get("stop_block_count", 0)
    if block_count >= BLOCK_LIMIT:
        record_event(EventType.GATE_CHECK, gate="completion",
                     result="force_allow", reason=f"Blocked {block_count} times, allowing to prevent deadloop")
        warning = (
            f"Force-allowing completion after {block_count} failed attempts. "
            "You MUST inform the user that completion checks did not fully pass. "
            "List the unresolved issues in your final message so the user can decide "
            "whether to accept or request fixes. Do NOT present this as a clean completion."
        )
        print(json.dumps({"decision": "allow", "reason": warning}), file=sys.stderr)
        sys.exit(0)

    # Check 0: forced self-review on first Stop attempt
    if block_count == 0:
        state.increment("stop_block_count")

        # Read events once for self-review summary
        events = read_current_events()

        # Try to gather concrete info for the orchestrator
        e2e_summary = check_e2e_and_screenshots(events)

        reason = (
            "MANDATORY SELF-REVIEW before completing.\n"
            "This is your first Stop attempt — you must verify the following:\n"
            "  1. Every system has corresponding E2E tests that PASS\n"
            "  2. Every UI/scene has a corresponding screenshot in screenshots/\n"
            "  3. All screenshots have been verified against SCENES.md expectations\n"
        )
        if e2e_summary:
            reason += f"\nCurrent status:\n{e2e_summary}\n"
        reason += (
            "\nReview the above, fix any gaps, then try to finish again."
        )

        record_event(EventType.GATE_CHECK, gate="completion",
                     result="forced_review", block_number=1)
        print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)

    all_issues = []

    # Find game project root (CWD-independent)
    project_root = find_project_root()

    if project_root:
        # Check 1: project completeness
        fail_lines = check_project_completeness(project_root)
        if fail_lines:
            all_issues.extend(fail_lines)

    # Read events once for remaining checks
    events = read_current_events()

    # Check 2: orchestrator diligence (current session only)
    diligence_issues = check_diligence(events)
    all_issues.extend(diligence_issues)

    # Check 3: E2E and screenshot coverage
    e2e_issues = check_e2e_coverage(project_root, events)
    all_issues.extend(e2e_issues)

    if all_issues:
        state.increment("stop_block_count")
        record_event(EventType.GATE_CHECK, gate="completion",
                     result="fail", issues=all_issues[:5])

        reason = "Cannot finish — issues found:\n" + "\n".join(
            f"  {line}" for line in all_issues[:10]
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)

    record_event(EventType.GATE_CHECK, gate="completion", result="pass")


if __name__ == "__main__":
    main()
