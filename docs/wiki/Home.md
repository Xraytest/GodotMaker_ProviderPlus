# GodotMaker Wiki

GodotMaker lets you describe a game in plain language and get back a complete, playable Godot project — with ECS architecture, unit tests, and visual QA baked in. You write what you want; a multi-agent pipeline figures out the rest.

## What You Can Do

| Capability | What It Means for You |
|------------|----------------------|
| **Describe, don't configure** | Write a plain-language game brief; GodotMaker plans, scaffolds, and codes it for you |
| **Get tested code by default** | Unit tests (gdUnit4) and end-to-end tests are generated alongside game code, not added later |
| **Catch Godot-specific bugs early** | Eight domain reviewers (physics, animation, UI, tilemap, navigation, shader, audio, particles) flag common Godot pitfalls before you see the build |
| **Visual quality checks included** | Automated screenshots and AI-based visual assessment confirm the game looks right, not just compiles |
| **Consistent ECS structure** | All generated game logic follows Entity-Component-System via gecs — no spaghetti node scripts |

## Wiki Sections

| Section | Contents |
|---------|----------|
| [Installation](01-getting-started/installation.md) | Prerequisites, API keys, environment setup |
| [First Game](01-getting-started/first-game.md) | End-to-end walkthrough of generating your first game |
| [Project Layout](01-getting-started/project-layout.md) | Structure of a generated game project |
| [Concepts](02-concepts/architecture-overview.md) | ECS architecture, Scene-as-Spawner, skill layers, pipeline stages |
|   | [Architecture Overview](02-concepts/architecture-overview.md) -- [ECS Design](02-concepts/ecs-design.md) -- [Orchestrator Pipeline](02-concepts/orchestrator-pipeline.md) -- [Multi-Agent Model](02-concepts/multi-agent-model.md) |
| [Skills Reference](03-skills/skill-system.md) | Core skills and reviewer skills |
|   | [Skill System](03-skills/skill-system.md) -- [Core Skills](03-skills/core-skills.md) -- [Reviewer Skills](03-skills/reviewer-skills.md) |
| [Tools](05-tools/publish.md) | Asset pipeline, environment checker, project validator |
|   | [Publish](05-tools/publish.md) -- [Check Env](05-tools/check-env.md) -- [Check Project](05-tools/check-project.md) -- [Asset Tools](05-tools/asset-tools.md) |
| [Configuration](06-configuration/godotmaker-yaml.md) | godotmaker.yaml, config.yaml, settings.json, addon versions |
|   | [godotmaker.yaml](06-configuration/godotmaker-yaml.md) -- [Project Config](06-configuration/project-config.md) -- [Addon Versions](06-configuration/addon-versions.md) |
| [Contributing](07-contributing/development-setup.md) | How to contribute skills, tools, hooks, and documentation |
|   | [Development Setup](07-contributing/development-setup.md) -- [Codebase Guide](07-contributing/codebase-guide.md) -- [Testing](07-contributing/testing.md) -- [Release Process](07-contributing/release-process.md) -- [Hook System](07-contributing/hook-system.md) -- [Hook Reference](07-contributing/hook-reference.md) -- [Metrics and State](07-contributing/metrics-and-state.md) -- [Writing a Skill](07-contributing/writing-a-skill.md) -- [Stage Schemas](07-contributing/stage-schemas.md) |
| [API Reference](08-reference/glossary.md) | Glossary, FAQ, and changelog |
|   | [Glossary](08-reference/glossary.md) -- [FAQ](08-reference/faq.md) -- [Changelog](08-reference/changelog.md) |

## Current Status

The core pipeline (skills, hooks, orchestrator, verification chain) is complete. Current focus is plugin skills for popular Godot addons. See the [CHANGELOG](https://github.com/RandallLiuXin/GodotMaker/blob/main/CHANGELOG.md) for the latest release and [ROADMAP.md](https://github.com/RandallLiuXin/GodotMaker/blob/main/ROADMAP.md) for the full plan.

## Quick Links

- [GodotMaker Repository](https://github.com/RandallLiuXin/GodotMaker)
- [gecs -- ECS Framework](https://github.com/csprance/gecs)
- [gdUnit4 -- Testing Framework](https://github.com/MikeSchulze/gdUnit4)
- [godot-mcp -- Runtime Debugging](https://github.com/Coding-Solo/godot-mcp)
