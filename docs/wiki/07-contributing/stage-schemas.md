# Stage Schemas

Defines the required outputs and validation checks for each stage of the GodotMaker build pipeline.

## Location

```
config/stage_schemas.json          (source, in GodotMaker repo)
<project>/.godotmaker/stage_schemas.json  (deployed to target project)
```

Deployed by the publish system on every publish (always overwritten).

## Format

Each entry maps a stage number (as a string key) to an object containing `files` (required file paths) and/or `checks` (programmatic validation functions).

```json
{
  "1": {
    "files": ["GDD.md", "PLAN.md", "ASSETS.md", "SCENES.md", "TOC.md"]
  },
  "5": {
    "checks": ["metrics_has_worker_done", "plan_has_non_pending"]
  }
}
```

## All 8 Stages

| Stage | Name | Requirements |
|---|---|---|
| 1 | Planning | **Files**: `GDD.md`, `PLAN.md`, `ASSETS.md`, `SCENES.md`, `TOC.md` |
| 2 | Structure | **Files**: `STRUCTURE.md` |
| 3 | Project Setup | **Files**: `project.godot`, `addons/gecs/` |
| 4 | Asset Preparation | **Checks**: `references_has_images` |
| 5 | First Implementation | **Checks**: `metrics_has_worker_done`, `plan_has_non_pending` |
| 6 | Full Implementation | **Checks**: `metrics_has_new_worker_done`, `plan_no_pending` |
| 7 | Verification | **Checks**: `metrics_has_verifier` |
| 8 | Visual QA | **Checks**: `screenshots_match_scenes` |

## File Requirements

When a stage specifies `files`, each path is checked relative to the project root. Paths ending in `/` (like `addons/gecs/`) are checked as directories.

## Programmatic Checks

When a stage specifies `checks`, each string names a validation function executed by the hook system. These checks inspect project state beyond simple file existence.

| Check | What it validates |
|---|---|
| `references_has_images` | The `references/` directory contains at least one image file (used as visual reference for asset generation) |
| `metrics_has_worker_done` | The metrics/progress tracking shows at least one worker task marked as done |
| `plan_has_non_pending` | `PLAN.md` contains at least one task that is not in `pending` status (work has started) |
| `metrics_has_new_worker_done` | New worker completions have been recorded since the last stage transition |
| `plan_no_pending` | `PLAN.md` has no remaining tasks in `pending` status (all tasks attempted) |
| `metrics_has_verifier` | At least one verifier subagent has run and recorded results |
| `screenshots_match_scenes` | Screenshots exist for the scenes defined in `SCENES.md`, confirming visual output |

## How Hooks Use This

Two hooks consume stage_schemas.json:

- **`stage_reminder.py`** -- Triggered on PreToolUse (Write/Edit) when writing to `.godotmaker/stage.json`. Validates that required outputs for the completed stage exist before allowing the stage advancement.
- **`check_stage_prerequisites.py`** -- Triggered on PreToolUse (Agent). Validates that outputs from already-completed stages exist before allowing subagent dispatch.
