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

> If "Yes": add a script to `migrations/{current}_to_{next}/NNN_description.py`.
> The script must define `migrate(target: Path) -> None` and be idempotent.

## Checklist

- [ ] Code follows project conventions (English code/comments, GDScript style guide)
- [ ] ECS systems declare proper read/write metadata
- [ ] No hardcoded secrets or API keys
- [ ] [`docs/update/next.md`](docs/update/next.md) updated with a changelog entry for this PR
