# Versioning & Upgrades

How GodotMaker tracks versions and handles upgrades between releases.

## Version Scheme

GodotMaker uses [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

| Level | Meaning | Example | Upgrade behavior |
|-------|---------|---------|------------------|
| **PATCH** | Bug fixes, no functionality change | `0.3.0 → 0.3.1` | Auto-proceed, informational message |
| **MINOR** | New features or behavior changes | `0.3.0 → 0.4.0` | Show changelog, require confirmation |
| **MAJOR** | Breaking changes, may need migration | `0.x → 1.x` | Strong warning, require confirmation |

## Where Versions Live

| File | Location | Purpose |
|------|----------|---------|
| `VERSION` | GodotMaker repo root | Source of truth for current release |
| `.godotmaker/version` | Target game project | Records which version was last published |
| `CHANGELOG.md` | GodotMaker repo root | Human-readable change log per version |
| `migrations/` | GodotMaker repo root | Version migration scripts |

## Publishing & Upgrading

### Fresh Install

```bash
python tools/publish.py /path/to/my-game
```

No version exists in the target — publish proceeds directly and stamps
the version into `.godotmaker/version`.

### Upgrade (re-publish to existing project)

```bash
python tools/publish.py /path/to/my-game
```

The publish script compares the source `VERSION` against the target's
`.godotmaker/version` and behaves according to the upgrade level:

| Level | Behavior |
|-------|----------|
| **PATCH** | Proceeds automatically. No migrations. |
| **MINOR** | Shows changelog, asks confirmation, then runs migration scripts. |
| **MAJOR** | Blocks incremental migration. Requires `--force` for clean re-init. |

### Version Migrations

MINOR upgrades may include migration scripts that automatically fix
compatibility issues in the target project. Migrations live in
`migrations/{old}_to_{new}/` and run in sorted order.

Example: upgrading from 0.2.0 → 0.4.0 runs:
```
migrations/0.2_to_0.3/001_xxx.py
migrations/0.2_to_0.3/002_yyy.py
migrations/0.3_to_0.4/001_track_hooks.py
migrations/0.3_to_0.4/002_track_stage_schemas.py
```

If a migration fails, the chain aborts and publish exits with an error.
The target project may be in a partially migrated state — fix the issue
and re-run publish, or use `--force` for a clean install.

Migrations can also be run standalone for testing:
```bash
python tools/migrate.py /path/to/my-game --from 0.3.0 --to 0.4.0
```

### MAJOR Upgrades

MAJOR version bumps indicate breaking changes that cannot be handled
by incremental migration. `publish.py` refuses to upgrade across MAJOR
boundaries without `--force`, which performs a clean re-initialization.

Full rebuild cleans all framework-managed content:
- `.claude/skills/`, `.claude/agents/`, `.claude/config/`, `.claude/templates/`
- `.godotmaker/hooks/`, `.godotmaker/stage_schemas.json`
- `.godotmaker/state.json`, `.godotmaker/metrics*.jsonl`
- `tools/`
- `.claude/settings.json` (force-overwritten)

Preserved (user configuration):
- `CLAUDE.md`, `.claude/godotmaker.yaml`, `.godotmaker/config.yaml`

All migration scripts from the previous MAJOR version are deleted
at release time — they are not carried forward.

### Downgrade

Downgrading (e.g., `0.4.0 → 0.3.0`) is blocked by default. Use `--force` to override:

```bash
python tools/publish.py --force /path/to/my-game
```

### Re-publish Same Version

Re-publishing the same version is always allowed. This is useful for
picking up local changes during development.

## Session Version Display

When a Claude Code session starts in a published project, the
`session_start.py` hook reads `.godotmaker/version` and injects
`[GodotMaker vX.Y.Z]` into the session context. This helps the
orchestrator (and the user) know which framework version is active.

## Workflow for Releasing a New Version

1. Make your changes in the GodotMaker repo
2. If your changes require migration (MINOR bump), add a migration script
   to `migrations/{old}_to_{new}/` — see `migrations/README.md` for details
3. Update `CHANGELOG.md` — add a new `## [X.Y.Z]` section at the top
4. Update `VERSION` — change to the new version number
5. Commit and (optionally) tag:
   ```bash
   git add VERSION CHANGELOG.md migrations/
   git commit -m "release: vX.Y.Z"
   git tag vX.Y.Z
   ```
6. Publish to target projects:
   ```bash
   python tools/publish.py /path/to/my-game
   ```

## What Gets Overwritten on Upgrade

Every publish overwrites:

| Directory | Content |
|-----------|---------|
| `.claude/skills/` | All skills (flattened from core + reviewer) |
| `.claude/agents/` | Agent definitions (worker, verifier, reviewer, analyst) |
| `.godotmaker/hooks/` | All hook scripts |
| `.claude/config/` | Config files (settings.json only with `--force`) |
| `.claude/templates/` | Document templates |
| `tools/` | Python tools (check_project, check_env, etc.) |

These are **not** overwritten (created only on fresh install):

| File | Reason |
|------|--------|
| `CLAUDE.md` | User may have customized it |
| `.claude/settings.json` | User hook configuration (overwritten only with `--force`) |
| `.claude/godotmaker.yaml` | Host-specific paths |
| `.godotmaker/config.yaml` | Project-specific settings |

## Note on addon_versions.json

`config/addon_versions.json` tracks Godot addon versions (gecs, gdUnit4, etc.)
— this is separate from GodotMaker's own version. Addon versions are pinned
per Godot engine version and managed independently.
