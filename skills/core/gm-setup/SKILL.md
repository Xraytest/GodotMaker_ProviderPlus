---
name: gm-setup
description: |
  Set up a new game project: requirements, architecture, scaffold, and assets.
  Explicit invocation only — use /gm-setup.
disable-model-invocation: true
---

# GodotMaker Setup

$ARGUMENTS

You are setting up a new Godot game project from a natural language description. This covers the full setup pipeline: requirements gathering, ECS architecture design, project scaffolding, and asset collection.

## Session Setup

**FIRST ACTION — before anything else:** Write `setup` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`. Build the set of completed roles from these events.

- If `setup` has already completed AND all required files exist (GDD.md, PLAN.md, STRUCTURE.md, ASSETS.md, SCENES.md, TOC.md) → STOP. Tell the user:
  > "Role 'setup' was already completed at {timestamp}. Recommended next: /gm-build.
  > If you need to redo this step or have other plans, just tell me."
- If `setup` has already completed but some files are missing → previous run was incomplete, resume from the missing piece.
- Otherwise → fresh start from the first incomplete stage in this skill.

## Pipeline

Execute these stages in order. Each stage has a gate — you cannot proceed until it passes.

| # | Stage | Detail File | Gate |
|---|-------|-------------|------|
| 1 | Requirements & Game Design | `.claude/skills/orchestrator/stages/stage1_requirements.md` | GDD.md + PLAN.md + ASSETS.md + SCENES.md + TOC.md exist |
| 2 | Architecture | `.claude/skills/orchestrator/stages/stage2_architecture.md` | STRUCTURE.md with Components + Systems |
| 3 | Scaffold | `.claude/skills/orchestrator/stages/stage3_scaffold.md` | Compilable project with addons |
| 4 | Assets | `.claude/skills/orchestrator/stages/stage4_assets.md` | Reference images + asset manifest |

**Read each stage's detail file BEFORE starting that stage.** Do not rely on memory.

## Hard Rules

1. **You CANNOT write .gd/.tscn/.tres directly.** Scaffold uses a Worker subagent.
2. **Workers CANNOT modify PLAN.md/STRUCTURE.md/ASSETS.md.**
3. **Use AskUserQuestion for confirmations.** GDD must be confirmed by the user before proceeding.
4. **MUST NOT skip stages.** Fix issues first; report to user after 3 attempts.

## Skills Reference

| Skill | Purpose |
|-------|---------|
| game-planner | Socratic interview → GDD generation |
| project-scaffold | Project structure generation |
| gecs | ECS framework API + patterns |
| godot-api | Godot API reference |

## When Done

After Stage 4 gate passes:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "setup", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `Setup complete. Recommended next: /gm-build`
