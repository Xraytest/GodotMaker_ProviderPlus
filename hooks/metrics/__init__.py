"""GodotMaker metrics system.

Self-contained metrics collection and reporting.
All hooks import from this package to record events.

Usage from hooks:
    from metrics import record_event, EventType
    record_event(EventType.HOOK_BLOCK, hook="check_file_permissions", reason="...")

Generate report:
    python -m hooks.metrics.reporter .godotmaker/metrics.jsonl -o report.html
"""
import json
import os

from .collector import record_event, read_events, read_current_events, start_session
from .schema import (
    EventType, REPORT_MARKERS, detect_report_type, event_has_role,
    REPORT_REQUIRED_SECTIONS, REPORT_FORMAT_HINTS, REPORT_REQUIRED_LABELS,
    ROLE_WORKER, ROLE_VERIFIER, ROLE_REVIEWER, ROLE_ANALYST, ROLE_UNKNOWN,
    KNOWN_ROLES,
)
from . import state


def get_current_stage() -> int:
    """Read the highest completed stage from .godotmaker/stage.json."""
    stage_file = os.path.join(".godotmaker", "stage.json")
    if not os.path.isfile(stage_file):
        return 0
    try:
        with open(stage_file, encoding="utf-8") as f:
            data = json.load(f)
        stages = data.get("completed_stages", {})
        if stages:
            return max(int(k) for k in stages)
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return 0


__all__ = [
    "record_event", "read_events", "read_current_events", "start_session",
    "EventType", "REPORT_MARKERS", "detect_report_type", "event_has_role",
    "REPORT_REQUIRED_SECTIONS", "REPORT_FORMAT_HINTS", "REPORT_REQUIRED_LABELS",
    "ROLE_WORKER", "ROLE_VERIFIER", "ROLE_REVIEWER", "ROLE_ANALYST", "ROLE_UNKNOWN",
    "KNOWN_ROLES",
    "state",
    "get_current_stage",
]
