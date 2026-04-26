# Version Migrations

Migration scripts that run automatically during `publish.py` upgrades.

## Directory Structure

```
migrations/
  0.3_to_0.4/          # MINOR: 0.3.x -> 0.4.x
    001_track_hooks.py
    002_update_gitignore.py
  0.4_to_0.5/          # next MINOR bump
    001_xxx.py
```

## Naming Convention

- Directory: `{old_minor}_to_{new_minor}/` (e.g., `0.3_to_0.4/`)
- Files: `NNN_description.py` — zero-padded, executed in sorted order

## How Migrations Run

1. `publish.py` reads the target's `.godotmaker/version`
2. Compares against source `VERSION`
3. Finds all migration directories in the chain (e.g., `0.3→0.4→0.5`)
4. Executes each directory's scripts in sorted order
5. MAJOR upgrade: refuses incremental migration, requires `--force` (full re-init)
6. PATCH upgrade: skips migrations entirely (no behavior change)

## Writing a Migration Script

Each script must define a `migrate(target: Path) -> None` function:

```python
"""Brief description of what this migration does."""
from pathlib import Path

def migrate(target: Path) -> None:
    """target is the absolute path to the game project root."""
    # Do your migration work here.
    # Raise an exception to abort the migration chain.
    pass
```

Rules:
- Scripts MUST be idempotent (safe to re-run)
- Scripts MUST NOT prompt for user input
- Scripts should print what they do (for publish.py output)
- If a script fails, the entire migration chain aborts

## When to Write a Migration

Add a migration script when your PR introduces:
- File location changes (moved hooks, config, etc.)
- New files that must exist in the target project
- Git tracking changes (files that need `git add`)
- Settings format changes
- Removed or renamed files that leave stale copies

Do NOT write a migration for:
- Skill content changes (overwritten on every publish)
- New features that don't affect existing projects
- Bug fixes (PATCH level)

## MAJOR Version Policy

MAJOR upgrades (e.g., 0.x → 1.x) do not run migrations. They use
`--force` for a full re-initialization that wipes all framework-managed
content (skills, hooks, config, templates, tools, state files) and
re-deploys from scratch. User configs (CLAUDE.md, godotmaker.yaml,
config.yaml) are preserved.

When releasing a new MAJOR version:
1. Delete all migration directories from the previous MAJOR
2. Start fresh with an empty `migrations/` directory

Migration scripts only accumulate within one MAJOR version and are
discarded at the next MAJOR boundary.
