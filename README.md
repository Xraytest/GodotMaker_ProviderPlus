# GodotMaker

[![License: BUSL 1.1](https://img.shields.io/badge/License-BUSL_1.1-orange.svg)](LICENSE)
[![Godot 4.x](https://img.shields.io/badge/Godot-4.x-blue?logo=godotengine)](https://godotengine.org)
[![CI](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml/badge.svg)](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml)

**English** | [中文](README.zh-CN.md)

**ECS-native text-to-game framework for Godot.**

GodotMaker turns natural-language game descriptions into playable Godot projects. It combines an AI orchestrator (Claude Code skills) with an Entity Component System ([gecs](https://github.com/csprance/gecs)) to generate GDScript code, scenes, and assets — all inside the Godot editor.

## Features

- **Text-to-Game Pipeline** — Describe a game concept; GodotMaker scaffolds the project, generates ECS components/systems, and wires up scenes.
- **ECS-First Architecture** — Built on gecs. Components hold pure data; Systems declare their queries. The scene tree stays reserved for UI/menus.
- **Scene-as-Spawner** — Scenes hold marker nodes (metadata only); the runtime converts them to ECS entities at load time.
- **Two-Layer Skill System** — Core skills (orchestrator, build, test, ECS, asset pipeline, e2e) and Reviewer skills (physics, animation, UI, audio, tilemap, navigation, shader, particles).
- **Hook-Enforced Pipeline** — Eight hooks gate the build pipeline: file permissions, stage prerequisites, report validation, completion checks. The orchestrator cannot skip stages or self-certify.
- **Automated Validation** — `godot --headless --quit` build, gdUnit4 unit tests, godot-e2e integration tests, screenshot-based visual checks.

## Requirements

| Dependency | Version |
|---|---|
| [Godot Engine](https://godotengine.org) | 4.x |
| [gecs](https://github.com/csprance/gecs) | latest |
| [gdUnit4](https://github.com/MikeSchulze/gdUnit4) | latest (v5.x for Godot 4.4, v6.x for 4.5+) |
| [Claude Code](https://claude.ai/code) | latest |
| Python | 3.10+ |
| .NET SDK | 8.0+ (optional, only for C# game projects) |

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker

# 2. Install Python dependencies
pip install -r tools/requirements.txt

# 3. Install git hooks (includes gitleaks secret scanning)
bash scripts/install-hooks.sh

# 4. Deploy GodotMaker skills into Claude Code
python tools/publish.py

# 5. Open a target Godot project and start using GodotMaker via Claude Code
```

## Project Structure

```
skills/
  core/         # orchestrator, godot-api, headless-build, gdunit-driver,
                # gdtoolkit, gecs, game-planner, project-scaffold,
                # visual-qa, screenshot, mcp-driver, godot-e2e
  reviewer/     # physics, animation, ui, tilemap, navigation, shader, audio, particles
  pattern/      # genre templates (planned)
shell/          # publish.sh / publish.ps1, _read_config.sh
tools/          # publish.py, check_env.py, asset_gen, rembg, check_project
templates/      # PLAN / STRUCTURE / ASSETS / MEMORY document templates
docs/           # getting-started.md, wiki/, reference/
```

## Architecture Overview

```
Natural Language Description
        |
        v
  Game Planner  ──>  Project Scaffold  ──>  ECS Code Generation
        |                                          |
        v                                          v
  Asset Generation                         Headless Build + Tests
        |                                          |
        v                                          v
  Scene Assembly  ──────────────────────>  E2E + Visual Checks
        |                                          |
        v                                          v
  Playable Godot Project  <──  MCP Debug (escalation path)
```

**Roadmap and design notes** live in [`ROADMAP.md`](ROADMAP.md) and the [wiki](docs/wiki/).

## Testing

GodotMaker uses [gdUnit4](https://github.com/MikeSchulze/gdUnit4) with a TDD approach.

```bash
# Run a single test file
godot --headless -s addons/gdunit4/bin/gdunit4_run.gd --single --file res://test/xxx.gd

# Run Python tool tests
pytest
```

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a PR.

## License

This project is licensed under the [Business Source License 1.1](LICENSE).
