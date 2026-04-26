# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GodotMaker is an ECS-native text-to-game framework for Godot. It uses gecs (open-source ECS addon) with AI working in the GDScript layer. The project generates complete Godot game projects from natural language descriptions via a multi-agent pipeline.

## Repository Structure

```
hooks/              8 Python hook scripts + hooks/metrics/ subsystem
skills/
  core/             13 core skills (orchestrator is the most complex)
  reviewer/         8 reviewer skills (physics, animation, ui, etc.)
shell/              publish.sh / publish.ps1, report.sh / report.bat
tools/              publish.py, check_env.py, check_project.py, asset_gen.py, etc.
config/             settings.json, stage_schemas.json, addon_versions.json
templates/          PLAN/STRUCTURE/ASSETS/SCENES/MEMORY/GDD templates + game-claude.md
docs/               getting-started.md, hooks.md, wiki/, reference/
```

## Key Commands

```bash
# Run tests (193+ tests)
python -m pytest tests/ -x -q

# Publish to a game project
python tools/publish.py <target_dir>
python tools/publish.py --force <target_dir>

# Check environment
python tools/check_env.py
```

## How Publish Works

`publish.py` deploys skills, hooks, tools, config, and templates into a target game project:
- Skills → `.claude/skills/`
- Hooks → `.godotmaker/hooks/` (git-tracked, available in worktrees)
- Settings → `.claude/settings.json` (only on fresh install or `--force`)
- Version stamped in `.godotmaker/version`

## Skill System (Three Layers)

- **Layer 1 — Core** (13 skills): orchestrator, game-planner, project-scaffold, godot-api, gecs, input-mapper, headless-build, gdunit-driver, godot-e2e, gdtoolkit, visual-qa, screenshot, mcp-driver
- **Layer 2 — Reviewer** (8 skills): physics, animation, ui, tilemap, navigation, shader, audio, particles — each has SKILL.md + gotchas.md + checklist.md
- **Layer 3 — Pattern**: per game genre (deferred)

## Versioning

- `VERSION` file at repo root (semantic versioning: MAJOR.MINOR.PATCH)
- `CHANGELOG.md` tracks all changes
- Publish compares versions and prompts on MINOR/MAJOR upgrades

## Language

- All conversations, explanations, and communication with the user must be in Chinese
- Code, comments, and commit messages should be in English
