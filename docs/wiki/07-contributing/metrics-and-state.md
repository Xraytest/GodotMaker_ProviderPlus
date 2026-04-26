# Metrics and State

GodotMaker tracks all hook decisions, subagent lifecycles, file operations, and gate checks through a metrics system. This data feeds the HTML report generator and drives hook behavior (anti-deadloop counters, diligence checks, progress reminders).

## Event Logging

The metrics collector writes events to two JSONL files in `.godotmaker/`:

| File | Scope | Lifecycle |
|------|-------|-----------|
| `metrics.jsonl` | All sessions | Append-only, never cleared. Used for trend analysis across sessions. |
| `metrics_current.jsonl` | Current session | Truncated at session start by `session_start.py`. Used for in-session checks (diligence, progress). |

Every `record_event()` call writes the same JSON line to both files simultaneously. If either write fails, the error is silently swallowed -- metrics must never break the pipeline.

### Event format

Each line is a JSON object with a mandatory `ts` (ISO 8601 UTC timestamp) and `event` (EventType value) field, plus arbitrary key-value detail fields:

```json
{"ts": "2025-01-15T14:32:01.123456+00:00", "event": "hook_block", "hook": "check_file_permissions", "reason": "Orchestrator cannot write game code directly (player.gd).", "file": "player.gd"}
```

### Usage from hooks

```python
from metrics import record_event, EventType

record_event(EventType.HOOK_BLOCK, hook="check_file_permissions", reason="...", file="player.gd")
record_event(EventType.SUBAGENT_START, agent_id="w1", agent_type="worker", role="worker")
record_event(EventType.WORKER_DONE, agent_id="w1", files=["src/systems/movement.gd"])
```

### Reading events

```python
from metrics import read_current_events

events = read_current_events()  # Current session only
# Returns list[dict], each dict is one parsed JSONL line
```

The `read_events()` function reads from the history log by default, or accepts a custom path.

## EventType Enum

All event types are defined in `hooks/metrics/schema.py` as a string enum:

| EventType | Value | When Recorded |
|-----------|-------|---------------|
| `SUBAGENT_START` | `subagent_start` | SubagentStart hook fires |
| `SUBAGENT_STOP` | `subagent_stop` | SubagentStop hook fires |
| `HOOK_BLOCK` | `hook_block` | Any hook blocks an action |
| `HOOK_ALLOW` | `hook_allow` | Any hook explicitly allows an action |
| `GATE_CHECK` | `gate_check` | Stage validation or completion check runs |
| `STAGE_COMPLETE` | `stage_complete` | A pipeline stage is marked done |
| `SPOT_CHECK` | `spot_check` | Ad-hoc verification event |
| `ERROR` | `error` | Error encountered during pipeline |
| `RETRY` | `retry` | Retry attempt recorded |
| `WORKER_DONE` | `worker_done` | Worker subagent finishes with status DONE |
| `WORKER_PARTIAL` | `worker_partial` | Worker finishes with status PARTIAL |
| `WORKER_FAILED` | `worker_failed` | Worker finishes with status FAILED |
| `VERIFIER_PASS` | `verifier_pass` | Verifier finishes with status PASS |
| `VERIFIER_FAIL` | `verifier_fail` | Verifier finishes with status FAIL |
| `VERIFIER_PARTIAL` | `verifier_partial` | Verifier finishes with status PARTIAL |
| `SKILL_READ` | `skill_read` | A skill file is read |
| `FILE_WRITE` | `file_write` | A file is created via the Write tool |
| `FILE_EDIT` | `file_edit` | A file is modified via the Edit tool |
| `E2E_RUN` | `e2e_run` | An end-to-end test execution is recorded |
| `UNIT_TEST_RUN` | `unit_test_run` | A unit test execution is recorded |
| `BUILD_CHECK` | `build_check` | A build check is recorded |
| `SCREENSHOT_CAPTURE` | `screenshot_capture` | A screenshot is captured |
| `WORKER_BRIEF` | `worker_brief` | Orchestrator prepares a worker brief |

## State Management

Unlike metrics (append-only history), state tracks mutable values that affect hook behavior during the current session.

**File:** `.godotmaker/state.json`

### API

| Function | Signature | Description |
|----------|-----------|-------------|
| `get` | `get(key: str, default=None) -> Any` | Read a state value |
| `put` | `put(key: str, value: Any) -> None` | Write a state value |
| `increment` | `increment(key: str) -> int` | Increment an integer value, returns new value |
| `reset` | `reset() -> None` | Reset to defaults (called at session start) |

### Default state

```json
{
  "stop_block_count": 0
}
```

### State keys used by hooks

| Key | Used By | Purpose |
|-----|---------|---------|
| `stop_block_count` | `check_completion.py` | Tracks how many times the Stop hook has blocked. Force-allows at 5. |
| `worker_report_block:{agent_id}` | `check_worker_report.py` | Per-agent block counter. Force-allows at 5. |

State is read from disk on every `get`/`increment` call and written back immediately. This ensures consistency when multiple hooks run in the same event cycle.

## Report Generation

The metrics reporter generates an HTML dashboard from JSONL event logs.

### Running the reporter

```bash
# Unix
bash shell/report.sh .godotmaker/metrics.jsonl
bash shell/report.sh .godotmaker/metrics.jsonl report.html

# Windows
shell\report.bat .godotmaker\metrics.jsonl
shell\report.bat .godotmaker\metrics.jsonl report.html
```

If no output path is given, the report is written to the same directory as the input file (e.g., `.godotmaker/report.html`).

Internally, both scripts run:
```
python -m hooks.metrics.reporter <input.jsonl> -o <output.html>
```

### Report sections

The HTML report contains these sections:

| Section | Contents |
|---------|----------|
| Overview | Total events, first/last timestamp, session duration |
| Highlights | Color-coded anomaly alerts (see below) |
| Subagents | Dispatch counts by type, outcome status distribution |
| Hook Blocks | Block counts per hook, last 20 block details |
| Gate Checks | Gate results (pass/fail/force_allow) by gate name |
| Errors and Retries | Error type distribution |
| Worker Outcomes | DONE/PARTIAL/FAILED counts |
| File Operations | Most modified files (top 15) |
| Verification Coverage | Worker-to-verifier/reviewer mapping table |
| Test Execution Summary | E2E, unit test, and build check pass/fail counts |
| Worker Granularity Analysis | Files per worker, duration, oversized worker flags |
| Event Timeline | Last 50 events with color-coded tags |

### Highlight rules

The report runs anomaly detection rules and displays color-coded alerts:

| Rule | Severity | Condition |
|------|----------|-----------|
| No Verifiers | critical | Workers dispatched but 0 verifiers |
| No Reviewers | critical | Workers dispatched but 0 reviewers |
| Gate Force-Allowed | critical | Any gate was force-allowed |
| All Status UNKNOWN | warning | Every subagent stop has UNKNOWN status |
| Tests Never Executed | critical | >5 test files written but 0 test runs recorded |
| Oversized Workers | warning | Any worker wrote >20 files |
| High Block Rate | warning | >30% of hook decisions were blocks (minimum 10 decisions) |
| Completion Fail Loop | warning | Completion gate failed 3+ times |

Severity colors: critical = red (`#d63031`), warning = orange (`#e17055`), info = blue (`#0984e3`).

## Role Detection

Agent roles are detected at two points in the pipeline:

### At SubagentStart (description parsing)

The `detect_role_from_description()` function in `log_subagent.py` parses the `description` field of the Agent tool call. It uses a two-phase approach:

1. **Prefix match** (highest confidence): Checks if the description starts with `analyst:`, `worker:`, `verifier:`/`verify:`, or `reviewer:`/`review:`
2. **Keyword fallback** (lower confidence): Searches for role keywords anywhere in the description. Order: analyst > reviewer > verifier > worker (specific roles checked first to avoid false matches)

The detected role is stored in the `SUBAGENT_START` metric event.

### At SubagentStop (lookup + fallback)

The `lookup_role_from_events()` function reads `metrics_current.jsonl` in reverse to find the `SUBAGENT_START` event with a matching `agent_id`, returning the role recorded at start time.

### Cross-event role matching

The `event_has_role()` utility checks if a metric event matches a given role. It checks two fields in order:

1. `role` field (set at SubagentStart from description parsing)
2. `report_type` field (set at SubagentStop from report content detection)

```python
from metrics import event_has_role

if event_has_role(event, "worker"):
    # True if event["role"] == "worker" OR event["report_type"] == "worker"
```

This two-field approach handles cases where role detection at start time fails but the report content clearly identifies the agent type.

## Report Type Detection

Report type detection uses a 3-layer system defined in `hooks/metrics/schema.py`. Each layer is tried in order; the first match wins.

### Layer 1: Exact marker (fastest)

Checks for exact substring matches against `REPORT_MARKERS`:

| Role | Marker |
|------|--------|
| worker | `## Report:` |
| verifier | `## Verification Report:` |
| reviewer | `## Review Report:` |
| analyst | `## Analyst Report:` |

### Layer 2: Flexible regex

Catches heading-level variations (`#`, `##`, `###`, `####`), spacing, and full/half-width colons:

| Role | Pattern |
|------|---------|
| analyst | `#{1,4}\s*Analyst\s+Report\s*[::]` |
| worker | `#{1,4}\s*Report\s*[::]` |
| verifier | `#{1,4}\s*Verification\s+Report\s*[::]` |
| reviewer | `#{1,4}\s*Review\s+Report\s*[::]` |

### Layer 3: Section fingerprint (last resort)

Detects reports by the presence of role-specific section headings:

| Role | Fingerprint Pattern |
|------|---------------------|
| analyst | `### Asset Summary` |
| worker | `### Status: (DONE\|PARTIAL\|FAILED)` |
| verifier | `### Overall: (PASS\|FAIL\|PARTIAL)` |
| reviewer | `### Reviewers? Matched` |

### Usage

```python
from metrics import detect_report_type

report_type = detect_report_type(message)
# Returns "worker", "verifier", "reviewer", "analyst", or None
```

## Key Exported Utilities

Summary of the public API from `hooks/metrics/__init__.py`:

| Function/Constant | Module | Description |
|--------------------|--------|-------------|
| `record_event(event_type, **details)` | `collector` | Append event to both JSONL logs |
| `read_events(log_path=None)` | `collector` | Read all events from history log (or custom path) |
| `read_current_events()` | `collector` | Read events from current session log |
| `start_session()` | `collector` | Truncate current session log |
| `EventType` | `schema` | String enum of all event types |
| `detect_report_type(message)` | `schema` | 3-layer report type detection |
| `event_has_role(event, role)` | `schema` | Check role OR report_type field |
| `REPORT_MARKERS` | `schema` | Exact marker strings per role |
| `REPORT_REQUIRED_SECTIONS` | `schema` | Required `(name, regex)` tuples per role |
| `REPORT_FORMAT_HINTS` | `schema` | Template strings shown in block messages |
| `REPORT_REQUIRED_LABELS` | `schema` | Comma-separated section names per role |
| `ROLE_WORKER`, `ROLE_VERIFIER`, etc. | `schema` | Canonical role name constants |
| `KNOWN_ROLES` | `schema` | Set of all valid role strings |
| `get_current_stage()` | `__init__` | Read highest completed stage from `stage.json` |
| `state.get(key, default)` | `state` | Read mutable state value |
| `state.put(key, value)` | `state` | Write mutable state value |
| `state.increment(key)` | `state` | Increment integer state value |
| `state.reset()` | `state` | Reset state to defaults |
