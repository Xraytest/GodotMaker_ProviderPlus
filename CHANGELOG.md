# Changelog

All notable changes to GodotMaker will be documented in this file.

Format: [Semantic Versioning](https://semver.org/) — MAJOR.MINOR.PATCH

## [0.3.0] — 2026-05-07

### Added

- **`.godotmaker/verify_report.json` — structured feedback channel from `/gm-verify` to `/gm-build` and `/gm-fixgap`.** `/gm-verify` now writes this file on every run (PASS or FAIL) with per-check results: `checks.build.errors[]`, `checks.unit_tests.failures[]`, `checks.lint.{issues, format_drift}`, `checks.static_check.issues[]`, plus `tooling_notes[]` for verification-tool crashes (gdlint / gdformat / godot etc.) carrying a `suggested_fallback` discriminator (`exclude_file` / `scope_narrow` / `add_gdlintrc_rule` / `skip_check` / `escalate`) and a matching structured operand (`crashed_on` / `narrowed_command` / `rule_name` / `check_name`) so consumers can apply the fix deterministically without parsing free-text `error` strings. Per-check `result` is a 4-value enum `pass | warn | fail | error` — `error` distinguishes "tool crashed, project status unknown" (consumer applies a config fallback) from `fail` "project has problems" (consumer dispatches a code fix). On their next invocation, `/gm-build` and `/gm-fixgap` Resume Checks read this report — when its `ts` is newer than the last `build`/`fixgap` event in `stage.jsonl` and overall `result == "fail"` (any per-check `fail` or `error`), they translate each failure into pending PLAN.md / GAP.md tasks before resuming. Producers that cannot fill the required operand for a non-`escalate` fallback MUST emit `escalate` instead; consumers that see a non-`escalate` fallback with a missing operand MUST degrade to `escalate` (surface to user, do not auto-fix). This closes the retry loop where verify failures had no machine-readable channel to drive the next iteration.
- `gm-verify` SKILL.md "Output Format" split into A. chat-readable report and B. machine-readable JSON, with the full schema documented inline. Permission section adds `verify_report.json` as a third write exception alongside `current_role` and `stage.jsonl`.
- `gm-build` SKILL.md "Step 0 — Process Verify Feedback" — runs only when Resume Check flags a fresh `verify_report.json`; per-check translation rules cover compile errors, test failures, lint issues, format drift, static-check issues, and tooling-note fallbacks (config-only fixes, never code deletions).
- `gm-fixgap` SKILL.md "Step 1b — Pull failures from `verify_report.json`" — same translation rules as gm-build. Verify-source tasks share the existing `C` / `J` severity prefixes with evaluation-source tasks but are listed first within each letter so the mechanical layer is fixed before product-layer fixes are dispatched. Per-task `Source: verify_report.json | evaluation.json` line records origin.
- `templates/GAP.md` — adds optional `Source Verify` header section, per-task `Source:` line, and a `Source` column in the Task Status table.
- Wiki — `the-9-roles.md` (EN + zh) gm-verify section documents `verify_report.json` as the protocol-level feedback channel; gm-build and gm-fixgap sections describe the Resume Check feedback consumption.
- Wiki — `common-problems.md` (EN + zh) adds "`/gm-verify` keeps failing on the same issues and `/gm-build` retries forever" diagnostic with the three failure modes (missing report, stale report, old SKILL.md deployed) and step-by-step fixes.

### Changed

- `config/stage_schemas.json` `verify` entry now declares `files: [".godotmaker/verify_report.json"]`. The existing `stage_reminder.py` path validator automatically blocks the `verify` completion event from being appended to `stage.jsonl` when the report file is missing — same gate mechanism as `evaluate` already uses for `evaluation.json`.
- `hooks/check_file_permissions.py` — `VERIFY_ALLOWED_GM_FILES` adds `.godotmaker/verify_report.json`. The block message lists all three allowed paths.

### Upgrade note (v0.2.x → v0.3.0)

The new feedback channel only takes effect once the **deployed** SKILL.md files (under each project's `.claude/skills/`) are the v0.3.0 versions. The `tools/publish.py` upgrade flow normally handles this on a MINOR bump, but a project that was last published before v0.3.0 will keep running the old `gm-build` / `gm-fixgap` SKILLs (and the retry-loop bug the channel fixes) until you redeploy. To force a clean SKILL refresh:

```
python tools/publish.py --force <project_dir>
```

`--force` overwrites `.claude/skills/`, hooks, `stage_schemas.json`, and templates; it leaves your project state (`.godotmaker/stage.jsonl`, `evaluation.json`, `PLAN.md`, `GAP.md`, etc.) untouched. No migration script ships with v0.3.0 — the change is fully additive on the state side, and `gm-fixgap`'s Resume Check has a per-row backward-compat clause for `GAP.md` files written under the v0.2.x format.

### Protocol guarantee (downstream-facing)

- `/gm-verify` MUST produce `.godotmaker/verify_report.json` every run. Schema is documented in `gm-verify/SKILL.md` Output Format Section B; downstream consumers may rely on top-level keys (`result`, `ts`, `checks`, `tooling_notes`) and per-check shapes.
- **Open string discriminators** (may gain new values in future releases — consumers MUST tolerate unknown values, never crash):
  - `checks.static_check.issues[].check` — fall back to using the raw value verbatim and treating the issue as a generic project-code fix.
  - `tooling_notes[].suggested_fallback` — fall back to treating it as `"escalate"` (do NOT auto-fix; surface the tool + error + crashed_on fields to the user and halt the current build/fixgap cycle) and recording the raw value verbatim. The `"escalate"` value is itself a shipped discriminator for non-lint tool crashes (`tool == "godot"`, full-run dumps) where no in-place config edit can route around it.
  - Each non-`escalate` fallback ships a required operand field (`exclude_file`→`crashed_on`, `scope_narrow`→`narrowed_command`, `add_gdlintrc_rule`→`rule_name`, `skip_check`→`check_name`). A note where the operand is missing/null/empty MUST be treated as `escalate` by the consumer; producers MUST emit `escalate` rather than emitting a routable fallback they cannot operationalize.
- **Closed enums** (changing requires a coordinated SKILL.md update across producer and consumers):
  - top-level `result`: `pass | fail`.
  - per-check `result`: `pass | warn | fail | error` (`warn` is lint-only).
- **Producer invariants** (always true in any report `/gm-verify` writes; consumers may rely on these without further validation):
  - `result: "pass"` ⇔ every `checks.*.result ∈ {pass, warn}` AND `tooling_notes == []`. A non-empty `tooling_notes` array implies at least one `checks.*.result == "error"`, which forces `result: "fail"` — these two cannot coexist with PASS.
  - Every `checks.<name>` carries its own required arrays even when empty: `build.errors`, `unit_tests.failures`, `lint.issues`, `static_check.issues`. `unit_tests` additionally carries integer `passed` and `failed` counts. Consumers may iterate these arrays without presence checks.
  - Every non-`escalate` `tooling_notes[*].suggested_fallback` carries a non-empty operand field per the table above; producers must emit `escalate` instead of leaving an operand unfilled.
- `stage.jsonl`'s existing contract is preserved — PASS still appends `{"role": "verify", "ts": ...}`. Existing harnesses that judge verify outcome by line-count delta and last-event role need no change.

## [0.2.2] — 2026-04-28

### Added

- `auditor_model` config key in `config/config.yaml.default` (default `sonnet`).
- Cross-layer consistency tests — `tests/test_config_consistency.py` (skill-referenced `*_model` defaults match config) and `tests/test_audit_workflow.py` (Round 6 + Round 7 dispatch contract).
- `docs/wiki/07-contributing/codebase-guide.md` (EN + zh) "Permission contract layers" subsection explaining the schema vs hook vs SKILL.md split.
- `docs/update/v0.2.0.md` "Upgrading from v0.1.x" section — declares clean redeploy via `--force` as the supported path; no `0.1_to_0.2` migration is shipped.
- Pre-push CI-mirror hook (`scripts/pre-push`, `scripts/install-hooks.sh`).

### Changed

- `check_file_permissions.py` narrowed evaluate/verify write scopes — evaluate may write `e2e/`, `.godotmaker/evaluation.json`, `.godotmaker/stage.jsonl`, `.godotmaker/current_role`; verify is read-only except `stage.jsonl` and `current_role`.
- `gm-evaluate`/`gm-verify`/`gm-fixgap` SKILL.md now have explicit Permission sections that mirror the hook allow-lists; `gm-fixgap` notes the `fixgap → verify → evaluate` loop position.
- `game-planner` `auditor_model` default switched from `opus` to `sonnet` to match `config.yaml.default`.
- The 9-roles wiki page (EN + zh) — `/gm-asset` section expanded to describe scene reference generation and how `/gm-evaluate` uses `references/scene_<name>.png` as the visual contract.
- FAQ (EN + zh) — per-scene visual reference target corrected to `references/scene_<name>.png`; runtime frame capture path documented separately.
- Active terminology converged on the role-based model — "Stage 1b/4" and "orchestrator" removed from hooks, skills, templates, agents, and tests. Historical references in changelog/glossary/FAQ explanations are kept on purpose.
- README first-run flow (EN + zh) — entry command is `/gm-scaffold`, with `/gm-gdd` as the per-milestone follow-up.
- `docs/update/release-checklist.md` — new step 5 covering five cross-layer consistency gates.
- `templates/TOC.md` — replaced legacy "Stage Execution Records" placeholders with real "Pipeline Records" artifacts.
- `tests/test_agents.py` drops the PyYAML runtime dependency.
- CI workflows bumped to `actions/checkout@v6` and `actions/setup-python@v6` (Node 24).

### Fixed

- Hook docstrings, comments, and user-visible block messages no longer say "orchestrator" — `check_file_permissions.py`, `session_start.py`, `stage_reminder.py`, `metrics/highlights.py`, `metrics/schema.py`.
- `_shared/manifest.json` sanity checks in `check_stage_prerequisites.py` and `stage_reminder.py` now raise `RuntimeError` instead of `assert` (survives `python -O`).
- All `.godotmaker/verify_result.json` references removed from skills and wiki — that file was documented but never produced.

### Removed

- `templates/TOC.md` "Stage Execution Records" rows (STAGE_3 through STAGE_8).

## [0.2.1] — 2026-04-28

### Added

- New `gdd-auditor` sub-agent — independent reviewer that audits a draft GDD against a 9-category checklist and returns 5-8 high-impact follow-up questions per pass. Read-only.
- `tests/test_agents.py` — frontmatter validation for `agents/*.md` (parses, required fields, name matches filename, valid model alias).

### Changed

- `game-planner` now runs two fixed audit rounds (Rounds 6-7) after synthesizing the GDD draft and before showing it to the user. Each round dispatches the new `gdd-auditor` with a fresh context; Round 7 explicitly populates the auditor's `Previously Asked` field to avoid repeats.
- Wiki (EN + zh) updated to document the new agent — `core-skills.md` and `codebase-guide.md` (new `agents/` section enumerating all 5 sub-agents).

## [0.2.0] — 2026-04-27

### Added

- Shared reference docs mechanism (`skills/core/_shared/`) deployed via `publish_shared_refs()` into each consumer skill's `references/` (auto-generated, single source of truth).
- Per-scene visual targets — `/gm-asset` generates `references/scene_*.png`; `/gm-evaluate` compares running screenshots against them via the `visual-qa` skill (Static / Dynamic templates, frame sequences under `e2e/screenshots/scene_{name}/frame_*.png`).

### Changed

- Pipeline split into 9 role-based skills (`gm-scaffold` → `gm-gdd` → `gm-asset` → `gm-build` → `gm-verify` → `gm-evaluate` → `gm-fixgap` → `gm-accept` → `gm-finalize`). `.godotmaker/current_role` file lock enforces per-role write scope at hook level. Stage transitions recorded in `.godotmaker/stage.jsonl` (was `stage.json`).
- Hooks rewritten for the role model — `check_stage_prerequisites.py` uses `PREREQ_ROLE`; `stage_reminder.py` validates per-role outputs from `config/stage_schemas.json`; `on_subagent_stop.py` serialises `log_subagent` + `check_worker_report` to avoid race on `metrics_current.jsonl`.
- Wiki rewritten end-user-facing — 28 pages across 8 sections (getting-started, concepts, skills, troubleshooting, tools, configuration, contributing, reference). `mkdocs.yml` nav and landing page synced.

### Fixed

- Cleared 24 ruff lint errors across `hooks/`, `tools/`, `tests/` and a real `NameError` in `tools/rembg_matting.py` (`bg_color` referenced before assignment in `--preview` branch).
- Aligned `pyproject.toml` version with `VERSION` file.

### Removed

- `harness/` code and docs migrated out into the separate `external automation host` repository.

## [0.1.0] — 2026-04-26

Initial public release.

- 8-stage orchestrator pipeline with hook-enforced gates (requirements → architecture → scaffold → assets → risk impl → main impl → integration → final)
- Worker / verifier / reviewer / analyst subagent dispatch with format-validated reports
- 13 core skills (orchestrator, godot-api, headless-build, gdunit-driver, gdtoolkit, gecs, game-planner, project-scaffold, visual-qa, screenshot, mcp-driver, godot-e2e, input-mapper) and 8 reviewer skills (physics, animation, ui, tilemap, navigation, shader, audio, particles)
- 8 hooks: file permission enforcement, stage prerequisite gating, completion checks, subagent report validation, session bookkeeping, anti-deadloop protection, worktree-aware file resolution
- `tools/publish.py` deploys the framework into a target Godot project, with version tracking and upgrade prompts
- Static checks: `check_project.py` for project completeness, `check_classname.py` for Godot built-in collisions
- Asset pipeline helpers (`asset_gen.py`, `rembg_matting.py`, `tripo3d.py`)
- Wiki documentation (30 pages across 8 sections)
- 193+ unit tests for hooks and tools
