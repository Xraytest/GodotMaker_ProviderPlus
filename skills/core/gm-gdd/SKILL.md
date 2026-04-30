---
name: gm-gdd
description: |
  Game Design Document phase: interview the user, write GDD/PLAN/STRUCTURE/
  SCENES/TOC, mark new assets MISSING in ASSETS.md. Per-milestone once.
  First milestone creates these docs; subsequent milestones extend them.
  Explicit invocation only — use /gm-gdd.
disable-model-invocation: true
---

# GodotMaker GDD

$ARGUMENTS

You are running the design phase of a milestone. Output: GDD, PLAN, STRUCTURE, SCENES, TOC. New asset requirements get added to ASSETS.md as `MISSING` (filled in later by `/gm-asset`).

A milestone is one full pipeline cycle (gdd → asset → build → verify → evaluate → accept → finalize). Each `/gm-gdd` invocation drives exactly one milestone.

## Session Setup

**FIRST ACTION — before anything else:** Write `gdd` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If `project.godot` does not exist → STOP. Tell user to run `/gm-scaffold` first.
- If the **last event** has `role == "gdd"` → STOP. Tell the user:
  > "GDD already completed for this milestone at {timestamp}. Recommended next: /gm-asset.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (fresh project OR new milestone after a finalize).

## First Build vs New Milestone

Detect mode by file presence:

- **First build** (`GDD.md` does not exist): create all docs from scratch using `.claude/templates/`.
- **New milestone** (`GDD.md` exists; PLAN.md was archived by previous finalize): GDD/STRUCTURE/ASSETS/SCENES/TOC carry forward — **append** new sections rather than overwriting. PLAN.md is regenerated for this milestone's scope only.

## Hard Rules

1. **You CANNOT write game code (.gd/.tscn/.tres).** Code lives in workers in `/gm-build`.
2. **You CANNOT write to assets/.** Assets are produced in `/gm-asset`.
3. **Use AskUserQuestion for confirmation.** GDD must be explicitly confirmed by the user before writing PLAN.md.
4. **MUST NOT skip sub-stages.** Both 1a (interview) and 1b (decomposition) must complete.
5. **New milestone APPENDS — does not overwrite** GDD/STRUCTURE/ASSETS/SCENES/TOC.

## Sub-stages

### 1a — Interview & GDD Generation

Invoke the game-planner skill (`.claude/skills/game-planner/SKILL.md`).

- **First build:** game-planner runs full Socratic interview → produces `GDD.md`.
- **New milestone:** brief the user "what's this milestone about?" → game-planner appends a new milestone section to `GDD.md` (e.g., `## Milestone 2: Boss enemies`).

**Gate 1a:**
- [ ] GDD.md exists with at least: Game Overview, Core Gameplay Loop, Mechanics, Scope (first build) OR a new milestone section appended
- [ ] User has explicitly confirmed the GDD update

### 1b — Decomposition

After the GDD is confirmed, **delegate the entire decomposition to the `decomposer` subagent**.

```
Agent({
  subagent_type: "decomposer",
  description: "Decompose GDD into milestone artifacts",
  model: "{decomposer_model from .godotmaker/config.yaml, default: sonnet}",
  prompt: "{brief below}"
})
```

Brief:

```
## Task: Decompose GDD into milestone artifacts

### Mode
{first-build | new-milestone}

### Project Root
{absolute path to project root}

### GDD Path
{absolute path to GDD.md}

### Templates Dir
{absolute path to .claude/templates/}

### Project.godot Path
{absolute path to project.godot}

### Milestone Number
{N — count from stage.jsonl + 1, or 1 for first build}

### Manifest Path
{absolute path to assets/manifest.json — include only if file exists}

### Existing Artifact Paths (new-milestone only)
- PLAN.md: {path or "absent — will create"}
- STRUCTURE.md: {absolute path}
- SCENES.md: {absolute path}
- ASSETS.md: {absolute path}
- TOC.md: {absolute path}
```

The decomposer returns a short report: files written, project.godot changes, risk tasks, key architecture decisions. Hold this report — do NOT relay to the user yet. Run the gate check first; if you take over, the report is stale.

**Gate 1b:**
- [ ] PLAN.md exists with Task Status table (all `pending`), Risk Tasks section
- [ ] ASSETS.md has this milestone's assets marked `MISSING`
- [ ] SCENES.md covers all scenes for this milestone
- [ ] STRUCTURE.md has Components, Systems, Archetypes, Build Order for this milestone
- [ ] TOC.md updated

**Fallback when subagent doesn't finish.** If any gate item is unmet (whether the decomposer reported failure or just produced incomplete artifacts), do NOT respawn the subagent — instead, take over directly. Read whichever artifacts exist, identify the missing pieces, and write them using the same templates the decomposer would have used (`.claude/templates/PLAN.md` etc.). The templates themselves document their structure conventions.

**`new-milestone` mode dedupe rule.** Append-only files (STRUCTURE / SCENES / ASSETS / TOC) are non-idempotent: if the decomposer half-appended a milestone-N section before failing, blindly re-appending creates duplicates. Before adding milestone-N content to any of these files, grep for `## Milestone {N}` (or the equivalent marker the template uses) — if it already exists, only fill in the missing sub-sections under it; do NOT add a second milestone-N block.

**User-facing 1b summary (after gate + any fallback are complete).** Build the announcement from the final on-disk state, not the raw decomposer report. Combine: (a) the decomposer's `Risk Tasks Identified` and `Key Architecture Decisions` (still useful as design rationale), and (b) a fresh "files now on disk" line you observed yourself after fallback. If you took over for any file, say which ones — the user reads the actual files themselves.

**Cross-session backstop — what each hook actually does:**

- `stage_reminder.py` fires the moment you write `{"role": "gdd", ...}` to `.godotmaker/stage.jsonl` (a stage-complete write, not a next-stage entry). It validates that all 6 files in the `gdd` schema (`config/stage_schemas.json` → `gdd.files`) exist; if any are missing, it surfaces that to the lead before the gdd phase is considered done.
- `check_stage_prerequisites.py` fires when `/gm-build` (or `/gm-fixgap`) dispatches a worker — it re-validates the same 6-file schema. **It does NOT gate `/gm-asset`** (asset is not in `WORKER_DISPATCH_ROLES`); the asset phase relies on its own SKILL.md Resume Check instead.
- `check_completion.py` does NOT validate `gdd` at all — it only enforces worker-dispatch roles. Don't rely on it here.

So a partial 1b can still slip past `/gm-asset` if you skip the `stage_reminder` warning. The fallback above (lead takes over to fill missing files) is the primary safety net; the hooks are catch-up checks at later stages.

## Available Skills & Subagents

| Name | Type | Purpose |
|------|------|---------|
| game-planner | skill | Socratic interview → GDD generation (sub-stage 1a) |
| decomposer | subagent | Writes PLAN/STRUCTURE/SCENES/ASSETS/TOC + project.godot tweaks (sub-stage 1b) |
| godot-api | skill | Godot API reference (consumed by decomposer for project.godot edits) |

## When Done

After both gates pass:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "gdd", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `GDD complete. Recommended next: /gm-asset` (or skip straight to `/gm-build` if no new assets are needed for this milestone — `/gm-asset` is manual and will simply STOP if there's nothing MISSING).
