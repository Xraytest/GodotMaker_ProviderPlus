# Stage 1: Requirements & Game Design

## Required Documents

| Document | Schema Check |
|----------|-------------|
| GDD.md | Required sections: Game Overview, Core Gameplay Loop, Mechanics (§3), Art Style (§4), Menu Flow (§7), Asset List (§9) |
| PLAN.md | Required: Task Status table with `pending` status column, Risk Tasks section |
| ASSETS.md | Required: Art Direction section, Asset Table with `status` column |
| SCENES.md | Required: at least 3 scene sections, each with Elements table containing Position and Size columns |

Documents listed here are verified by the stage gate hook. Missing or malformed documents block stage transition.

---

This stage has two sub-stages. Both must complete before proceeding.

---

## Stage 1a — Interview & GDD Generation

Invoke the game-planner skill (`.claude/skills/game-planner/SKILL.md`).

Game-planner handles the entire interview and GDD generation process — do NOT
duplicate its logic here. Just invoke it and wait for the confirmed GDD.

**Output:** `GDD.md` in the project root.

**Gate 1a:**
- [ ] GDD.md exists with at least: Game Overview, Core Gameplay Loop, Mechanics, Scope
- [ ] User has explicitly confirmed the GDD (after any Ask Maker modifications)

---

## Stage 1b — Asset Collection & Decomposition

After the GDD is confirmed, YOU (orchestrator) perform these steps:

### Step 1: Decompose GDD → PLAN.md

1. **Risk Tasks:** scan GDD §3 for features matching risk taxonomy (procedural generation,
   complex physics, custom shaders, etc.). Isolate as risk tasks.
2. **Main Build Tasks:** convert remaining mechanics + entities into system/component tasks.
3. Write PLAN.md from `.claude/templates/PLAN.md` template.

### Step 2: Generate ASSETS.md

Create ASSETS.md from `.claude/templates/ASSETS.md` template:
- Art Direction: from GDD §4
- Asset Table: from GDD §9 — list all required assets; art as `pending`, audio as `pending` (user must provide audio)

### Step 3: Generate SCENES.md

Create SCENES.md from `.claude/templates/SCENES.md` template:

1. Read GDD §7 (Menu Flow) to identify all distinct screens and scenes.
2. For each screen/scene, write one `## Scene:` section following the template format.
3. For every UI element, specify:
   - **Position** using anchor terms: `top-center`, `bottom-left`, `center`, etc.
   - **Size** as viewport percentage: e.g. `40%w × 15%h`
4. Fill in transitions based on GDD §7 navigation flow.
5. **Minimum required scenes:** Main Menu, Gameplay (HUD overlay), Game Over / Results.
6. Add additional scenes for any other distinct screens described in the GDD (pause menu, settings, etc.).

### Step 4: Create TOC.md

Create the document index from `.claude/templates/TOC.md` template:
- Fill in the game name
- All stage execution records listed as "pending" until their stage runs

---

**Gate 1:**
- [ ] GDD.md confirmed by user; art style description present in §4
- [ ] PLAN.md exists with Task Status table (all `pending`), Risk Tasks section
- [ ] ASSETS.md exists with Art Direction and Asset Table
- [ ] SCENES.md exists with at least 3 scenes, each having an Elements table
- [ ] TOC.md exists with document index

**After passing Gate 1:** Update `.godotmaker/stage.json` — add `"1": "<UTC timestamp>"` to `completed_stages`. Proceed to Stage 2.
