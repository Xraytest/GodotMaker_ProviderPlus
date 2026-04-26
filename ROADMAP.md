# Roadmap

> Turn natural-language game descriptions into playable Godot projects, powered by ECS and AI orchestration.

This roadmap tracks what has shipped, what we are working on now, and where the project is headed.

## Completed

### v0.1 — Foundation

- [x] `R-001` Project skeleton and repository setup
- [x] `R-002` Asset pipeline tools (asset_gen, rembg, sprite utilities)
- [x] `R-003` Skill infrastructure and publish pipeline

### v0.2 — Skills

- [x] `R-010` 13 core skills (orchestrator, godot-api, headless-build, gdunit-driver, gdtoolkit, gecs, game-planner, project-scaffold, visual-qa, screenshot, mcp-driver, godot-e2e, input-mapper)
- [x] `R-011` 8 reviewer skills (physics, animation, ui, tilemap, navigation, shader, audio, particles)
- [x] `R-012` Capability skills (headless-build, gdunit-driver, godot-e2e, gdtoolkit, visual-qa)

### v0.3 — Pipeline

- [x] `R-020` Multi-agent orchestrator pipeline (game-planner → scaffold → generate → validate)
- [x] `R-021` Stage gate validation with schema enforcement
- [x] `R-022` Hook system (8 hooks: pre-commit, SubagentStop, worktree lifecycle, etc.)
- [x] `R-023` Metrics and state tracking subsystem

### v0.4 — Polish

- [x] `R-030` Semantic versioning with publish-time upgrade prompts
- [x] `R-031` Hooks migration to `.godotmaker/` (git-tracked, worktree-safe)
- [x] `R-032` Wiki documentation (30 pages)
- [x] `R-033` CI workflow (lint, test, gitleaks)

## In Progress

### v0.5 — Plugin Skills

- [ ] `R-050` [Phantom Camera](https://github.com/ramokz/phantom-camera) — Camera management (inspired by Cinemachine)
- [ ] `R-051` [Dialogic](https://github.com/dialogic-godot/dialogic) — Dialogue and visual novel system
- [ ] `R-052` [Input Helper](https://github.com/nathanhoad/godot_input_helper) — Input device detection and icon mapping
- [ ] `R-053` [Scene Manager](https://github.com/maktoobgar/scene_manager) — Scene transitions and organization
- [ ] `R-054` [Godot State Charts](https://github.com/derkork/godot-statecharts) — Hierarchical state machines
- [ ] `R-055` [Godot Sound Manager](https://github.com/nathanhoad/godot_sound_manager) — Music and SFX playback
- [ ] `R-056` [GodotSteam](https://github.com/GodotSteam/GodotSteam) — Steam platform integration
- [ ] `R-057` [Beehave](https://github.com/bitbrain/beehave) — Behavior tree AI
- [ ] `R-058` [Importality](https://github.com/nklbdev/godot-4-importality) — Universal raster graphics and animation importer
- [ ] `R-059` [Spine Runtime](https://github.com/EsotericSoftware/spine-runtimes) — 2D skeletal animation (commercial license)
- [ ] `R-060` [gdfxr](https://github.com/timothyqiu/gdfxr) — Retro sound effect generator (sfxr port)

## Future / Exploring

### Permission & Pipeline

- `R-070` **Permission isolation upgrade** — Current e2e/ permission isolation uses a file lock (`.godotmaker/current_role`). Explore stronger mechanisms: agent-type-based identity (GSD-style skill→agent dispatch), or harness-injected env vars. Goal: tamper-proof role separation without extra subagent nesting.
- `R-071` **Pipeline decomposition** — Split monolithic orchestrator skill into independent orchestrator + evaluator roles with dedicated skills and agent definitions. Evaluator owns e2e/ exclusively, orchestrator owns planning + worker dispatch.

### Framework Features

Items below are ideas under consideration — not committed to a timeline.

- `R-100` **TileMap support** — Terrain systems, tileset asset generation, and TileMap-based level design. Currently deferred; sprite-placement is the recommended terrain approach until this ships.
- `R-101` **ECS framework migration** — Migrate tindercore (C++ GDExtension) from EnTT to flecs, then adopt tindercore as the ECS runtime replacing gecs.
- `R-102` **Scene-markers skill** — Marker type → component composition mapping for ECS entity spawning.
- `R-103` **System DAG checker CLI** — Static dependency analysis for ECS systems at build time.
- `R-104` **gdUnit ECS test templates** — Reusable test fixtures for ECS system testing.
- `R-105` **DestructionSystem and Node lifecycle** — Entity destruction protocol and component add/remove lifecycle.
- `R-106` **Multi-platform game publishing** — One-click export and publish to Steam, iOS, Google Play, Web. Includes export preset generation, platform-specific assets, store metadata templates, and CI/CD integration.
- `R-107` **Pattern skills** — Per-genre architecture templates (e.g., top-down shooter, platformer, tower defense). Built from real pipeline runs, not theoretical.
- `R-108` **Tester subagent** — Dedicated E2E and gameplay testing role in the multi-agent pipeline.
- `R-109` **GDD quality review** — Automated completeness and consistency checks on generated Game Design Documents.
- `R-110` **Android build workflow** — APK/AAB export with signing, versioning, and store-ready packaging.
- `R-111` **Sprite sheet animation pipeline** — Generate multi-frame sprite sheets from single-frame AI-generated sprites.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved. Feature proposals are welcome as [GitHub Issues](https://github.com/RandallLiuXin/GodotMaker/issues).
