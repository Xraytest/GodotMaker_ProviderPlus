---
name: gm-finalize
description: |
  Finalize the project: verify document consistency, archive results, clean up runtime state.
  Explicit invocation only — use /gm-finalize.
disable-model-invocation: true
---

# GodotMaker Finalize

$ARGUMENTS

You are finalizing a completed game project. Your job is to ensure everything is consistent, documented, and clean.

## Session Setup

**FIRST ACTION — before anything else:** Write `finalize` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y, ...}`.

- If **no event with `role == "accept"` and `decision == "accept"`** exists anywhere in the file → STOP. Tell user to run `/gm-accept` first.
  (Events with `decision == "fix"` or `decision == "done"` are trace records, not completions.)
- If the **last event** has `role == "finalize"` → STOP. Tell the user:
  > "Finalize already recorded at {timestamp}. Project milestone is closed. Run /gm-gdd to start a new milestone.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed.

## Process

### 1. Quick Sanity Check

- `godot --headless --quit 2>&1` — builds clean
- `PLAN.md` — no `pending` or `in_progress` tasks
- `.godotmaker/evaluation.json` exists with `result: "approve"`

### 2. Document Consistency Check

This is the most important step. Ensure game docs match the actual game:

**For each document, verify and update if needed:**

- **GDD.md**: Does the game description still match what was built? If the user changed requirements mid-build, update GDD to reflect what was actually delivered.
- **PLAN.md**: All tasks should be `verified`. If any are `completed` but not `verified`, note this.
- **STRUCTURE.md**: Do the listed Components and Systems match what actually exists in the code? Run a quick check: list all `extends Component` and `extends System` files and compare against STRUCTURE.md.
- **ASSETS.md**: Do listed assets match what's in the `assets/` directory?
- **SCENES.md**: Do scene descriptions match the actual scenes?
- **MEMORY.md**: Are there unresolved issues or discoveries that should be surfaced?

**For any inconsistency found:**
- If it's a changed requirement → update the document to match reality
- If it's an unresolved issue → record it in the final report under `unresolved_issues`
- Do NOT change code — only update documentation

### 3. Generate Final Report

Read `.godotmaker/stage.jsonl` for the actual completed-role events. Write `.godotmaker/final_report.json`:

```json
{
  "status": "completed",
  "completed_at": "UTC timestamp",
  "stages_completed": {},
  "summary": {
    "systems": ["list of implemented systems"],
    "components": ["list of components"],
    "features": ["key features from GDD"],
    "test_count": {"unit": 0, "e2e": 0}
  },
  "doc_updates": ["list of documents updated in this step"],
  "unresolved_issues": ["issues that could not be fixed, documented for future work"],
  "known_limitations": ["from MEMORY.md"]
}
```

`stages_completed` should be derived from the actual `.godotmaker/stage.jsonl` events (e.g., a `{role: ts}` map built from the log), not hardcoded.

### 4. Update Stage

Append a line to `.godotmaker/stage.jsonl`: `{"role": "finalize", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.

### 5. Archive Milestone State

Close the milestone by moving its transient state into `.godotmaker/milestones/<N>/`. Subsequent milestones start with a clean slate.

**Determine milestone number N:**
```
N = (number of existing subdirectories under .godotmaker/milestones/) + 1
```
Create `.godotmaker/milestones/<N>/` if needed.

**Move into the milestone directory:**
- `.godotmaker/stage.jsonl` → `.godotmaker/milestones/<N>/stage.jsonl`
- `PLAN.md` → `.godotmaker/milestones/<N>/PLAN.md`
- `.godotmaker/evaluation.json` → `.godotmaker/milestones/<N>/evaluation.json`
- `.godotmaker/final_report.json` → `.godotmaker/milestones/<N>/final_report.json`
- `.godotmaker/gaps/` (if exists) → `.godotmaker/milestones/<N>/gaps/`
- `e2e/screenshots/` (if exists) → `.godotmaker/milestones/<N>/screenshots/` — next milestone's evaluator captures fresh ones; archived snapshots preserve audit trail

**Keep at project root (cumulative across milestones):**
- `GDD.md`, `STRUCTURE.md`, `ASSETS.md`, `SCENES.md`, `TOC.md`
- `MEMORY.md` and `memory/`
- All game code (`src/`, `scenes/`, `e2e/` (test files only — screenshots archived above), `assets/`, `references/`, `addons/`, `project.godot`)

After archive, the next `/gm-gdd` invocation sees an empty `stage.jsonl` and treats it as a new milestone.

### 6. Clean Up Runtime State

Remove or reset remaining `.godotmaker` runtime artifacts:
- Delete `.godotmaker/current_role` (no lingering role lock)
- Delete `.godotmaker/metrics_current.jsonl` (session metrics — history in `metrics.jsonl` is preserved)
- Delete `.godotmaker/traces/` directory (debug traces)
- Keep: `.godotmaker/milestones/`, `.godotmaker/config.yaml`, `.godotmaker/hooks/`, `.godotmaker/version`, `.godotmaker/metrics.jsonl`

### 7. Inform User

Present a concise completion summary:

```
## Milestone {N} Complete

**{game_name}** milestone {N} is shipped.

- {N} systems, {M} components
- {X} unit tests, {Y} e2e tests
- Documents updated: {list or "none needed"}
- Unresolved issues: {list or "none"}
- Known limitations: {list or "none"}
- Archived to: .godotmaker/milestones/{N}/

To run: {instructions}
To start a new milestone: /gm-gdd
```
