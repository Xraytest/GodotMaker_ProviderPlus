# Glossary

Terms and concepts used throughout the GodotMaker project.

## Architecture

| Term | Definition |
|---|---|
| **ECS** | Entity Component System -- an architecture where entities are numeric IDs, components are plain data containers, and systems are stateless logic that operates on entities matching specific component queries. Decouples data from behavior. |
| **gecs** | Open-source Godot ECS addon ([github.com/csprance/gecs](https://github.com/csprance/gecs)). Provides the Entity, Component, and System base classes that GodotMaker builds on. |
| **Scene-as-Spawner** | Design pattern where Godot scenes define entity templates via marker nodes (metadata only). At runtime, the framework converts markers into ECS entities. The scene tree itself is reserved for UI and menus. |
| **DAG** | Directed Acyclic Graph -- used for system dependency checking. Each system declares which components it reads and writes. A static DAG checker verifies that no two systems write to the same component on the same entity, preventing circular dependencies. |

## Testing and Validation

| Term | Definition |
|---|---|
| **gdUnit4** | Godot unit testing framework ([github.com/MikeSchulze/gdUnit4](https://github.com/MikeSchulze/gdUnit4)). Used for TDD-style testing of ECS systems and components. |
| **godot-e2e** | End-to-end testing framework for Godot ([github.com/RandallLiuXin/godot-e2e](https://github.com/RandallLiuXin/godot-e2e)). Provides out-of-process Python control over a running Godot instance for integration and acceptance tests. |
| **VQA** | Visual Question Answering -- AI-powered screenshot analysis that verifies visual correctness of rendered output. Uses Gemini Flash or Claude to answer questions like "Is the player sprite visible?" against captured screenshots. |
| **MCP** | Model Context Protocol -- a runtime debugging bridge between Claude and Godot. Implemented via the `godot-mcp` npm package (`@coding-solo/godot-mcp`). Provides capabilities to run the project, capture debug output, inspect scene state, and manage the project from outside the editor. |

## Pipeline Roles

| Term | Definition |
|---|---|
| **Orchestrator** | The lead Opus agent that coordinates the entire pipeline. It plans the implementation, dispatches workers, verifiers, and reviewers, tracks stage progression, and enforces quality gates. Defined in `skills/core/orchestrator/SKILL.md`. |
| **Worker** | A Sonnet subagent that implements one system, feature, or component. Workers operate in isolated git worktrees to enable parallel development. Their output is validated by the `check_worker_report` hook. |
| **Verifier** | A Sonnet subagent that runs integration tests and adversarial probes against a worker's implementation. Verifiers check for edge cases, error handling, and correctness beyond what unit tests cover. |
| **Reviewer** | A Sonnet subagent that performs domain-specific code review using one of the 8 reviewer skills (physics, animation, UI, etc.). Reviewers check for Godot-specific pitfalls documented in `gotchas.md` and verify compliance with `checklist.md`. |
| **Analyst** | A Sonnet subagent that inspects assets and reference images. Used during asset planning and visual QA stages to evaluate whether generated assets match the game design requirements. |

## Pipeline Concepts

| Term | Definition |
|---|---|
| **Hook** | A Python script triggered by Claude Code lifecycle events (SessionStart, PreToolUse, SubagentStart, SubagentStop, Stop). Hooks enforce pipeline rules by returning allow/block decisions as JSON. See `config/settings.json` for the hook registration map. |
| **Stage** | One of 8 sequential pipeline phases that the orchestrator progresses through. Each stage has prerequisites, deliverables, and validation criteria. The stages are: (1) Requirements, (2) Architecture, (3) Scaffold, (4) Assets, (5) Risk Implementation, (6) Main Implementation, (7) Integration, (8) Final. |
| **Worktree** | A git worktree created for each parallel worker subagent, providing filesystem isolation so multiple workers can modify files simultaneously without conflicts. Requires at least one commit in the repository (which is why `publish.py` creates an initial commit). |

## Tools and Infra

| Term | Definition |
|---|---|
| **publish.py** | The deployment script that copies GodotMaker skills, hooks, tools, config, and templates into a target Godot project directory. Handles versioned upgrades with semantic version comparison. |
| **Metrics** | The event tracking subsystem in `hooks/metrics/`. Records hook decisions, subagent lifecycle events, and pipeline progression to `.godotmaker/metrics_current.jsonl`. Used for HTML report generation and session analysis. |
