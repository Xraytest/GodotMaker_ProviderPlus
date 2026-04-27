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

After the GDD is confirmed:

#### Step 1: Generate (or regenerate) PLAN.md

PLAN.md is **per-milestone** — it gets archived at finalize. So always create fresh from `.claude/templates/PLAN.md`:

1. **Risk Tasks:** scan this milestone's GDD scope for features matching risk taxonomy (procedural generation, complex physics, custom shaders, etc.). Isolate as risk tasks.
2. **Main Build Tasks:** convert remaining mechanics + entities into system/component tasks.
3. Write PLAN.md with all tasks status `pending`.

#### Step 2: Update ASSETS.md

- **First build:** create from `.claude/templates/ASSETS.md`. Art Direction from GDD §4. Asset Table from GDD §9 — every asset starts as `MISSING`.
- **New milestone:** append new milestone's required assets to existing Asset Table, all marked `MISSING`. Existing `provided`/`generated` rows stay as-is.

#### Step 3: Update SCENES.md

- **First build:** create from `.claude/templates/SCENES.md` covering all scenes from GDD §7. For each UI element specify `Position` (anchor terms) and `Size` (viewport %).
- **New milestone:** append new scenes to the existing SCENES.md.

Minimum required scenes (first build only): Main Menu, Gameplay (HUD overlay), Game Over / Results.

#### Step 4: Update STRUCTURE.md

Design the ECS architecture for this milestone's scope:

- **First build:** create from `.claude/templates/STRUCTURE.md`. Components, Systems, Entity Archetypes, System Schedule, Build Order.
- **New milestone:** extend Component Registry / System Schedule / Archetypes with new entries. Update Build Order if new dependencies introduced.

Each task in PLAN.md must reference a specific system: not "implement movement" but "implement PlayerMovementSystem: reads PlayerInput + Velocity, writes Transform".

#### Step 5: Update project.godot (if needed)

If GDD design implies project-level config changes (viewport size, rendering method, main_scene path), update `project.godot` accordingly. Skip if generic defaults still fit.

#### Step 6: Update TOC.md

Update the document index. Add this milestone's records.

**Gate 1b:**
- [ ] PLAN.md exists with Task Status table (all `pending`), Risk Tasks section
- [ ] ASSETS.md has new milestone's assets marked `MISSING`
- [ ] SCENES.md covers all scenes for this milestone
- [ ] STRUCTURE.md has Components, Systems, Archetypes, Build Order for this milestone
- [ ] TOC.md updated

## Available Skills & Tools

| Skill | Purpose |
|-------|---------|
| game-planner | Socratic interview → GDD generation |
| godot-api | Godot API reference (for project.godot tweaks) |

## When Done

After both gates pass:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "gdd", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `GDD complete. Recommended next: /gm-asset` (or skip straight to `/gm-build` if no new assets are needed for this milestone — `/gm-asset` is manual and will simply STOP if there's nothing MISSING).
