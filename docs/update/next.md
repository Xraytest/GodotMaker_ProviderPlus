# Next Release

> **Contributors:** Every pull request MUST include an entry in this file describing the change.
> When a new version is released, this file will be archived as `vX.Y.Z.md` and a fresh copy will take its place.

## How to add an entry

Append your change under the appropriate category below. Use this format:

```
- Brief description of the change (#PR_NUMBER) — @author
```

If no category fits, add a new one following [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## Added

## Changed

- Versioning policy aligned with standard SemVer — PATCH / MINOR / MAJOR
  now decided by backward-compatibility of user-saved files and runtime
  state, decoupled from whether a migration ships.
- Migration system rewritten to applied-tracking model (Flyway / Alembic
  style): timestamped scripts under `migrations/`
  (`<YYYYMMDDhhmmss>_<slug>.py`) plus per-target
  `.godotmaker/applied_migrations.json`. Any non-MAJOR upgrade applies
  pending migrations; FRESH and MAJOR `--force` baseline. Use
  `python tools/migrate.py --new <slug>` to scaffold; `--baseline` or a
  manual empty tracker handles legacy projects.
- `publish.py --force` documented accurately — full clean re-init only
  happens on MAJOR upgrades; on PATCH/MINOR/SAME `--force` just skips
  prompts and overwrites `settings.json`.
- gecs v7.1.0 World pattern documented as a scene-node
  (`@onready var world: World = $World; ECS.world = world`) across
  `project-scaffold/SKILL.md`, `templates/claude.md.tmpl`, and
  `references/project_settings.md`; `src/world.gd` removed from the
  scaffold directory tree.

## Fixed

- `project-scaffold/templates/project.godot.tmpl` drops the
  `World="*res://src/world.gd"` autoload (collides with gecs v7.1.0's
  `class_name World`) and adds the missing `config_version=5` line.

- `hooks/check_file_permissions.py` asset-role gate resolves the
  candidate path against cwd via `_is_project_root_assets_md` —
  project-root `ASSETS.md` is allowed from bare and absolute path
  forms; subdirectory variants stay blocked.

## Removed

- `tools/migrate.py --from <ver> --to <ver>` CLI flags. The
  applied-tracking model derives "what to run" from the per-target
  tracker, not from a version range — pass only the target path.
- `migrations/{old}_to_{new}/` directory layout. Migrations are now flat
  `<YYYYMMDDhhmmss>_<slug>.py` files directly under `migrations/`;
  downstream forks must rename.
