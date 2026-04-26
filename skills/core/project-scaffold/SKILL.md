---
name: project-scaffold
description: |
  Generate a new Godot game project with standardized ECS structure and tooling.
  Use when starting a new game: "create a project", "set up a new game",
  "scaffold", "initialize", "new project", "start building", "let's make it".
  Triggers after game-planner produces a confirmed plan, or when the user
  provides a game name + genre directly. Even for simple requests like
  "make me a new Godot project", use this skill to ensure proper ECS structure.
  Creates directory structure, project.godot, CLAUDE.md, gecs World setup,
  addon stubs, and template source files based on the game plan or user input.
---

# Project Scaffold

$ARGUMENTS

Generate a new Godot game project with GodotMaker's ECS architecture.
Read templates from this skill's `templates/` directory, fill `{{placeholders}}`
with values from the game plan or user input, and write results to the target.

## Step 1 — Gather Variables

If a confirmed Game Plan exists in the conversation (from game-planner), extract
variables from it. Otherwise, ask the user for **game name** and **genre** at
minimum — use genre defaults for everything else.

| Variable | Source | Default |
|----------|--------|---------|
| `{{game_name}}` | user input, snake_case, used as directory name | *required* |
| `{{game_title}}` | user input or Title Case of game_name | *required* |
| `{{genre}}` | Game Plan "Genre" or user | `"platformer"` |
| `{{perspective}}` | Game Plan "Perspective" or genre default | `"2D"` |
| `{{viewport_width}}` | genre defaults table | `1280` |
| `{{viewport_height}}` | genre defaults table | `720` |
| `{{rendering_method}}` | perspective | `"gl_compatibility"` (2D) / `"forward_plus"` (3D) |
| `{{root_node_type}}` | perspective | `"Node2D"` (2D) / `"Node3D"` (3D) |
| `{{camera_type}}` | perspective | `"Camera2D"` (2D) / `"Camera3D"` (3D) |
| `{{game_description}}` | Game Plan summary or one-line from user | genre name + " game" |

**Genre defaults:**

| Genre | Viewport | Gravity | Input Actions |
|-------|----------|---------|---------------|
| Platformer | 1280x720 | 980.0 | move_left, move_right, jump |
| Top-down | 1280x720 | none | move_up, move_down, move_left, move_right |
| Puzzle | 1280x720 | none | select, confirm, cancel |
| Endless runner | 720x1280 | 980.0 | jump |
| 3D game | 1280x720 | 9.8 | move_forward, move_back, strafe_left, strafe_right, jump |

## Step 2 — Create Directory Structure

Create the project root and all subdirectories:

```
{{game_name}}/
├── project.godot
├── CLAUDE.md
├── .gitignore
├── src/
│   ├── components/          # C_ prefixed component scripts
│   ├── systems/             # NameSystem scripts
│   ├── entities/            # Entity scene definitions
│   ├── ui/                  # UI scenes and scripts
│   └── world.gd            # gecs World — system registration
├── scenes/
│   ├── main.tscn            # Entry point scene
│   └── game_world.tscn      # Gameplay scene with camera
├── test/
│   └── test_example.gd      # gdUnit4 test template
├── tests/
│   └── e2e/
│       └── conftest.py       # E2E test config (GODOT_PROJECT = "../..")
├── assets/
│   ├── sprites/
│   ├── audio/
│   ├── fonts/
│   └── ui/
├── references/              # Scene reference images (generated in Stage 4)
└── addons/                  # gecs + gdUnit4 installed here
```

## .tscn Generation Rules

When writing `.tscn` files (from templates or manually), follow these rules strictly:

1. **No UID references** — use `res://path/to/script.gd` paths, never `uid://xxx`. UID references fail in headless/CI environments because `uid_cache.bin` cannot be rebuilt.
2. **load_steps formula** — `load_steps = ext_resource_count + sub_resource_count + 1`. Count carefully; mismatch causes parse errors.
3. **parent attribute required** — only the root `[node]` omits `parent`. Every other node MUST have `parent="."` (direct child of root) or `parent="path/to/parent"`.
4. **World node setup** — always set `system_nodes_root = NodePath(".")` and `entity_nodes_root = NodePath(".")` when using SystemGroups.

## Step 3 — Fill Templates

Read each template from `templates/`, replace all `{{placeholders}}`, write output.
Remove any template comments (lines starting with `; TEMPLATE:`) from the output.

| Template | Output Path | Notes |
|----------|------------|-------|
| `project.godot.tmpl` | `project.godot` | Must be valid Godot ConfigFile |
| `claude.md.tmpl` | `CLAUDE.md` | Fill game info + ECS reference |
| `gitignore.tmpl` | `.gitignore` | Use as-is, no placeholders |
| `main_scene.tmpl` | `scenes/main.tscn` | Swap root node type for perspective |
| `world_scene.tmpl` | `scenes/game_world.tscn` | Swap node + camera types |
| `test_example.tmpl` | `test/test_example.gd` | Replace `{{GameNamePascal}}` |
| `component.tmpl` | `src/components/c_example.gd` | Example stub |
| `system.tmpl` | `src/systems/example_system.gd` | Example stub |

Write `src/world.gd` directly — too short for a template:

```gdscript
extends World

## ECS World — register systems here.
## See the gecs skill for World API details.
```

### Game Plan ECS stubs

If the Game Plan includes an ECS Architecture section with components and systems:

- **Components**: for each planned component (e.g., `C_Velocity`), create a file in
  `src/components/` based on `component.tmpl`. Fill the class name and add `@export`
  vars from the plan.
- **Systems**: for each planned system (e.g., `MovementSystem`), create a file in
  `src/systems/` based on `system.tmpl`. Fill the class name and `query()` with
  the required components.
- **World**: register all planned systems in `src/world.gd`.

## Step 4 — Genre Adaptations

After writing base template files, apply genre-specific modifications to `project.godot`:

**Platformer / Endless runner** (gravity games):
- Add `[physics]` section: `2d/default_gravity=980.0`
- Add `[input]` section with move + jump actions

**Top-down**:
- No `[physics]` section
- Add `[input]` section with 4-directional movement

**3D**:
- Change `renderer/rendering_method` to `"forward_plus"`
- Use `Node3D` / `Camera3D` in scene templates
- Add `[physics]` section: `3d/default_gravity=9.8`

For input action serialization format, read `references/project_settings.md`
— it has the exact Object() syntax and key code table.

## Step 5 — Post-Scaffold Steps

After all files are written, tell the user what to do next:

1. **Deploy GodotMaker skills** to the new project:
   ```bash
   bash <godotmaker_repo>/shell/publish.sh {{game_name}}/
   ```
   This copies skills to `.claude/skills/`, creates `godotmaker.yaml`
   (prompts for Godot executable path on first run), and creates
   `.godotmaker/config.yaml` with default project settings.

2. **Install addons** — read `references/addons.md` for details:
   - gecs -> `addons/gecs/`
   - gdUnit4 -> `addons/gdUnit4/`

3. **Register godot-mcp** for runtime debugging:
   ```bash
   claude mcp add godot -e GODOT_PATH="<godot_path>" -- npx @coding-solo/godot-mcp
   ```

4. **Verify** with headless-build: `godot --headless --quit 2>&1`

## Report

After scaffold completes, output:
- Project path (absolute)
- File tree listing
- Checklist of pending post-scaffold steps

## What This Skill Does NOT Do

- Does not implement game logic — only creates the starting structure
- Does not install addons — provides instructions in references/addons.md
- Does not run game-planner — expects a plan or minimal user input already
- Does not deploy skills — that is publish.sh's job
