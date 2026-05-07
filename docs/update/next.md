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

- `.godotmaker/verify_report.json` — `/gm-verify` now writes a
  structured report on every run (PASS or FAIL) with per-check
  results plus `tooling_notes[]` for verification-tool crashes.
  Each non-`escalate` `suggested_fallback` ships a required
  structured operand (`crashed_on` / `narrowed_command` /
  `rule_name` / `check_name`) so consumers can act
  deterministically without parsing the free-text `error` field.
  `/gm-build` and `/gm-fixgap` Resume Checks read the report and
  translate failures into pending PLAN.md / GAP.md tasks, closing
  the retry loop where verify failures had no machine-readable
  channel driving the next iteration. Schema documented in
  `gm-verify/SKILL.md`; declared as a protocol guarantee for
  downstream consumers (see [v0.3.0 changelog](../../CHANGELOG.md)).
- `tests/test_verify_report_fixtures.py` — golden fixtures + tiny
  hand-rolled schema validator pinning the v1 **producer-side
  schema invariants** (top-level required keys, per-check required
  arrays, fallback-operand pairing, PASS↔`tooling_notes==[]`,
  `warn` lint-only). 5 representative report shapes, 19 tests.
  **Scope is intentionally producer-side and shape-only** —
  consumer behavior in `gm-build` / `gm-fixgap` remains specified
  in SKILL.md prose and is not executable-tested here.
- `tools/publish.py` validates `godot_path` interactively before
  writing `.claude/godotmaker.yaml` — runs `<godot_path> --version`,
  re-prompts on empty / unverifiable input up to 5 times, and leaves
  the file uncreated on Ctrl+C / Ctrl+D.

## Changed

- `config/stage_schemas.json` `verify` entry declares
  `files: [".godotmaker/verify_report.json"]` so the existing
  `stage_reminder.py` validator blocks the `verify` completion
  event when the report is missing — same gate mechanism that
  `evaluate` already used for `evaluation.json`.
- `hooks/check_file_permissions.py` — `VERIFY_ALLOWED_GM_FILES`
  adds `.godotmaker/verify_report.json` (the third write
  exception alongside `current_role` and `stage.jsonl`).
- `templates/GAP.md` — adds optional `Source Verify` header
  section, per-task `Source:` line, and a `Source` column in the
  Task Status table. Verify-source tasks share `C` / `J`
  severity prefixes with evaluation-source tasks but list first
  within each letter.
- `migrations/README.md` adds an explicit "merged migrations are
  immutable" rule — edits to a shipped script only affect first-time
  runners; correct mistakes by shipping a new patching migration.
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
- `docs/wiki/06-configuration/godotmaker-yaml.md` (EN + zh) describes
  the validation loop — exit code 0 is sufficient, stdout is shown as
  the detected version (or `?` when wrappers suppress it).
- `tools/check_project.py --build` covers the full gm-scaffold
  readiness gate — addon directories (`gecs` / `gdunit4` /
  `godot_e2e`), godot-e2e plugin enablement, `e2e/conftest.py`
  `GodotE2E` import, resolvable `git HEAD`, and a headless
  `<godot_path> --headless --quit` parse. Missing `godot_path` in
  `.claude/godotmaker.yaml` downgrades the headless step to a `WARN`.
- `gm-scaffold/SKILL.md` Step 2 split into 2a (project-scaffold writes
  the four base templates: `project.godot`, `main_scene`,
  `world_scene`, `.gitignore`) and 2b (gm-scaffold lead clones addons
  per `.claude/config/addon_versions.json` and enables the godot-e2e
  plugin); Step 4 collapses to a single `python tools/check_project.py
  <dir> --build` invocation.
- `project-scaffold/SKILL.md` Step 5 standalone addon-install list
  realigned with `.claude/config/addon_versions.json` — adds
  `godot_e2e -> addons/godot_e2e/` and lowercases `gdunit4`.
- `gm-scaffold/SKILL.md` Session Setup notes that `session_start.py`
  clears `.godotmaker/current_role` on every new session, so
  re-issuing the slash command re-establishes the role.

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
