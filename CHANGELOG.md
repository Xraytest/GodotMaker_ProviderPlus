# Changelog

All notable changes to GodotMaker will be documented in this file.

Format: [Semantic Versioning](https://semver.org/) — MAJOR.MINOR.PATCH

## [0.1.0] — 2026-04-26

Initial public release.

- 8-stage orchestrator pipeline with hook-enforced gates (requirements → architecture → scaffold → assets → risk impl → main impl → integration → final)
- Worker / verifier / reviewer / analyst subagent dispatch with format-validated reports
- 13 core skills (orchestrator, godot-api, headless-build, gdunit-driver, gdtoolkit, gecs, game-planner, project-scaffold, visual-qa, screenshot, mcp-driver, godot-e2e, input-mapper) and 8 reviewer skills (physics, animation, ui, tilemap, navigation, shader, audio, particles)
- 8 hooks: file permission enforcement, stage prerequisite gating, completion checks, subagent report validation, session bookkeeping, anti-deadloop protection, worktree-aware file resolution
- `tools/publish.py` deploys the framework into a target Godot project, with version tracking and upgrade prompts
- Static checks: `check_project.py` for project completeness, `check_classname.py` for Godot built-in collisions
- Asset pipeline helpers (`asset_gen.py`, `rembg_matting.py`, `tripo3d.py`)
- Wiki documentation (30 pages across 8 sections)
- 193+ unit tests for hooks and tools
