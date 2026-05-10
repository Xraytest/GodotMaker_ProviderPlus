## Summary

Brief description of the changes.

## Motivation

Why is this change needed? Link related issues: `Closes #xxx`

## Changes

- [ ] Change 1
- [ ] Change 2

## Benchmark Verification (Required)

**All PRs must include benchmark results.** Verify your changes do not regress performance before submitting.

- [ ] I have run benchmarks before and after my changes
- [ ] Benchmark results are attached below or in a linked comment
- [ ] No performance regressions detected

<details>
<summary>Benchmark Results</summary>

```
Paste benchmark output here.
Include: test name, before/after numbers, environment info.
```

</details>

## Testing

- [ ] New/updated unit tests pass (`pytest` / `gdUnit4`)
- [ ] Gitleaks pre-commit hook passes (no secrets detected)
- [ ] Manual testing completed (describe below)

## Version Compatibility

Does this PR change behavior, move files, rename config keys, or break existing target projects?

- [ ] **No** — no migration needed
- [ ] **Yes** — migration script added to `migrations/` ([guide](migrations/README.md))

> If "Yes": run `python tools/migrate.py --new <slug>` to scaffold
> `migrations/<utc-timestamp>_<slug>.py`. The script must define
> `migrate(target: Path) -> None` and be idempotent. The bump level does
> NOT gate migrations — PATCH releases can ship them too.

### Migration version-upgrade gate (required if a migration script is added or modified)

A unit test on a synthetic `tmp_path` project is necessary but **not sufficient**. Migrations must be exercised through the actual publish-upgrade path — take a real GodotMaker game project pinned at the previous version and run `python tools/publish.py <target>` so the migration runs as it would for an end user. The 2026-05-09 e2e showed why: the tag-pipeline migration's unit tests passed against synthetic minimal projects while it silently missed ASSETS.md `Tag` column, scene reference rows, and PLAN.md `Tag Mechanics` section — gaps that only surfaced when a real legacy project later entered a `/gm-*` loop.

- [ ] Real GodotMaker game project pinned at the previous version was upgraded via `python tools/publish.py <target>`
- [ ] Post-upgrade `<target>/.godotmaker/applied_migrations.json` contains the new migration ID with `source: "executed"`
- [ ] Post-upgrade on-disk state (files the migration was supposed to update) inspected and matches expectations
- [ ] Re-running `tools/publish.py` produces no further migration changes (idempotency confirmed)
- [ ] Result attached or summarized below

## Checklist

- [ ] Code follows project conventions (English code/comments, GDScript style guide)
- [ ] ECS systems declare proper read/write metadata
- [ ] No hardcoded secrets or API keys
- [ ] [`docs/update/next.md`](docs/update/next.md) updated with a changelog entry for this PR
