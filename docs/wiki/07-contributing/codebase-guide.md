# Codebase Guide

Source code orientation for contributors. This page describes how the repository is organized and where to find key entry points.

## Repository Layout

```
GodotMaker/
  hooks/                     8 hook scripts + metrics subsystem
    metrics/                 Metrics core (5 modules)
  skills/
    core/                    13 core skills
      orchestrator/          Main orchestrator (most complex: 15 files + 8 stage docs)
    reviewer/                8 reviewer skills
  tools/                     10 Python CLI tools
  config/                    4 configuration files
  templates/                 9 markdown templates
  shell/                     5 shell scripts
  tests/
    hooks/                   8 test files for hooks
    tools/                   5 test files for tools
  docs/                      Documentation
  VERSION                    Semantic version (currently 0.3.0)
  CHANGELOG.md               Release history
  pyproject.toml             Pytest configuration
```

## hooks/ -- Pipeline Enforcement

Eight Python scripts triggered by Claude Code events. Each reads JSON from stdin and writes a JSON decision to stdout.

| Script | Event | Purpose |
|---|---|---|
| `session_start.py` | SessionStart | Display version, initialize metrics session |
| `check_file_permissions.py` | PreToolUse (Write/Edit) | Block writes to protected files |
| `stage_reminder.py` | PreToolUse (Write/Edit) | Inject current stage context |
| `check_stage_prerequisites.py` | PreToolUse (Agent) | Validate stage prerequisites before spawning subagents |
| `check_asset_access.py` | PreToolUse (Read) | Gate access to asset files |
| `log_subagent.py` | SubagentStart/Stop | Record subagent lifecycle events |
| `check_worker_report.py` | SubagentStop | Validate worker/verifier/reviewer report format |
| `check_completion.py` | Stop | Enforce completion criteria before session end |

### hooks/metrics/

The metrics subsystem tracks session events for reporting.

| Module | Purpose |
|---|---|
| `__init__.py` | Package entry point, exports `record_event`, `get_current_stage` |
| `collector.py` | `record_event`, `read_events`, `start_session` |
| `schema.py` | `EventType` enum, role constants, report format definitions |
| `state.py` | Persistent state management (block counters, stage tracking) |
| `reporter.py` | HTML report generation from JSONL event logs |
| `highlights.py` | Session highlight extraction for reports |

## skills/core/ -- Core Skills

Thirteen skill directories, each containing at minimum a `SKILL.md` prompt file.

| Skill | Purpose |
|---|---|
| `orchestrator` | Lead agent coordination (15 files + `stages/` with 8 stage docs) |
| `game-planner` | Game design document generation |
| `project-scaffold` | Project directory and file scaffolding |
| `gecs` | ECS framework usage patterns |
| `godot-api` | Godot API reference and patterns |
| `headless-build` | Headless build and validation |
| `gdunit-driver` | Unit test execution |
| `gdtoolkit` | GDScript linting and formatting |
| `godot-e2e` | End-to-end testing framework |
| `visual-qa` | AI-powered screenshot analysis |
| `screenshot` | Screenshot capture utilities |
| `mcp-driver` | MCP server interaction |
| `input-mapper` | Input action mapping |

The **orchestrator** is the most complex skill. Its `stages/` subdirectory contains 8 stage documents:

```
stages/
  stage1_requirements.md
  stage2_architecture.md
  stage3_scaffold.md
  stage4_assets.md
  stage5_risk_impl.md
  stage6_main_impl.md
  stage7_integration.md
  stage8_final.md
```

Additional orchestrator files handle worker dispatch, verifier dispatch, reviewer dispatch, analyst dispatch, asset planning, visual QA, and more.

## skills/reviewer/ -- Domain Reviewers

Eight reviewer skills. Each follows the same structure: `SKILL.md` + `checklist.md` + `gotchas.md`.

| Skill | Domain |
|---|---|
| `physics` | Physics and collision |
| `animation` | Animation and tweens |
| `ui` | User interface |
| `tilemap` | Tilemap systems |
| `navigation` | Pathfinding and navigation |
| `shader` | Shader programs |
| `audio` | Audio and sound |
| `particles` | Particle systems |

These are post-implementation reviewers, not pre-implementation guides. The orchestrator dispatches them after a worker completes implementation.

## tools/ -- CLI Tools

Ten Python scripts for development and deployment tasks.

| Tool | Purpose |
|---|---|
| `publish.py` | Deploy GodotMaker into a target Godot project |
| `check_env.py` | Verify environment setup (Godot, addons, MCP) |
| `check_project.py` | Validate project completeness |
| `check_classname.py` | Detect classname conflicts with Godot built-ins |
| `asset_gen.py` | AI-powered asset generation |
| `rembg_matting.py` | Background removal from images |
| `grid_slice.py` | Sprite sheet slicing |
| `find_loop_frame.py` | Find loop points in animation frames |
| `tripo3d.py` | 3D model generation |
| `requirements.txt` | Python dependency list |

## config/ -- Configuration

| File | Purpose |
|---|---|
| `settings.json` | Hook registration (which hooks fire on which events) |
| `stage_schemas.json` | JSON schemas for stage validation |
| `config.yaml.default` | Default project configuration template |
| `addon_versions.json` | Godot version to addon version mappings |

## templates/ -- Document Templates

Nine markdown templates used when scaffolding a new game project:

`GDD.md`, `PLAN.md`, `STRUCTURE.md`, `ASSETS.md`, `SCENES.md`, `MEMORY.md`, `TOC.md`, `game-claude.md`, `memory_subsystem.md`

## shell/ -- Shell Scripts

| Script | Purpose |
|---|---|
| `publish.sh` | Unix publish wrapper |
| `publish.ps1` | Windows publish wrapper |
| `report.sh` | Unix metrics report generator |
| `report.bat` | Windows metrics report generator |
| `_read_config.sh` | Config file reader helper (also deployed to skills/) |

## tests/ -- Test Suite

### tests/hooks/ (8 test files)

| File | Tests |
|---|---|
| `test_check_completion.py` | Completion criteria enforcement |
| `test_check_file_permissions.py` | File permission checks |
| `test_check_stage_prerequisites.py` | Stage prerequisite validation |
| `test_check_worker_report.py` | Worker/verifier/reviewer report validation |
| `test_metrics.py` | Metrics collection and reporting |
| `test_session_start.py` | Session initialization |
| `test_stage_reminder.py` | Stage reminder injection |
| `helpers.py` | Shared test utilities (`run_hook`, `is_blocked`, etc.) |

### tests/tools/ (5 test files)

| File | Tests |
|---|---|
| `test_publish.py` | Publish deployment logic |
| `test_check_env.py` | Environment validation |
| `test_check_project.py` | Project completeness checks |
| `test_check_classname.py` | Classname conflict detection |
| `test_addon_versions.py` | Addon version mapping validation |

## Key Entry Points

If you are new to the codebase, start with these files:

1. **`tools/publish.py`** -- The deployment script. Reading it reveals what gets copied where and how versioning works.
2. **`hooks/metrics/__init__.py`** -- The metrics package entry point. Shows how hooks record events and track pipeline state.
3. **`skills/core/orchestrator/SKILL.md`** -- The orchestrator prompt. This is the "brain" of the system -- it defines how the lead agent coordinates workers, verifiers, and reviewers.
4. **`config/settings.json`** -- Hook registration. Shows which hooks fire on which Claude Code events.
5. **`tests/hooks/helpers.py`** -- Test infrastructure. Understanding `run_hook` and `is_blocked` is essential for writing hook tests.
