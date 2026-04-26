# Hooks Reference

Complete reference for all GodotMaker hooks. Hooks are Python scripts that run
on Claude Code events to enforce pipeline rules.

Registered in `config/settings.json`, deployed to `.godotmaker/hooks/` via publish.

---

## Hook Inventory

| Hook | Event | Matcher | Blocks? | Purpose |
|------|-------|---------|---------|---------|
| `session_start.py` | SessionStart | — | No | Clear session metrics, reset state |
| `check_file_permissions.py` | PreToolUse | Write\|Edit | Yes | Orchestrator can't write .gd/.tscn/.tres; workers can't write PLAN/STRUCTURE/ASSETS.md |
| `stage_reminder.py` | PreToolUse | Write\|Edit | No | Detect stage.json writes, inject next-stage reminder |
| `check_stage_prerequisites.py` | PreToolUse | Agent | Yes | Before worker dispatch, verify prerequisite stage files exist |
| `check_asset_access.py` | PreToolUse | Read | Yes | Block orchestrator from reading image files in assets/ |
| `log_subagent.py` | SubagentStart, SubagentStop | — | No | Record subagent lifecycle metrics (role, status, files changed) |
| `check_worker_report.py` | SubagentStop | — | Yes | Validate worker/verifier/reviewer/analyst report format and content |
| `check_completion.py` | Stop | — | Yes | Final gate: project completeness + orchestrator diligence |

---

## Detailed Descriptions

### session_start.py

**Event:** SessionStart
**Blocks:** Never

Clears `metrics_current.jsonl` (session log) and resets `state.json` counters.
Runs once at conversation start.

### check_file_permissions.py

**Event:** PreToolUse (Write|Edit)
**Blocks:** Yes

Two rules:
1. **Orchestrator** (agent_id empty) cannot write `.gd`, `.tscn`, `.tres` files.
   Must dispatch workers for game code.
2. **Workers/subagents** (agent_id present) cannot write `PLAN.md`, `STRUCTURE.md`, `ASSETS.md`.
   Planning docs are orchestrator-only.

Also records `FILE_WRITE` / `FILE_EDIT` metrics events for every file operation.

### stage_reminder.py

**Event:** PreToolUse (Write|Edit)
**Blocks:** Never

Watches for writes to `.godotmaker/stage.json`. When orchestrator marks a stage
complete:

1. **Validates stage outputs** — reads `config/stage_schemas.json`, checks file
   existence (`files` field) and runs programmatic checks (`checks` field).
   Blocks the write if validation fails.
2. **Injects reminder** — points orchestrator to next stage's detail file.

Programmatic checks (stages 4-8):
- `references_has_images` — references/ has ≥1 .png
- `metrics_has_worker_done` — metrics show ≥1 successful worker
- `plan_has_non_pending` — PLAN.md has ≥1 non-pending task
- `plan_no_pending` — PLAN.md has 0 pending tasks
- `metrics_has_verifier` — metrics show ≥1 verifier event
- `screenshots_match_scenes` — screenshots/ has ≥N .png where N = scene count in SCENES.md

### check_stage_prerequisites.py

**Event:** PreToolUse (Agent)
**Blocks:** Yes

Before the orchestrator dispatches any subagent, checks that prerequisite
stage outputs exist:

| Prerequisite | File/Dir |
|-------------|----------|
| Stage 1 (Requirements) | `PLAN.md` |
| Stage 2 (Architecture) | `STRUCTURE.md` |
| Stage 3 (Scaffold) | `project.godot` |
| Stage 3 (ECS Framework) | `addons/gecs/` |
| Stage 4 (Assets) | `ASSETS.md` |

Only checks the main agent (orchestrator), not sub-subagent dispatches.

Reads `config/stage_schemas.json` dynamically — covers all stages with `files`
fields. Checks `.godotmaker/stage.json` for which stages are completed, then
verifies all completed stages' output files exist.

### check_asset_access.py

**Event:** PreToolUse (Read)
**Blocks:** Yes

Blocks the orchestrator (main agent) from reading image files in `assets/`
directory. Image extensions: .png, .jpg, .jpeg, .svg, .webp, .gif, .bmp, .tga.

Subagents (analyst) are allowed. Non-image files (.json, .ogg) are allowed.

Purpose: Force orchestrator to delegate asset analysis to analyst subagent
instead of consuming context with raw image data.

### log_subagent.py

**Event:** SubagentStart, SubagentStop
**Blocks:** Never

**SubagentStart:** Detects role from Agent description field (`detect_role_from_description`),
records `SUBAGENT_START` metric with agent_id, agent_type, role, description.

Role detection order (prefix first, then keyword):
1. `analyst:` → analyst
2. `worker:` → worker
3. `verifier:` / `verify:` → verifier
4. `reviewer:` / `review:` → reviewer

**SubagentStop:** Extracts report type, status, files changed from assistant message.
Looks up role from start event. Records `SUBAGENT_STOP` metric.
Also records outcome-specific events: `WORKER_DONE`, `VERIFIER_PASS`, etc.

### check_worker_report.py

**Event:** SubagentStop
**Blocks:** Yes

Validates report format and content for all agent roles.

**Format detection flow:**
1. Detect report_type from message content (layered: exact marker → regex → fallback)
2. If report_type detected → check required sections for that type
3. If report_type is None but role is known (from start event) → block and demand formatted report

**Per-role required sections:**

| Role | Required Sections |
|------|------------------|
| worker | Status, Files Changed, Tests, Build, Memory Entry |
| verifier | Overall, Results, Adversarial Probes |
| reviewer | Reviewers Matched, ECS Review, Issues Found, Summary |
| analyst | Status, Asset Summary, Art Style Summary, Files Generated |

**Worker-specific deep checks:**
- `check_test_substance()` — Tests section must have unittest + e2e results with actual pass/fail output
- `check_e2e_files_exist()` — E2E test file paths in report must exist, be non-empty, non-placeholder
- `check_resource_paths()` — `res://` paths in .gd files must exist
- `check_classname_conflicts()` — `class_name` declarations must not conflict with Godot built-ins

**Progress reminder:** On successful validation, injects a progress summary
(workers done, verifiers done, reviewers done) as additional context.

**Reviewer substance check:** ECS Review and Issues Found sections must each
have ≥50 characters of content. Prevents empty/trivial reviews.

**Gaps:**
- Verifier reports: no check that tests were actually run (only format)
- No per-worker screenshot validation (screenshots checked at stage 8 completion)

### check_completion.py

**Event:** Stop
**Blocks:** Yes

Final gate when orchestrator tries to end the conversation. Two checks:

1. **Project completeness:** Runs `tools/check_project.py --all` on the game
   project directory. Checks for FAIL lines.
2. **Orchestrator diligence:** Verifies workers, verifiers, and reviewers were
   dispatched (from metrics events). If workers dispatched but 0 verifiers or
   0 reviewers → block.

**Anti-deadloop:** After 5 blocks (`BLOCK_LIMIT`), force-allows with a warning
to prevent infinite retry loops.

---

## Event Flow Diagram

```
SessionStart
  └── session_start.py (clear metrics)

PreToolUse(Write|Edit)
  ├── check_file_permissions.py (block .gd from orchestrator)
  └── stage_reminder.py (detect stage.json, inject reminder)

PreToolUse(Agent)
  └── check_stage_prerequisites.py (block if prerequisites missing)

PreToolUse(Read)
  └── check_asset_access.py (block orchestrator from reading assets/ images)

SubagentStart
  └── log_subagent.py (record start + role)

SubagentStop
  ├── log_subagent.py (record stop + outcome)
  └── check_worker_report.py (validate report, block if incomplete)

Stop
  └── check_completion.py (project check + diligence check)
```

---

## Known Gaps (TODO)

1. **Verifier test execution:** No hook verifies that verifiers actually RAN
   tests (vs just reporting format-correct results). Spot-check is prompt-level
   only.
