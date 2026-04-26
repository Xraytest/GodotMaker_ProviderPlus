# Hook Reference

Detailed reference for all 8 hook scripts. Each hook is a Python script in the `hooks/` directory, deployed to `.godotmaker/hooks/` via the publish script.

---

## 1. session_start.py

**Event:** SessionStart
**Matcher:** (none)
**Blocks:** Never

Initializes the metrics system for a new Claude Code session.

**Actions:**
- Calls `start_session()` to truncate `.godotmaker/metrics_current.jsonl` (session-scoped log)
- Calls `state.reset()` to reset `.godotmaker/state.json` to defaults (clears block counters)
- Reads `.godotmaker/version` and injects the deployed GodotMaker version as `additionalContext`

**Output (when version file exists):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "[GodotMaker v0.3.0]"
  }
}
```

---

## 2. check_file_permissions.py

**Event:** PreToolUse
**Matcher:** `Write|Edit`
**Blocks:** Yes

Enforces role-based file write restrictions. Two rules:

| Agent | Blocked Files | Reason |
|-------|---------------|--------|
| Orchestrator (empty `agent_id`) | `.gd`, `.tscn`, `.tres` | Must dispatch workers for game code |
| Subagents (non-empty `agent_id`) | `PLAN.md`, `STRUCTURE.md`, `ASSETS.md` | Planning docs are orchestrator-only |

**Side effects:** Records `FILE_WRITE` or `FILE_EDIT` metric events for every file operation, regardless of whether it blocks.

**Block conditions:**
- Orchestrator writes a file with extension `.gd`, `.tscn`, or `.tres`
- Subagent writes a file named `plan.md`, `structure.md`, or `assets.md` (case-insensitive)

**Bypass conditions:**
- Orchestrator writing non-game files (`.md`, `.json`, `.cfg`, etc.) -- allowed
- Subagent writing game code files -- allowed (that is their job)
- Path normalization uses forward slashes and lowercase for cross-platform matching

---

## 3. stage_reminder.py

**Event:** PreToolUse
**Matcher:** `Write|Edit`
**Blocks:** Yes (conditionally)

Watches for writes to `.godotmaker/stage.json`. When the orchestrator marks a stage complete, this hook validates the stage outputs and injects a reminder for the next stage.

**Trigger condition:** The `file_path` in the tool input ends with `.godotmaker/stage.json`.

**Validation flow:**
1. Parse the stage number from the content being written (supports both `{"completed_stage": N}` and `{"completed_stages": {"1": "...", "2": "..."}}` formats)
2. Load `config/stage_schemas.json` (deployed as `.godotmaker/stage_schemas.json`)
3. Check file existence for the `files` array in the stage schema
4. Run programmatic checks listed in the `checks` array

**Programmatic checks:**

| Check Name | Stage | Condition |
|------------|-------|-----------|
| `references_has_images` | 4 | `references/` has at least 1 `.png` file |
| `metrics_has_worker_done` | 5, 6 | Metrics contain at least 1 `worker_done` event |
| `plan_has_non_pending` | 5 | `PLAN.md` has at least 1 task marked completed or in_progress |
| `plan_no_pending` | 6 | `PLAN.md` has 0 tasks marked pending |
| `metrics_has_verifier` | 7 | Metrics contain at least 1 verifier event (pass/fail/partial) |
| `screenshots_match_scenes` | 8 | `screenshots/` has >= N `.png` files where N = scene count in `SCENES.md` |

**Block conditions:** Any validation issue (missing file or failed programmatic check) blocks the stage completion write.

**On success:** Injects a reminder pointing to the next stage's detail file:
```
[Stage 3 complete] Next: Stage 4. Read the detail file before proceeding: stages/stage4_assets.md
```

**Stage detail files:**

| Stage | File |
|-------|------|
| 1 | `stages/stage1_requirements.md` |
| 2 | `stages/stage2_architecture.md` |
| 3 | `stages/stage3_scaffold.md` |
| 4 | `stages/stage4_assets.md` |
| 5 | `stages/stage5_risk_impl.md` |
| 6 | `stages/stage6_main_impl.md` |
| 7 | `stages/stage7_integration.md` |
| 8 | `stages/stage8_final.md` |

---

## 4. check_stage_prerequisites.py

**Event:** PreToolUse
**Matcher:** `Agent`
**Blocks:** Yes

Prevents the orchestrator from dispatching subagents when prerequisite stage outputs are missing.

**Trigger condition:** The orchestrator (empty `agent_id`) invokes the `Agent` tool.

**Check logic:**
1. Read the current stage from `.godotmaker/stage.json` via `get_current_stage()`
2. Load `config/stage_schemas.json`
3. For each completed stage (1 through current), verify all files listed in the stage schema's `files` array exist

**Block conditions:** Any file from a completed stage's schema is missing on disk.

**Bypass conditions:**
- Subagent dispatching a sub-subagent (non-empty `agent_id`) -- not checked
- No `stage_schemas.json` file found -- silently allows
- Current stage is 0 (no stages completed) -- nothing to check

**Block message example:**
```
Cannot dispatch worker -- prerequisite stage outputs missing:
  - Stage 1: PLAN.md not found
  - Stage 3: project.godot not found
Complete earlier stages first. See SKILL.md Mandatory Pipeline.
```

---

## 5. check_asset_access.py

**Event:** PreToolUse
**Matcher:** `Read`
**Blocks:** Yes

Prevents the orchestrator from consuming context by reading raw image files in the `assets/` directory.

**Block conditions (all must be true):**
- The agent is the orchestrator (empty `agent_id`)
- The file path contains `/assets/` or starts with `assets/`
- The file extension is an image type: `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`, `.gif`, `.bmp`, `.tga`

**Bypass conditions:**
- Subagents (analyst, worker, etc.) reading any file -- allowed
- Orchestrator reading non-image files in `assets/` (`.json`, `.ogg`, `.txt`) -- allowed
- Orchestrator reading images outside `assets/` -- allowed

**Block message:**
```
Orchestrator cannot read image files in assets/ directly.
Dispatch an analyst subagent to analyze 'player_sprite.png' instead.
See analyst-dispatch.md for the protocol.
```

---

## 6. log_subagent.py

**Event:** SubagentStart, SubagentStop
**Matcher:** (none)
**Blocks:** Never

Records subagent lifecycle events to the metrics system. This hook never blocks -- it is purely observational.

### SubagentStart

Detects the agent role from the `description` field using `detect_role_from_description()`:

**Role detection order (prefix match first, then keyword fallback):**

| Priority | Pattern | Detected Role |
|----------|---------|---------------|
| 1 | Description starts with `analyst:` | analyst |
| 2 | Description starts with `worker:` | worker |
| 3 | Description starts with `verifier:` or `verify:` | verifier |
| 4 | Description starts with `reviewer:` or `review:` | reviewer |
| 5 | Description contains `analyst` or `analyze` | analyst |
| 6 | Description contains `reviewer` or `review` | reviewer |
| 7 | Description contains `verifier` or `verify` | verifier |
| 8 | Description contains `worker` | worker |
| 9 | None of the above | unknown |

Records a `SUBAGENT_START` metric with `agent_id`, `agent_type`, `role`, and `description`.

### SubagentStop

1. Detects report type from the subagent's final message using `detect_report_type()` (3-layer matching, see [metrics-and-state.md](metrics-and-state.md))
2. Extracts status from the message (`DONE`, `PARTIAL`, `FAILED`, `PASS`, `FAIL`)
3. Extracts file paths from the `### Files Changed` section
4. Looks up the role recorded at SubagentStart for this `agent_id`

Records a `SUBAGENT_STOP` metric, then records an outcome-specific event:

| Effective Role | Status | Event Recorded |
|----------------|--------|----------------|
| worker | DONE | `WORKER_DONE` |
| worker | PARTIAL | `WORKER_PARTIAL` |
| worker | FAILED | `WORKER_FAILED` |
| verifier | PASS | `VERIFIER_PASS` |
| verifier | FAIL | `VERIFIER_FAIL` |
| verifier | PARTIAL | `VERIFIER_PARTIAL` |

The "effective role" is the role from the start event if known, otherwise falls back to the detected `report_type`.

---

## 7. check_worker_report.py

**Event:** SubagentStop
**Matcher:** (none)
**Blocks:** Yes

Validates subagent report format and content. The most complex hook in the system.

### Anti-deadloop

Tracks per-agent block count via `state.json` key `worker_report_block:{agent_id}`. After 5 blocks (`BLOCK_LIMIT`), force-allows with a warning to stderr.

### Report detection flow

1. Run `detect_report_type(message)` -- returns `"worker"`, `"verifier"`, `"reviewer"`, `"analyst"`, or `None`
2. If a report type is detected, check required sections for that type
3. If report type is `None` but the agent has a known role (from SubagentStart), block and demand a formatted report

### Required sections by role

| Role | Required Sections |
|------|-------------------|
| worker | `### Status: (DONE\|PARTIAL\|FAILED)`, `### Files Changed`, `### Tests`, `### Build`, `### Memory Entry` |
| verifier | `### Overall: (PASS\|FAIL\|PARTIAL)`, `### Results`, `### Adversarial Probes` |
| reviewer | `### Reviewers Matched`, `### ECS Review`, `### Issues Found`, `### Summary` |
| analyst | `### Status: (DONE\|PARTIAL\|FAILED)`, `### Asset Summary`, `### Art Style Summary`, `### Files Generated` |

### Worker deep checks

After section validation passes, worker reports undergo additional checks:

**`check_test_substance()`** -- The `### Tests` section must:
- Be at least 20 characters long
- Contain test file paths matching `test[_/].*\.gd`
- Mention both unit tests and e2e tests
- Include actual e2e run results with pass/fail counts (e.g., "1 scenario passed")
- Not contain placeholder keywords (`placeholder`, `TODO`, `stub`, `not implemented`)

**`check_e2e_files_exist()`** -- E2E test file paths extracted from the report must:
- Exist on disk (checks both main project and `.claude/worktrees/agent-*/` directories)
- Be at least 50 characters long (not empty stubs)
- Not contain placeholder keywords
- Only checked when `project.godot` exists (inside a Godot project)

**`check_resource_paths()`** -- `res://` paths in `.gd` files listed in `### Files Changed` must:
- Resolve to actual files on disk (checks main project and worktrees)
- Commented-out lines (starting with `#`) are skipped

**`check_classname_conflicts()`** -- `class_name` declarations in `.gd` files must not conflict with Godot built-in names. Checked names include: `Key`, `Node`, `Node2D`, `Node3D`, `World`, `System`, `Resource`, `Timer`, `Signal`, `Error`, `Input`, `Label`, `Button`, `Control`, `Camera2D`, `Camera3D`, `Sprite2D`, `Object`, `RefCounted`.

### Reviewer substance check

**`check_reviewer_substance()`** -- The `### ECS Review` and `### Issues Found` sections must each contain content (not be empty). Prevents reviewers from submitting structurally correct but empty reports.

### Progress reminder

On successful validation, injects a progress summary as `additionalContext`:
```
[Progress] Workers: 3 done | Verifiers: 2 | Reviewers: 1.
Reminder: Every worker needs a verifier + reviewer. Do NOT stop without completing Stage 7 + 8.
```

---

## 8. check_completion.py

**Event:** Stop
**Matcher:** (none)
**Blocks:** Yes

Final gate when the orchestrator tries to end the conversation. Only checks the main agent (subagents can stop freely).

### Stage awareness

At stages < 7 (`ENFORCEMENT_STAGE`), the hook allows the stop without any checks. Full enforcement only applies at integration/final stages.

### Anti-deadloop

After 5 blocks (`BLOCK_LIMIT`) tracked via `state.json` key `stop_block_count`, force-allows with a warning.

### Check sequence

**Check 0 -- Forced self-review (first Stop only):**
On the first Stop attempt (`block_count == 0`), unconditionally blocks to force the orchestrator to verify:
1. Every system has E2E tests that pass
2. Every UI/scene has a screenshot in `screenshots/`
3. All screenshots match `SCENES.md` expectations

Injects current status metrics (E2E run count, screenshot count, scene count).

**Check 1 -- Project completeness (subsequent attempts):**
Runs `tools/check_project.py --all` against the game project directory. Looks for `tools/check_project.py` first, then falls back to `.claude/tools/check_project.py`. Collects all `[FAIL]` lines from the output.

**Check 2 -- Orchestrator diligence:**
Reads session metrics to verify:
- If workers were dispatched, at least 1 verifier must also have been dispatched
- If workers were dispatched, at least 1 reviewer must also have been dispatched
- Uses both SubagentStart (role field) and SubagentStop (role/report_type) for detection

**Check 3 -- E2E and screenshot coverage:**
- At least 1 `e2e_run` event must exist in metrics
- `screenshots/` must have >= N `.png` files where N = scene count in `SCENES.md`

**Block message example:**
```
Cannot finish -- issues found:
  Dispatched 3 workers but 0 verifiers. Verification is mandatory.
  No E2E test runs recorded in metrics.
  screenshots/ has 1 images but SCENES.md defines 3 scenes.
```

### Project root detection

The hook searches for `project.godot` in the current directory first, then in immediate subdirectories. This handles both cases where the CWD is the game project itself or the GodotMaker workspace.

---

## Hook Execution Order

When multiple hooks fire on the same event, they execute in the order listed in `config/settings.json`:

```
SessionStart
  1. session_start.py

PreToolUse (Write|Edit)
  1. check_file_permissions.py
  2. stage_reminder.py

PreToolUse (Agent)
  1. check_stage_prerequisites.py

PreToolUse (Read)
  1. check_asset_access.py

SubagentStart
  1. log_subagent.py

SubagentStop
  1. log_subagent.py
  2. check_worker_report.py

Stop
  1. check_completion.py
```

If `check_file_permissions.py` blocks a write, `stage_reminder.py` may not execute for that event.
