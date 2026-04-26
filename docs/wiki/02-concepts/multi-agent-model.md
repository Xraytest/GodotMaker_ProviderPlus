# How Work Is Assigned

When you describe a game to GodotMaker, you are not talking to a single AI. Behind the scenes, a team of specialized agents divides the work, implements it in parallel, and verifies the result — all without any manual coordination from you.

## The Four Roles

**Orchestrator** — Plans and coordinates everything. It reads your description, asks clarifying questions if needed, designs the overall game architecture, and decides how to split the work. The orchestrator never writes game code directly; its job is to keep the big picture coherent.

**Workers** — Write the actual game code. Each worker is given a focused brief: one system, one scene, or one UI component. Workers implement the feature, write unit tests for it, and report what they produced.

**Verifiers** — Independently check what workers built. A verifier runs the build, executes tests, and confirms the feature actually works end-to-end. Verification is separate from implementation so that errors are caught by a fresh pair of eyes.

**Reviewers** — Audit code for domain-specific issues. GodotMaker includes specialist reviewers for physics, animation, UI, tilemaps, navigation, shaders, audio, and particles. The right reviewer is matched to the right feature automatically.

## How a Task Flows

1. You describe your game in natural language.
2. The orchestrator breaks the description into an architecture plan and a list of tasks.
3. Workers pick up their assigned tasks and implement them concurrently.
4. Each worker's output is handed to a verifier, which runs builds and tests.
5. Domain reviewers audit the implementation for common pitfalls.
6. The orchestrator integrates the results and moves to the next stage.

This cycle repeats for each stage of the pipeline: planning, scaffolding, assets, scenes, and polish.

## Parallelism

Workers run in parallel where tasks are independent. If your game has a movement system, an inventory system, and a UI layer, those can be built at the same time rather than one after another. This keeps generation fast even for larger projects.

## What You Need to Do

Nothing, beyond describing your game. You do not assign roles, write briefs, or trigger verifications. The orchestrator handles all of that. If a stage needs your input — for example, to confirm the game design before implementation begins — it will ask.
