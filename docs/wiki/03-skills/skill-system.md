# Skill System

GodotMaker organizes its capabilities into **skills** -- specialized knowledge modules that handle specific tasks during game generation.

## Three-Layer Architecture

### Layer 1 -- Core (13 active skills)

Core skills handle the end-to-end game creation pipeline: planning, scaffolding, code generation, build/test, visual verification, and runtime debugging. They are used directly by the orchestrator and its subagents during game construction.

| Function | Skills |
|---|---|
| Planning | game-planner |
| Scaffolding | project-scaffold |
| API Reference | godot-api, gecs |
| Build/Test | headless-build, gdunit-driver, godot-e2e, gdtoolkit |
| Visual | visual-qa, screenshot |
| Runtime | mcp-driver |
| Orchestration | orchestrator |
| Utility | input-mapper |

See [Core Skills Reference](core-skills.md) for details on each.

### Layer 2 -- Reviewer (8 skills)

Reviewer skills check your generated code for domain-specific pitfalls after implementation. See [Reviewer Skills](reviewer-skills.md) for the full list.

### Layer 3 -- Pattern (deferred)

Pattern skills will provide game-genre-specific templates and constraints (e.g., platformer physics tuning, tower defense wave scheduling). This layer is planned for Phase 5 and is currently empty.

See [Writing a Skill](../07-contributing/writing-a-skill.md) for a guide on creating new skills.

## See Also

- [Core Skills Reference](core-skills.md) -- detailed documentation for each core skill
- [Reviewer Skills Reference](reviewer-skills.md) -- the eight domain-specific reviewer skills
- [Writing a Skill](../07-contributing/writing-a-skill.md) -- guide to creating new skills
