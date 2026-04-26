# Release Process

GodotMaker uses semantic versioning. This page describes how to create a release and publish it to target projects.

## Versioning Scheme

The version follows **Semantic Versioning** (MAJOR.MINOR.PATCH):

| Level | When to bump | Example |
|---|---|---|
| PATCH | Bug fixes, no functionality change | 0.3.0 -> 0.3.1 |
| MINOR | New features or behavior changes (backward-compatible) | 0.3.0 -> 0.4.0 |
| MAJOR | Breaking changes requiring project migration | 0.3.0 -> 1.0.0 |

The current version is stored in the `VERSION` file at the repository root as a single line (e.g., `0.3.0`).

## Steps to Release

### 1. Make your changes

Develop, test, and get changes merged to the main branch.

### 2. Update CHANGELOG.md

Add a new version section at the top of `CHANGELOG.md`, below the header. Follow the existing format:

```markdown
## [0.4.0] -- 2026-05-01

### Added
- Description of new features

### Fixed
- Description of bug fixes

### Changed
- Description of behavior changes
```

### 3. Update the VERSION file

Write the new version number to `VERSION`:

```bash
echo "0.4.0" > VERSION
```

### 4. Commit the release

```bash
git add VERSION CHANGELOG.md
git commit -m "release: v0.4.0"
```

### 5. Tag the release (optional)

```bash
git tag v0.4.0
```

### 6. Publish to target projects

```bash
python tools/publish.py <target_godot_project_dir>
```

## How publish.py Works

The publish script (`tools/publish.py`) deploys GodotMaker into a target Godot project. It performs these steps in order:

1. **Version check** -- Compares source `VERSION` against the target's `.godotmaker/version`
2. **Publish skills** -- Flattens `skills/core/*` and `skills/reviewer/*` into `.claude/skills/`
3. **Publish tools** -- Copies `tools/` to the target
4. **Publish config** -- Copies `config/` to `.claude/config/`
5. **Publish hooks** -- Copies `hooks/` to `.godotmaker/hooks/`
6. **Deploy settings.json** -- Copies hook registration (only if not already present)
7. **Publish templates** -- Copies `templates/` to `.claude/templates/`
8. **Deploy CLAUDE.md** -- Copies game-claude.md template (only if not already present)
9. **Create godotmaker.yaml** -- Interactive prompt for Godot executable path
10. **Create project config** -- Copies default config.yaml
11. **Deploy stage schemas** -- Copies stage_schemas.json to `.godotmaker/`
12. **Create project directories** -- Creates `assets/`, `references/` subdirectories
13. **Register MCP** -- Registers godot-mcp via `claude mcp add`
14. **Ensure .gitignore** -- Adds `.claude/` entry. For `.godotmaker/`, selectively ignores only runtime state files (`state.json`, `metrics.jsonl`, `metrics_current.jsonl`)
15. **Ensure git repo** -- Initializes git with an empty commit (required for worktree isolation)
16. **Stamp version** -- Writes deployed version to `.godotmaker/version`

## Version Comparison Logic

When publishing, `publish.py` compares the source version (from `VERSION`) against the target's deployed version (from `.godotmaker/version`):

| Scenario | Behavior |
|---|---|
| Fresh install (no target version) | Proceeds without prompting |
| Same version | Proceeds (re-publish) |
| PATCH upgrade | Proceeds without prompting |
| MINOR upgrade | Shows changelog, prompts for confirmation |
| MAJOR upgrade | Shows changelog, prompts for confirmation with warning |
| Downgrade | Blocked (requires `--force`) |

The version is parsed as a `SemVer` named tuple with `major`, `minor`, and `patch` fields. Standard tuple comparison determines upgrade direction.

## The --force Flag

The `--force` flag skips upgrade confirmations and allows downgrades. See [Publish](../05-tools/publish.md) for full details.

## Why publish.py Initializes a Git Repository

The publish script calls `git init` and creates an empty initial commit in the target project if one does not exist. This is required because the orchestrator uses **git worktrees** for parallel worker isolation. Worktree creation fails with `fatal: not a valid object name: HEAD` if the repository has no commits.
