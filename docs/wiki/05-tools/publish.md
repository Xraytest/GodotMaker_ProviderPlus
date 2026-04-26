# Publish System

The publish system deploys GodotMaker's skills, hooks, tools, configuration, and templates into a target Godot game project. It is the primary mechanism for setting up new projects and upgrading existing ones.

## Usage

**Linux / macOS:**

```bash
bash shell/publish.sh [--force] <target_godot_project_dir>
```

**Windows (PowerShell):**

```powershell
.\shell\publish.ps1 [-Force|--force] <target_godot_project_dir>
```

Both shell scripts are thin wrappers that detect Python and delegate to `tools/publish.py`. You can also invoke Python directly:

```bash
python tools/publish.py [--force] <target_godot_project_dir>
```

## What Publish Does

Publish copies the GodotMaker framework into a target Godot project so that Claude Code sessions in that project have access to skills, hooks, tools, and templates. It also configures the godot-mcp MCP server, initializes git, and stamps a version marker.

## Publish Steps (in order)

1. **Version check** -- Compare `VERSION` (repo root) against `.godotmaker/version` (target). May abort on MAJOR/MINOR upgrades without `--force`.
2. **Force clean** (if `--force`) -- Delete and recreate `.claude/skills/`.
3. **Publish skills** -- Flatten-copy `skills/core/*` and `skills/reviewer/*` into `.claude/skills/`. Also copies `_read_config.sh` helper.
4. **Publish tools** -- Copy `tools/` directory to `<target>/tools/`.
5. **Publish config** -- Copy `config/` directory to `.claude/config/`.
6. **Publish hooks** -- Copy `hooks/` directory to `.godotmaker/hooks/`.
7. **Deploy settings.json** -- Copy `config/settings.json` to `.claude/settings.json` (only if it does not exist, or `--force`).
8. **Publish templates** -- Copy `templates/` directory to `.claude/templates/`.
9. **Deploy CLAUDE.md** -- Copy `templates/game-claude.md` to `<target>/CLAUDE.md` (only on fresh install).
10. **Create godotmaker.yaml** -- Interactive prompt for Godot executable path. Writes to `.claude/godotmaker.yaml`. Skipped if file already exists.
11. **Create project config** -- Copy `config/config.yaml.default` to `.godotmaker/config.yaml` (only on fresh install).
12. **Deploy stage_schemas.json** -- Copy `config/stage_schemas.json` to `.godotmaker/stage_schemas.json`.
13. **Create project directories** -- Create `assets/sprites`, `assets/audio`, `assets/fonts`, `assets/ui`, `references` if missing.
14. **Register godot-mcp** -- Run `claude mcp add godot` to register the MCP server with the Godot path from step 10.
15. **Ensure .gitignore** -- Add `.claude/` to `.gitignore`. For `.godotmaker/`, add selective ignores: only runtime state files (`state.json`, `metrics.jsonl`, `metrics_current.jsonl`) are gitignored.
16. **Ensure git repo** -- Run `git init` and create an initial empty commit if needed (required for worktree isolation).
17. **Stamp version** -- Write the source version to `.godotmaker/version`.

## Version Management

GodotMaker uses [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

| Location | Purpose |
|---|---|
| `VERSION` (repo root) | Source of truth for current GodotMaker release |
| `.godotmaker/version` (target project) | Records which version was last published |
| `CHANGELOG.md` (repo root) | Human-readable changes per version |

### Upgrade behavior by severity

| Level | Behavior |
|---|---|
| **PATCH** | Auto-proceed. Prints "Bug fixes only, no functionality change." |
| **MINOR** | Displays the CHANGELOG section for the new version. Prompts `Proceed with MINOR upgrade? [y/N]`. |
| **MAJOR** | Displays the CHANGELOG section with a strong warning ("Breaking changes -- backup your project first!"). Prompts for confirmation. |
| **Same version** | Always proceeds (useful for picking up local changes). |
| **Downgrade** | Blocked by default. Prints a warning and exits. |

## What Gets Overwritten vs. Preserved

**Overwritten on every publish:**

| Directory | Content |
|---|---|
| `.claude/skills/` | All skills (flattened from core + reviewer) |
| `.godotmaker/hooks/` | All hook scripts |
| `.claude/config/` | Config files |
| `.claude/templates/` | Document templates |
| `tools/` | Python tools |
| `.godotmaker/stage_schemas.json` | Stage validation schema |

**Preserved (created only on fresh install, never overwritten):**

| File | Reason |
|---|---|
| `CLAUDE.md` | User may have customized it |
| `.claude/settings.json` | User hook configuration (overwritten only with `--force`) |
| `.claude/godotmaker.yaml` | Host-specific paths |
| `.godotmaker/config.yaml` | Project-specific settings |

## The --force Flag

The `--force` flag does three things:

1. **Cleans skills directory** -- Deletes `.claude/skills/` before re-publishing (removes stale skills from previous versions).
2. **Skips confirmation prompts** -- MINOR and MAJOR upgrades proceed without asking.
3. **Allows downgrades** -- Overrides the downgrade block.
4. **Overwrites settings.json** -- Replaces `.claude/settings.json` even if it already exists.

## Excluded Content

The following directories are excluded from all copy operations: `__pycache__`, `doc_source`, `.workspace`.

## See Also

- [Check Env](check-env.md) -- environment validation tool
- [Check Project](check-project.md) -- project structure validator
- [Asset Tools](asset-tools.md) -- asset generation and processing utilities
