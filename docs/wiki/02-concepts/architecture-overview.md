# How GodotMaker Works

GodotMaker turns a natural language game description into a playable Godot project. You describe what you want; GodotMaker plans, builds, tests, and hands you a working game.

## The Basic Flow

```
You describe a game idea
        |
        v
GodotMaker runs an 8-stage pipeline
        |
        v
You receive a complete, tested Godot project
```

The pipeline is driven by an orchestrator agent. It coordinates specialized sub-agents — writers, verifiers, and reviewers — each responsible for a distinct part of the job. See [How Work Is Assigned](multi-agent-model.md) for details on each role. Skills supply the know-how for each task; hooks enforce quality rules throughout.

## The 8 Stages

The pipeline moves through three broad phases: design (Stages 1-2), build (Stages 3-6), and verification (Stages 7-8). Each stage must pass a gate — a set of output checks — before the next stage begins. Stages cannot be skipped or reordered. Once the gate passes, progress is recorded and the orchestrator moves forward automatically.

For a detailed breakdown of each stage, see [Orchestrator Pipeline](orchestrator-pipeline.md).

## What Keeps Quality High

**Skills** are the knowledge packages that power each stage. Core skills handle building, testing, linting, and API lookups. Reviewer skills carry domain-specific checklists and known pitfalls for Godot subsystems like physics, shaders, and navigation. You do not invoke skills directly — the orchestrator selects and uses them automatically.

**Hooks** run silently in the background at each stage boundary. They block the pipeline from advancing until each stage passes quality checks. If a check fails, the orchestrator must resolve the issue before continuing.

## What You Do

Your active involvement is concentrated at Stage 1. After the interview, the pipeline runs largely unattended. You can monitor progress through the session log. When the pipeline finishes, you get a project directory ready to open in Godot.

If anything goes wrong mid-pipeline, the orchestrator retries or asks for your input before stopping. You are never left with a silently broken project.
