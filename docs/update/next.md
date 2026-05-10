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

- **`.worktreeinclude` written by `publish.py`.** New project-root file (gitignore syntax) telling claude-code which paths to carry over when creating a sub-agent worktree. Includes `.claude/` minus `.claude/worktrees/` (negation prevents recursion if a sub-agent is already inside a worktree). Sub-agents dispatched into worktrees can now read `.claude/godotmaker.yaml` and `.claude/skills/` from their isolated cwd, fixing the worker-burn case-006 incident where workers in worktrees PATH-spelunked for `godot` despite the `godot_path` SKILL fix below. Anthropic-documented mechanism — see https://code.claude.com/docs/en/worktrees. — @LiuXin

## Changed

## Fixed

- **`gm-verify`, `gm-evaluate`, `gm-finalize` assumed `godot` was on `PATH`.** Each SKILL now reads `godot_path` from `.claude/godotmaker.yaml` (written by `tools/publish.py` at first install) and substitutes it for `<godot_path>` in every `godot --headless …` command. Falls back to plain `godot` only when the field is missing; STOPs and asks the user to re-run `tools/publish.py` if both fail. PATH-spelunking is explicitly forbidden in the SKILL — that's the load-bearing line for cutting the multi-turn PATH-discovery loops sub-agents previously fell into. — @LiuXin
- **`gm-verify` gdUnit4 invocation was stale.** SKILL sample command was `godot --headless -s addons/gdunit4/bin/gdunit4_run.gd`; the addon shipped via `config/addon_versions.json` is gdUnit4 v4.x, which lives at `addons/gdUnit4/bin/GdUnitCmdTool.gd` (capital U, different entry script) and requires `--ignoreHeadlessMode` to run under `--headless`. Updated to current syntax with an inline note explaining the casing / entry / flag. — @LiuXin
- **`tools/check_project.py` `check_e2e()` fallback misclassified `conftest.py`.** When `e2e/` had no `test_*.py` files, the fallback walked the project for `*.py` files whose path contained `e2e`, added `e2e/conftest.py` (a pytest infrastructure file with no `def test_…`) to `e2e_files`, then failed it for "no test functions". Fallback now skips `conftest.py` / `__init__.py` and requires `test_*.py` / `*_test.py` naming before adding to `e2e_files`. Defense-in-depth alongside the `gm-verify` `--all` removal — anyone calling `check_project.py --e2e` directly (or `--all` from accept / rescue) on a pre-evaluate project still gets a clean classification. — @LiuXin
- **`tools/migrate.py` halted on legacy targets it could deterministically resolve.** Targets stamped with `.godotmaker/version` predating the `applied_migrations.json` tracker AND with migration scripts on disk previously raised `LegacyTargetWithMigrationsError` and forced a manual recovery step (create `{"applied": []}` by hand, then re-run publish — with a Windows PowerShell-incompatible Python one-liner as the only cross-platform shape). The migrations could not have been applied yet (they didn't exist when the project was stamped), so the answer was unambiguously "no, not applied". `migrate.py` now auto-creates `{"applied": []}` for this case and falls through to the normal pending-application path; the hand-applied edge case still has the explicit `migrate.py --baseline` opt-out. The dead `LegacyTargetWithMigrationsError` class, the `publish.py` `except` exiting with code 3, the matching `TestPublishLegacyError` test, and the troubleshooting wiki entries are all removed. — @LiuXin

## Removed

- **Stale `--all` e2e gating in `gm-verify` static check.** `python tools/check_project.py --all` was replaced with `--build --ecs --tests --plan --mcp` in `gm-verify/SKILL.md`. The `e2e/` suite is owned by the Evaluator (per `gm-build` Hard Rule 2 / `gm-evaluate` Phase 2) and written / maintained AFTER `/gm-verify`; gating it during verify caused phantom failures on every fresh tag's first verify (the `e2e/conftest.py` stub, with no `def test_…`, was the trigger). — @LiuXin
