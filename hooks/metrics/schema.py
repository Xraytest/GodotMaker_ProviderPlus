"""Event type definitions for the metrics system.

All metric events flow through these types. Add new types here when extending.
"""
import re
from enum import Enum


# Canonical role names — use these instead of raw strings
ROLE_WORKER = "worker"
ROLE_VERIFIER = "verifier"
ROLE_REVIEWER = "reviewer"
ROLE_ANALYST = "analyst"
ROLE_UNKNOWN = "unknown"
KNOWN_ROLES = {ROLE_WORKER, ROLE_VERIFIER, ROLE_REVIEWER, ROLE_ANALYST}


class EventType(str, Enum):
    # Subagent lifecycle
    SUBAGENT_START = "subagent_start"
    SUBAGENT_STOP = "subagent_stop"

    # Hook decisions
    HOOK_BLOCK = "hook_block"
    HOOK_ALLOW = "hook_allow"

    # Gate / verification
    GATE_CHECK = "gate_check"
    STAGE_COMPLETE = "stage_complete"
    SPOT_CHECK = "spot_check"

    # Errors and retries
    ERROR = "error"
    RETRY = "retry"

    # Worker outcomes
    WORKER_DONE = "worker_done"
    WORKER_PARTIAL = "worker_partial"
    WORKER_FAILED = "worker_failed"

    # Verifier outcomes
    VERIFIER_PASS = "verifier_pass"
    VERIFIER_FAIL = "verifier_fail"
    VERIFIER_PARTIAL = "verifier_partial"

    # Skill usage
    SKILL_READ = "skill_read"

    # File operations
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"

    # Test/build execution
    E2E_RUN = "e2e_run"
    UNIT_TEST_RUN = "unit_test_run"
    BUILD_CHECK = "build_check"
    SCREENSHOT_CAPTURE = "screenshot_capture"

    # Orchestrator actions
    WORKER_BRIEF = "worker_brief"


# Shared markers used to identify report type in subagent output
REPORT_MARKERS = {
    ROLE_WORKER: "## Report:",
    ROLE_VERIFIER: "## Verification Report:",
    ROLE_REVIEWER: "## Review Report:",
    ROLE_ANALYST: "## Analyst Report:",
}

# Flexible regex patterns — catch heading level variations, spacing, etc.
REPORT_PATTERNS = {
    ROLE_ANALYST: re.compile(r"#{1,4}\s*Analyst\s+Report\s*[:：]", re.IGNORECASE),
    ROLE_WORKER: re.compile(r"#{1,4}\s*Report\s*[:：]", re.IGNORECASE),
    ROLE_VERIFIER: re.compile(r"#{1,4}\s*Verification\s+Report\s*[:：]", re.IGNORECASE),
    ROLE_REVIEWER: re.compile(r"#{1,4}\s*Review\s+Report\s*[:：]", re.IGNORECASE),
}

# Last resort: detect by unique section headings present in each report type
REPORT_FALLBACK = {
    ROLE_ANALYST: re.compile(r"###\s*Asset\s+Summary", re.IGNORECASE),
    ROLE_WORKER: re.compile(r"###\s*Status:\s*(DONE|PARTIAL|FAILED)", re.IGNORECASE),
    ROLE_VERIFIER: re.compile(r"###\s*Overall:\s*(PASS|FAIL|PARTIAL)", re.IGNORECASE),
    ROLE_REVIEWER: re.compile(r"###\s*Reviewers?\s*Matched", re.IGNORECASE),
}


# --- Report format specifications (single source of truth) ---
# Each role defines: required sections (name + regex), and a format hint for block messages.

REPORT_REQUIRED_SECTIONS = {
    ROLE_WORKER: [
        ("Status", r"### Status:\s*(DONE|PARTIAL|FAILED)"),
        ("Files Changed", r"### Files Changed"),
        ("Tests", r"### Tests"),
        ("Build", r"### Build"),
        ("Memory Entry", r"### Memory Entry"),
    ],
    ROLE_VERIFIER: [
        ("Overall", r"### Overall:\s*(PASS|FAIL|PARTIAL)"),
        ("Results", r"### Results"),
        ("Adversarial Probes", r"### Adversarial Probes"),
    ],
    ROLE_REVIEWER: [
        ("Reviewers Matched", r"### Reviewers Matched"),
        ("ECS Review", r"### ECS Review"),
        ("Issues Found", r"### Issues Found"),
        ("Summary", r"### Summary"),
    ],
    ROLE_ANALYST: [
        ("Status", r"### Status:\s*(DONE|PARTIAL|FAILED)"),
        ("Asset Summary", r"### Asset Summary"),
        ("Art Style Summary", r"### Art Style Summary"),
        ("Files Generated", r"### Files Generated"),
    ],
}

REPORT_FORMAT_HINTS = {}
for _role, _sections in REPORT_REQUIRED_SECTIONS.items():
    _heading = REPORT_MARKERS.get(_role, f"## {_role.capitalize()} Report:")
    _lines = [_heading] + [f"### {name}" for name, _ in _sections]
    REPORT_FORMAT_HINTS[_role] = "\n".join(_lines)

REPORT_REQUIRED_LABELS = {
    role: ", ".join(name for name, _ in sections)
    for role, sections in REPORT_REQUIRED_SECTIONS.items()
}


def event_has_role(event: dict, role: str) -> bool:
    """Check if an event matches a role, checking 'role' field first, then 'report_type' fallback."""
    return event.get("role") == role or event.get("report_type") == role


def detect_report_type(message: str) -> str | None:
    """Detect report type from message content using layered matching.

    Layer 1: exact substring (fastest, original behavior)
    Layer 2: flexible regex on heading (catches ## / ### / # variations)
    Layer 3: unique section headings as fingerprint

    Returns report type string or None if not a recognized report.
    """
    if not message:
        return None
    # Layer 1: exact marker match
    for rtype, marker in REPORT_MARKERS.items():
        if marker in message:
            return rtype
    # Layer 2: flexible heading patterns
    for rtype, pattern in REPORT_PATTERNS.items():
        if pattern.search(message):
            return rtype
    # Layer 3: section-based fallback
    for rtype, pattern in REPORT_FALLBACK.items():
        if pattern.search(message):
            return rtype
    return None
