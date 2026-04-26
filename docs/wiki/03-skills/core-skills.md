# Core Skills Reference

GodotMaker ships 13 core skills that handle the complete game creation pipeline. This page provides a quick reference for each.

## Planning

| Skill | Purpose |
|---|---|
| game-planner | Conducts a Socratic game design interview and produces a Game Design Document (GDD). Must run before any implementation begins. |

## Scaffolding

| Skill | Purpose |
|---|---|
| project-scaffold | Generates a new Godot project with ECS directory structure, project.godot, CLAUDE.md, gecs World setup, addon stubs, and template source files. |

## API Reference

| Skill | Purpose |
|---|---|
| godot-api | Looks up Godot engine class APIs (methods, properties, signals, enums) with version-specific docs. Runs as a forked Sonnet subagent. |
| gecs | ECS framework API reference for gecs (Entity, Component, System, World, QueryBuilder, Relationship, Observer, CommandBuffer). Provides accurate gecs API reference so generated ECS code uses correct API calls. |

## Build and Test

| Skill | Purpose |
|---|---|
| headless-build | Compile-checks a Godot project using headless mode. Fastest feedback loop for parse errors. |
| gdunit-driver | Runs gdUnit4 unit tests and parses results. Supports both GDScript and C# test files. |
| godot-e2e | Writes and runs end-to-end game tests using the godot-e2e framework. Python controls a live Godot game over TCP for input simulation and state assertions. |
| gdtoolkit | Lints and formats GDScript files using gdlint and gdformat. Standalone Python tool, does not require Godot. |

## Visual

| Skill | Purpose |
|---|---|
| visual-qa | Analyzes game screenshots for visual defects, compares against reference images, checks motion across frame sequences. Supports Claude native vision and Gemini Flash backends. |
| screenshot | Captures gameplay screenshots using godot-e2e viewport capture. Works headless, multi-monitor safe. |

## Runtime

| Skill | Purpose |
|---|---|
| mcp-driver | Runtime debugging and live project inspection via godot-mcp. Escalation path when headless tools cannot diagnose the problem (code compiles but behavior is wrong). |

## Orchestration

| Skill | Purpose |
|---|---|
| orchestrator | Lead agent that coordinates the full game creation pipeline: requirements, architecture, scaffolding, implementation, testing, and verification. Dispatches workers, verifiers, and reviewers. |

## Utility

| Skill | Purpose |
|---|---|
| input-mapper | Manages Godot input action mappings in project.godot. Adds, changes, or validates input actions based on GDD requirements. |

## Skill Invocation

Core skills are invoked in two ways:

1. **Automatic** -- GodotMaker selects the right skills for each task during game generation.
2. **Direct invocation** -- Advanced users can invoke specific skills through Claude Code for targeted tasks (e.g., running the linter or debugging a test failure).
