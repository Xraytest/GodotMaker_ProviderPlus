---
name: gm-scaffold
description: |
  Scaffold a new Godot project: project.godot + addons + base directories +
  e2e/conftest.py + initial git commit. Lifetime-once role — runs only on
  fresh projects.
  Explicit invocation only — use /gm-scaffold.
disable-model-invocation: true
---

# GodotMaker Scaffold

$ARGUMENTS

You are scaffolding a brand-new Godot project. This is the **lifetime-once** foundation step: project.godot + addons + base directory layout + e2e/conftest.py + initial git commit. No game design happens here — that comes in `/gm-gdd`.

## Session Setup

**FIRST ACTION — before anything else:** Write `scaffold` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`. Find the **last event** in the file.

Scaffold is **lifetime-once** — its event gets archived after each milestone's finalize. So determine "already scaffolded" from project artifacts on disk, not the event log:

- If `project.godot` exists AND `addons/gecs/` exists AND `git log` has at least one commit → STOP. Tell the user:
  > "Project is already scaffolded. Recommended next: /gm-gdd.
  > If you need to re-scaffold (rare — usually addon migrations are handled by `tools/publish.py`), just tell me."
- Otherwise → proceed.

## Hard Rules

1. **Do NOT design the game here.** Game design is `/gm-gdd`'s job. Scaffold creates an empty, generic project. Non-gameplay project settings (resolution, rendering method, viewport defaults) are config choices scaffold may make — those are not game design.
2. **Do NOT create Component/System stubs.** STRUCTURE.md doesn't exist yet, so there's nothing to derive from. Workers in `/gm-build` create code files on demand.
3. **All addons MUST come from `.claude/config/addon_versions.json`** — do not guess versions.
4. **Initial git commit is mandatory.** Worker worktree isolation in `/gm-build` requires `HEAD` to resolve.

## Scaffold Steps

### 1. Gather minimal inputs

Use `AskUserQuestion` to ask for:
- **Game name** (snake_case, used as project directory name)
- **Perspective** (`2D` | `3D`) — defaults to `2D` if user is unsure

Other settings (genre, art style, mechanics) are deferred to `/gm-gdd`.

### 2. Run project-scaffold skill

Invoke `.claude/skills/project-scaffold/SKILL.md` with the gathered inputs.

The scaffold MUST produce:
- `project.godot` — generic 2D or 3D project, default viewport, default rendering method
- `addons/gecs/`, `addons/gdunit4/`, `addons/godot-e2e/` — versions from `.claude/config/addon_versions.json`
- godot-e2e enabled in `[editor_plugins]`
- Empty `Main` scene (placeholder — actual scenes come during build)
- `e2e/conftest.py` (template below)
- Base directories: `src/`, `scenes/`, `assets/`, `references/`
- `.godotmaker/config.yaml` (created by publish script — verify exists)

### E2E conftest.py template

Write the following to `e2e/conftest.py`:
```python
import pytest
import os
from godot_e2e import GodotE2E

GODOT_PROJECT = os.path.join(os.path.dirname(__file__), "..")

@pytest.fixture(scope="module")
def _game_process():
    with GodotE2E.launch(GODOT_PROJECT, timeout=15.0) as game:
        game.wait_for_node("/root/Main", timeout=10.0)
        yield game

@pytest.fixture(scope="function")
def game(_game_process):
    _game_process.reload_scene()
    _game_process.wait_for_node("/root/Main", timeout=5.0)
    yield _game_process
```

### 3. Initial commit

```bash
git init   # if not already a git repo
git add -A
git commit -m "Scaffold: initial Godot project with addons"
```

Required for `isolation: "worktree"` in worker dispatch — without `HEAD`, parallel workers fail with `fatal: not a valid object name: 'HEAD'`.

### 4. Verify

Run `python tools/check_project.py <project_dir> --build` and paste the output. Required:
- `project.godot` exists
- `addons/gecs/`, `addons/gdunit4/` present
- godot-e2e plugin enabled
- `godot --headless --quit` produces zero ERROR lines
- `e2e/conftest.py` exists with `GodotE2E` import
- `.git/` exists with at least one commit

## Available Skills & Tools

| Skill | Purpose |
|-------|---------|
| project-scaffold | Project structure + addon installation |
| godot-api | Godot API reference (sanity-check project.godot syntax) |

## When Done

After verification passes:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "scaffold", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `Scaffold complete. Recommended next: /gm-gdd`
