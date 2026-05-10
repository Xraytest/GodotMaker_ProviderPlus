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

- **`.worktreeinclude` written by `publish.py`.** New project-root file (gitignore syntax) carrying `.claude/` (minus `.claude/worktrees/`) into sub-agent worktrees so workers can read `godotmaker.yaml` and `skills/` from their isolated cwd. Anthropic-documented mechanism — see https://code.claude.com/docs/en/worktrees. — @LiuXin

## Changed

## Fixed

- **`gm-verify`, `gm-evaluate`, `gm-finalize` assumed `godot` was on `PATH`.** Each SKILL now reads `godot_path` from `.claude/godotmaker.yaml` (written by `tools/publish.py` at first install) and substitutes it for `<godot_path>` in every `godot --headless …` command. Falls back to plain `godot` if the field is missing; STOPs and asks for re-publish if both fail. — @LiuXin
- **`gm-verify` gdUnit4 invocation was stale.** Updated to gdUnit4 v4.x syntax: `addons/gdUnit4/bin/GdUnitCmdTool.gd` (capital U, different entry script) and `--ignoreHeadlessMode` (required under `--headless`). — @LiuXin
- **`tools/check_project.py` `check_e2e()` fallback misclassified `conftest.py`.** Fallback now skips `conftest.py` / `__init__.py` and requires `test_*.py` / `*_test.py` naming before adding to `e2e_files`. Defense-in-depth alongside the `--all` removal in `gm-verify`. — @LiuXin
- **`tools/migrate.py` halted on legacy targets it could deterministically resolve.** Legacy targets (`.godotmaker/version` present but no `applied_migrations.json`) with migration scripts on disk previously raised `LegacyTargetWithMigrationsError` and forced manual recovery. They couldn't have been applied yet (predate the migrations' introduction), so `migrate.py` now auto-creates `{"applied": []}` and falls through to the pending-application path. `migrate.py --baseline` remains for the hand-applied edge case. Dead `LegacyTargetWithMigrationsError` class + handlers + wiki entries removed. — @LiuXin
- **`gm-verify` "When Done" step 2 specified WHAT but not HOW for the stage event append** — verifier picked `Edit` (replace semantics), which silently no-op'd on non-matching `old_string` and stalled cli despite a passing `verify_report.json`. Aligned to the sibling SKILLs' explicit Read → append → write-back idiom plus a `Do NOT use Edit` warning. — @LiuXin
- **Reviewer agent over-read context regardless of change size.** `agents/reviewer.md` Execution Steps reordered: read deliverables FIRST, discover reviewer skills via directory pattern (glob `.claude/skills/*/checklist.md` — convention is `SKILL.md` + `gotchas.md` + `checklist.md` trio; reference skills like `gecs/` with only `gotchas.md` are excluded), match by evidence in the deliverables, load gotchas + checklist ONLY for matched domains. Hardcoded 8-reviewer list removed — the directory IS the catalog. New scope-size rule: skip ECS general review when all deliverables are test files (`test_*.gd` / `*_test.gd`) AND ≤3 of them. — @LiuXin

## Removed

- **gdtoolkit (gdlint + gdformat) disabled across the pipeline.** Recurring `gdtoolkit/linter/class_checks.py:144 NotImplementedError` crashes on ECS-style class shapes had zero project-code signal — value is style consistency only. `verify_report.json` lint schema preserved so consumers don't need to special-case. Tracked as ROADMAP `R-112`; rationale + restore guide in [`docs/decisions/disable-gdtoolkit.md`](docs/decisions/disable-gdtoolkit.md). — @LiuXin
- **Stale `--all` e2e gating in `gm-verify` static check.** `python tools/check_project.py --all` replaced with `--build --ecs --tests --plan --mcp`. The `e2e/` suite is owned by the Evaluator (per `gm-build` Hard Rule 2 / `gm-evaluate` Phase 2); gating it during verify caused phantom failures on every fresh tag's first verify. — @LiuXin
