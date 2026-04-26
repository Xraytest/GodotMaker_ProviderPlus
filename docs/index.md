# GodotMaker

**ECS-native text-to-game framework for Godot.**

GodotMaker turns natural-language game descriptions into playable Godot projects. It combines an AI orchestrator (Claude Code skills) with an Entity Component System ([gecs](https://github.com/csprance/gecs)) to generate GDScript code, scenes, and assets — all inside the Godot editor.

## Features

- **Text-to-Game Pipeline** — Describe a game concept; GodotMaker scaffolds the project, generates ECS components/systems, and wires up scenes.
- **ECS-First Architecture** — Built on gecs. Systems declare read/write dependencies; a static DAG checker prevents conflicts at build time.
- **Scene-as-Spawner** — Scenes hold marker nodes (metadata only); the runtime converts them to ECS entities. The scene tree stays reserved for UI/menus.
- **Three-Layer Skill System** — Core skills (build, test, orchestrate), Reviewer skills (physics, animation, UI, audio, ...), and Pattern skills (genre templates).
- **Automated Validation** — `dotnet build` > DAG check > gdUnit4 tests > headless run > Visual QA > MCP escalation.

## Quick Links

- [Installation](wiki/01-getting-started/installation.md)
- [First Game](wiki/01-getting-started/first-game.md)
- [Architecture Overview](wiki/02-concepts/architecture-overview.md)
- [Contributing](wiki/07-contributing/development-setup.md)
- [FAQ](wiki/08-reference/faq.md)
