# Version Migrations

Migration scripts that run automatically during `publish.py` upgrades.

This system is **decoupled from GodotMaker's MAJOR.MINOR.PATCH version**.
A migration is a tool for rewriting something inside an existing target
project; whether you ship one is independent of which version level you
bump.

## Concept

Each migration is a single Python script identified by its full filename
stem (the 14-digit UTC timestamp **plus** the slug). Every target project
records which IDs it has applied in `.godotmaker/applied_migrations.json`.
On every publish, `migrate.py` discovers all migrations on disk, subtracts
the ones already applied to the target, and runs the rest in chronological
order.

> The ID is the full stem, not just the timestamp prefix — two scripts
> created in the same UTC second still produce distinct IDs because their
> slugs differ. This makes simultaneous PRs from different contributors
> safe even at second-precision timestamps.

This is the same model as Flyway, Alembic, Rails ActiveRecord, Prisma,
TypeORM, and Liquibase — single monotonic IDs plus per-target applied
tracking, decoupled from the product's release cadence.

## Naming Convention

```
migrations/
  20260429100000_fix_state_path.py
  20260430153000_rename_metrics_field.py
  20260501090000_add_role_lock.py
```

Format: `<YYYYMMDDhhmmss>_<slug>.py`

- **Migration ID = full filename stem**, e.g. `20260429100000_fix_state_path`.
  The 14-digit UTC timestamp guarantees chronological order via
  lexicographic sort; the slug guarantees uniqueness when two scripts
  share a second.
- Slug is `[a-z0-9_]+` (lowercase, underscores). Carried into the ID,
  so it must remain stable once the migration is in `applied_migrations.json`
  on any target project — renaming a slug is equivalent to inventing a
  new migration that will re-run.
- Anything not matching this pattern (`README.md`, `_helpers.py`,
  `__pycache__/`, etc.) is ignored by the discovery scan.

## Scaffold a new migration

```bash
python tools/migrate.py --new fix-state-path
# Creates: migrations/<current-utc-timestamp>_fix_state_path.py
```

The slug is sanitised to lowercase + underscores (`Fix State!! Path`
becomes `fix_state_path`). The timestamp is captured at creation time
with second precision, and the slug is part of the ID, so collisions
between independent PRs require **the same UTC second AND the same slug
choice** — extremely rare in practice. When it does happen,
`create_migration_template` raises `FileExistsError` at scaffold time,
so the second author just picks a different slug and re-runs.

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

- Once a migration is merged to `main`, treat it as **immutable**.
  Editing the body of a shipped migration only affects users who run it
  for the first time after your edit — anyone whose
  `applied_migrations.json` already records that ID will never see the
  fix. To correct a mistake, ship a **new** migration that patches
  whatever the broken one left behind.
- Scripts MUST be idempotent (safe to re-run if a previous run was
  interrupted before being recorded).
- Scripts MUST NOT prompt for user input.
- Scripts should print what they do (it goes into publish.py output).
- If a script raises, the chain aborts immediately. Any scripts that
  already succeeded keep their entries in `applied_migrations.json`, so a
  re-run picks up exactly where it left off.

## How Migrations Run

1. `publish.py` calls `run_migrations(target)` after deploying framework
   files (skills / hooks / agents / templates / tools).
2. `migrate.py` reads `<target>/.godotmaker/applied_migrations.json` and
   computes `pending = discover_migrations() - applied_ids`.
3. Each pending script runs in chronological order. After each success,
   its entry is appended to `applied_migrations.json` immediately.
4. On the next publish, anything not yet recorded runs again — successful
   scripts will not re-run.

The product version (`VERSION` file, `.godotmaker/version`) is **not
consulted** during this process. Migrations advance independently.

## When publish.py baselines instead of running

In two situations a target starts with the latest format and has nothing
to migrate from. `publish.py` calls `baseline_applied(target)` instead,
which marks every current migration as applied without executing it:

| Situation | Why baseline |
|---|---|
| **Fresh install** (no `.godotmaker/version`) | Target has no historical state to migrate |
| **MAJOR `--force` re-init** | `--force` wipes state files and re-deploys; same as fresh |

A third edge case is handled inside `run_migrations()` itself: a
**legacy target** (has `.godotmaker/version` but no
`applied_migrations.json` — created by a pre-tracking GodotMaker version)
splits into two cases:

- **Legacy target + empty `migrations/`**: bootstrap an empty tracker
  (`{"applied": []}`) and return successfully. The target is now
  "tracked but with zero applied", so the next release that ships V
  files will go through the normal pending-application path.
- **Legacy target + non-empty `migrations/`**: raise
  `LegacyTargetWithMigrationsError` and abort. We cannot safely decide
  whether those V files were already applied to the target's old state
  (in which case we should baseline) or still need to run (in which
  case we should execute) — auto-deciding either way risks silent data
  loss. The error message tells the user how to recover: either
  `--baseline` (mark everything applied without running) or manually
  create an empty tracker (so the next publish runs everything as
  pending). `publish.py --force` is **not** a recovery option here:
  the `--force` cleanup loop only runs on MAJOR upgrades, so for a
  legacy + migrations collision on PATCH/MINOR/SAME the user would
  just hit the same exit 3 again.

> **Transition note for the version that introduces applied tracking.**
> Ship the tracking machinery in one release with an empty `migrations/`.
> Legacy targets reaching that release will hit the bootstrap branch
> above and emerge as "tracked, zero applied" — fully safe. Then later
> releases can ship V files normally; legacy users who *skipped* the
> tracking-introduction release will hit `LegacyTargetWithMigrationsError`
> on first contact with V files and pick a recovery path explicitly.
> The previous design tried to auto-baseline legacy + V silently, which
> would skip required cleanup work — the explicit error is by design,
> not a regression.

Each baseline entry carries `"source": "baseline"` in
`applied_migrations.json`; entries from real execution carry
`"source": "executed"`. The distinction has no behavioural effect — both
count as applied — and the field is **best-effort diagnostic metadata**:
it is validated as a closed enum on read (any other value is treated as
tracker corruption) but downstream tooling should not branch on the
difference between `baseline` and `executed`.

If `applied_migrations.json` becomes corrupt — invalid JSON, wrong
shape, missing required fields, or an unknown `source` value —
`migrate.py` raises `TrackerCorruptionError` instead of silently
treating the file as empty (which would re-run every historical
migration on the next publish). Recover from VCS, run
`python tools/migrate.py <target> --baseline` to reset tracking from
the current state, or delete the file to treat the project as a legacy
target (which then takes the legacy bootstrap branch above:
`migrations/` empty → empty tracker; non-empty → explicit
`LegacyTargetWithMigrationsError`).

## Same-version republish

`publish.py` also calls `run_migrations()` on SAME-version republish (re-running
`publish.py` against an already-up-to-date target — typical during framework
development). Any V file you added locally without bumping `VERSION` will be
applied on the next republish; this is the same idempotent behaviour as Flyway,
Rails, and Alembic.

## When to write a migration

Write one when your change requires rewriting something inside an
existing target project that re-publishing alone cannot fix:

- Path / location changes (a hook used to write to wrong directory; old
  state files are now orphaned).
- Schema changes in user-saved files (`config.yaml` key renamed) or
  runtime state (`state.json` field type changed, `metrics.jsonl` line
  format changed).
- New files that must exist in the target project and are not auto-deployed.
- Removed or renamed files that leave stale copies behind.
- A bug fix that requires correcting state already written by an older
  version (PATCH-level migrations are first-class — write one if needed).

Do NOT write a migration for:

- Skill / hook / agent / template / tool content changes — those are
  overwritten on every publish, so re-running publish *is* the migration.
- New features that simply add files (those are deployed by publish itself).
- Bug fixes that only change framework code, with nothing to clean up
  in existing target projects.

## CLI

```bash
# Apply pending migrations (the diff between disk and applied_migrations.json)
python tools/migrate.py /path/to/target

# Mark all current migrations as applied without running them
python tools/migrate.py /path/to/target --baseline

# Scaffold a new migration with the current UTC timestamp
python tools/migrate.py --new my-slug
```

`publish.py` does NOT always invoke the first form. On FRESH install and
MAJOR `--force` re-init it calls `baseline_applied()` directly (the
second form's library equivalent), since a brand-new target has nothing
to migrate from. The first form is what runs on PATCH / MINOR / SAME
upgrades — and what you get when you call the CLI yourself.

If you point the bare `migrate.py /target` form at a project that has
**no `.godotmaker/version` file at all** (truly fresh, never published),
every V file on disk will be **executed**, not baselined. Each V must be
written assuming it might run against an empty target; if you want
baseline semantics on a fresh project, pass `--baseline` explicitly.

## What about MAJOR upgrades?

MAJOR releases skip the migration system entirely. A MAJOR bump is
defined as a backward-incompatible change to user-saved files or runtime
state — by construction, no incremental migration can bridge it.

The intended path is `publish.py --force`, which wipes framework content
and runtime state, re-deploys from scratch, then baselines the migration
tracker. User configs (`CLAUDE.md`, `.claude/godotmaker.yaml`,
`.godotmaker/config.yaml`) and the user's game code are preserved.

There is no convention for "deleting old migrations at MAJOR boundaries"
in the new model — the timestamp series is monotonic and global. If a
migration becomes irrelevant for projects that have moved past it (which
happens for every executed migration), it stays on disk as historical
record; new fresh installs will baseline it as applied without running.
