# Memory: {Project Name}

## System Index

<!-- Each implemented system/module has a detail file in the memory/ subdirectory
     (same folder as this MEMORY.md). Use the template from .claude/templates/memory_subsystem.md.
     One line per entry: link + one-line summary. -->

<!-- Example entries (delete when starting):
- [movement_system](memory/movement_system.md) — PlayerMovementSystem: exponential deceleration, raycast ground detection
- [collision](memory/collision.md) — CollisionSystem: layer/mask setup, Area2D vs CharacterBody2D tradeoff
- [asset_gen](memory/asset_gen.md) — Asset generation: Gemini prompt patterns, background removal issues
-->

## Discoveries

<!-- Things learned during development that weren't obvious from docs. -->

- {date}: {discovery}

## What Worked

<!-- Approaches and patterns that succeeded. Reference for similar future tasks. -->

- {approach}: {why it worked}

## What Failed

<!-- Approaches attempted and abandoned. Avoid repeating these. -->

- {approach}: {why it failed, what replaced it}

## Engine Quirks

<!-- Godot-specific gotchas encountered during this project. -->

- {quirk}: {workaround}

## Workarounds

<!-- Temporary or permanent workarounds for issues that don't have clean fixes. -->

- {issue}: {workaround applied}

## Component Design Decisions

<!-- Rationale for component structure choices.
     Why fields were grouped this way, why components were split or merged. -->

- **{ComponentName}**: {decision and rationale}

## System Interaction Patterns

<!-- Patterns discovered for how systems communicate through components.
     Intent components, event components, state machine transitions, etc. -->

- **{Pattern name}**: {description}

## DAG Ordering Issues

<!-- Problems encountered with system scheduling and dependency ordering. -->

- **{Issue}**: {what happened, how it was resolved}
