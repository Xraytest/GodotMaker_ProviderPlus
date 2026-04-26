# CLAUDE.md

Generated Godot game project. The `/gm-*` skills drive the build pipeline — invoke them rather than recreating their flow manually.

## Don't get caught here

### Pipeline

- **Don't bypass the role lock.** `.godotmaker/current_role` decides who may write what. If a hook denies a write, dispatch the right subagent or switch to the right `/gm-*` skill — don't try to `--force` past it.
- **Don't write `e2e/` outside the Evaluator role.** Workers expose `simulate_*()` interfaces and write unit tests for them. Only the Evaluator (`/gm-evaluate`) writes the e2e tests.
- **Don't manually edit `.godotmaker/stage.json`.** Each `/gm-*` skill appends its own role timestamp on completion.
- **Read `MEMORY.md` before dispatching a worker.** Past mistakes are indexed there — workers will repeat them otherwise.

### Resources

- Never fabricate resource paths. Use only paths listed in `ASSETS.md` or verified to exist. If you need an asset that does not exist, report it — do not invent.

## Where to look

| Question | File |
|---|---|
| Game spec | `GDD.md` |
| Task list / progress | `PLAN.md` |
| Systems / Components / Archetypes | `STRUCTURE.md` |
| Scene layouts | `SCENES.md` |
| Past discoveries + gotchas | `MEMORY.md` (index) |
| Each role's full contract | `.claude/skills/gm-*/SKILL.md` |
| ECS API + the full gotcha list | `.claude/skills/gecs/` |
| godot-e2e API | `.claude/skills/godot-e2e/SKILL.md` |

## Conventions

- GDScript for all game logic; English for code and comments
- TDD: write tests alongside implementation
- One System per file (`{name}_system.gd`), one Component per file (`{name}.gd`)
- Tests in `test/`, named `test_{name}.gd`
- Physics callbacks must never manipulate the node tree directly — use deferred calls
- Only one System writes Transform per entity
- Scene tree is for UI/menus only; gameplay entities use ECS
- All systems must have corresponding unit tests
- Game must pass e2e tests before considered complete
