# Orchestrator Pipeline

The orchestrator runs a mandatory 8-stage pipeline to transform a natural language game description into a working Godot project. Stages cannot be skipped or reordered. Each stage has a gate -- a set of validation checks that must pass before the pipeline advances.

## Pipeline Overview

```
Stage 1: Requirements      -->  GDD.md, PLAN.md, ASSETS.md, SCENES.md, TOC.md
Stage 2: Architecture       -->  STRUCTURE.md
Stage 3: Scaffold           -->  project.godot, addons, component/system stubs
Stage 4: Assets             -->  reference images, asset manifest
Stage 5: Risk Implementation-->  risk systems implemented + tested
Stage 6: Main Implementation-->  all systems implemented + tested
Stage 7: Integration        -->  full verification suite passes
Stage 8: Final Acceptance   -->  screenshots match scenes, user informed
```

Progress is tracked in `.godotmaker/stage.json`, which records a UTC timestamp for each completed stage:

```json
{
  "completed_stages": {
    "1": "2026-04-19T03:38:56Z",
    "2": "2026-04-19T03:39:12Z",
    "3": "2026-04-19T03:45:08Z"
  }
}
```

## Stage Details

### Stage 1: Requirements and Game Design

**Goal**: Produce a complete game design and project plan from a user's natural language description.

**Process**:
1. **Stage 1a -- Interview**: Invoke the `game-planner` skill, which conducts a Socratic interview with the user and generates `GDD.md`.
2. **Stage 1b -- Decomposition**: The orchestrator decomposes the confirmed GDD into planning documents.

**Inputs**: User's game description (natural language).

**Outputs**:

| Document | Content |
|----------|---------|
| `GDD.md` | Game Overview, Core Gameplay Loop, Mechanics, Art Style, Menu Flow, Asset List |
| `PLAN.md` | Task Status table (all `pending`), Risk Tasks section |
| `ASSETS.md` | Art Direction, Asset Table with status column |
| `SCENES.md` | At least 3 scenes, each with Elements table (Position, Size columns) |
| `TOC.md` | Document index |

**Gate 1 validation** (`config/stage_schemas.json`):
- Files exist: `GDD.md`, `PLAN.md`, `ASSETS.md`, `SCENES.md`, `TOC.md`
- GDD confirmed by user
- PLAN.md has Task Status table with Risk Tasks section
- SCENES.md has at least 3 scene sections with Elements tables

---

### Stage 2: Architecture

**Goal**: Design the ECS architecture -- components, systems, entity archetypes, and build order.

**Inputs**: Confirmed `GDD.md` (Mechanics and Characters/Entities sections).

**Outputs**:

| Document | Content |
|----------|---------|
| `STRUCTURE.md` | Component Registry, System Schedule, Entity Archetypes, Build Order |

**Gate 2 validation**:
- File exists: `STRUCTURE.md`
- Component Registry has at least 1 game-specific component
- System Schedule has at least 1 system per phase (Input / Logic / Materialization / Cleanup)
- Entity Archetypes section present
- Build Order section present
- PLAN.md tasks updated to match systems

---

### Stage 3: Scaffold

**Goal**: Generate a compilable Godot project skeleton with all required addons.

**Inputs**: `STRUCTURE.md` (component and system definitions).

**Outputs**:
- `project.godot` with correct configuration
- `addons/gecs/` -- ECS framework (pinned version from `addon_versions.json`)
- `addons/gdunit4/` -- unit test framework
- godot-e2e addon installed and enabled
- Base component definition files
- Empty system stub files with correct class signatures
- `e2e/conftest.py` with GodotE2E fixture
- Git repository initialized (required for worktree isolation)

**Gate 3 validation**:
- Files exist: `project.godot`, `addons/gecs/`
- `check_project.py --build --ecs` passes with no FAIL lines
- At least 1 Component file and 1 System file exist
- `e2e/conftest.py` exists
- Git repo initialized with at least one commit

Note: Unit test coverage is intentionally NOT checked at Gate 3 -- systems are empty stubs.

---

### Stage 4: Assets

**Goal**: Collect user-provided assets and generate missing visual assets.

**Process**:
1. Ask user for art and audio files (audio is always user-provided, no AI audio generation)
2. If assets provided: dispatch analyst subagent to generate `assets/manifest.json`
3. Generate scene reference images (`references/scene_{name}.png`) for each scene in SCENES.md
4. Show references to user for approval
5. Generate remaining missing art assets using AI

**Inputs**: `ASSETS.md`, `SCENES.md`, user-provided files.

**Outputs**:
- `references/scene_{name}.png` for each scene (or explicit N/A with user approval)
- `assets/manifest.json` (if user provided assets)
- All art assets marked `provided`, `generated`, or `N/A`

**Gate 4 validation**:
- Check `references_has_images`: at least 1 `.png` in `references/` directory
- If user assets: `manifest.json` exists with valid structure
- ASSETS.md art direction filled
- All art assets accounted for

**Important constraint**: The orchestrator must NOT read image files in `assets/` directly. The `check_asset_access` hook blocks this -- analysis must be delegated to an analyst subagent.

---

### Stage 5: Risk Implementation

**Goal**: Implement high-risk systems in isolation before the main build. If PLAN.md has no risk tasks, skip to Stage 6.

Risk tasks are features matching a risk taxonomy: procedural generation, complex physics, custom shaders, etc.

**Process**: For each risk task, run the **Implement -> Verify -> Next** loop:
1. Dispatch Worker -- implements system + unit tests + E2E tests
2. Dispatch Verifier -- re-runs build + tests
3. Orchestrator Spot-Check -- re-runs subset of checks
4. Dispatch Reviewer -- domain-specific code review
5. Update PLAN.md + MEMORY.md

**Gate 5 validation**:
- Checks `metrics_has_worker_done`: at least 1 `worker_done` event in metrics
- Checks `plan_has_non_pending`: at least 1 task is no longer `pending`
- `check_project.py --build --ecs --tests` passes
- Each system file has a corresponding unit test file

---

### Stage 6: Main Implementation

**Goal**: Implement all remaining systems following the build order from STRUCTURE.md.

**Process**: Same **Implement -> Verify -> Next** loop as Stage 5, for every remaining task. Infrastructure first (components, core systems), then features.

Parallel workers may be dispatched, but no two concurrent workers may write to the same file. Workers use git worktree isolation.

**Gate 6 validation**:
- Checks `metrics_has_new_worker_done`: additional `worker_done` events since Stage 5
- Checks `plan_no_pending`: zero `pending` tasks remain in PLAN.md
- `check_project.py --all` passes with no FAIL lines

---

### Stage 7: Integration Verification

**Goal**: Full-project verification after all implementation is complete.

**Process**: Dispatch a Sonnet Verifier for comprehensive checks:
1. Build: `godot --headless --quit` -- zero ERROR lines
2. Unit tests: full gdUnit4 suite
3. E2E tests: all scenarios
4. Lint: `gdlint .` -- no errors
5. Static check: `check_project.py --all`
6. Visual cross-check: capture screenshots per scene, compare against references

The orchestrator must spot-check the verifier report (mandatory format defined in SKILL.md), including at least 1 E2E test re-run with screenshots.

**Gate 7 validation**:
- Checks `metrics_has_verifier`: at least 1 verifier event in metrics
- Build, unit tests, E2E tests, lint all pass
- Spot-check confirmed
- Visual cross-check completed

**Gate 7 blockers** (automatic failure):
- Empty E2E test files or files containing "placeholder" / "TODO"
- Spot-check that only ran build without running tests
- Test results reported without actual command output

---

### Stage 8: Final Acceptance

**Goal**: Capture gameplay evidence, run visual QA, and present results to the user.

**Process**:
1. Capture 3+ gameplay screenshots using the screenshot skill
2. Feed screenshots to VQA skill -- compare against reference images and SCENES.md layout descriptions
3. If runtime issues: escalate to MCP for live debugging
4. Present final report to user

**Gate 8 validation**:
- Checks `screenshots_match_scenes`: `screenshots/` has at least as many `.png` files as scenes in SCENES.md
- Game runs without crash (confirmed by E2E)
- At least one screenshot captured
- VQA completed
- Key scenes match SCENES.md descriptions

**Gate 8 blockers** (automatic failure):
- "N/A" or "placeholder" for any check
- No screenshot captured
- Game crashes on launch or during E2E

---

## Stage Schema Validation

Gate checks are defined in `config/stage_schemas.json` and enforced by the `stage_reminder` hook whenever the orchestrator writes to `stage.json`:

```json
{
  "1": { "files": ["GDD.md", "PLAN.md", "ASSETS.md", "SCENES.md", "TOC.md"] },
  "2": { "files": ["STRUCTURE.md"] },
  "3": { "files": ["project.godot", "addons/gecs/"] },
  "4": { "checks": ["references_has_images"] },
  "5": { "checks": ["metrics_has_worker_done", "plan_has_non_pending"] },
  "6": { "checks": ["metrics_has_new_worker_done", "plan_no_pending"] },
  "7": { "checks": ["metrics_has_verifier"] },
  "8": { "checks": ["screenshots_match_scenes"] }
}
```

Stages 1-3 use **file existence checks** -- the required documents must physically exist. Stages 4-8 use **programmatic checks** -- Python functions that inspect directory contents, metrics events, or document content.

## Hook Enforcement by Stage

| Hook | Stages Active | What It Does |
|------|---------------|--------------|
| `session_start` | All | Initializes metrics at session start |
| `check_file_permissions` | All | Blocks orchestrator from writing `.gd`/`.tscn`/`.tres`; blocks workers from writing planning docs |
| `check_asset_access` | 4+ | Blocks orchestrator from reading images in `assets/` |
| `check_stage_prerequisites` | 5+ | Before dispatching a worker, verifies all earlier stage outputs exist |
| `stage_reminder` | All | Validates stage outputs on `stage.json` write; injects next-stage pointer |
| `log_subagent` | 5+ | Records worker/verifier dispatches and completions (never blocks) |
| `check_worker_report` | 5+ | Validates report structure when workers/verifiers/reviewers finish |
| `check_completion` | 7+ | On Stop: forced self-review, project completeness, diligence check |

The `check_completion` hook is stage-aware: before Stage 7, the orchestrator may stop freely (e.g., waiting for user input). Full enforcement only applies at Stage 7 and beyond.

## Resume and Iteration

The pipeline supports two resume modes:

**Continue Interrupted Work**: If `stage.json` and `PLAN.md` exist with incomplete tasks, the orchestrator finds the earliest incomplete task, determines its stage, and resumes from there.

**Incremental Iteration**: If the user requests changes to an existing game (all previous tasks completed):
1. New tasks are added to PLAN.md as `pending`
2. STRUCTURE.md is updated if needed
3. Pipeline jumps to Stage 6 (new tasks only)
4. Followed by Stage 7 (integration) and Stage 8 (final)

Scaffolding (Stage 3) and asset generation (Stage 4) are not re-run unless the change requires them. Completed tasks are not re-implemented unless the change breaks them.
