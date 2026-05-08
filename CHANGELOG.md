# Changelog

All notable changes to GodotMaker will be documented in this file.

Format: [Semantic Versioning](https://semver.org/) — MAJOR.MINOR.PATCH

## [0.3.3] — 2026-05-09

PATCH bump fixing a Windows-only `--force` upgrade crash that surfaced as soon as users started upgrading from baselines that had cloned `godot-docs` into `.claude/skills/godot-api/doc_source/`.

- **`PermissionError [WinError 5]` on `--force` upgrade.** `publish.py` cleared `.claude/skills/` via plain `shutil.rmtree`, which on Windows refuses to unlink read-only files. Git writes pack-`*.idx` files as `r--r--r--`, and any prior version that cloned `godot-docs` left those files behind. All three `shutil.rmtree` call sites now go through a new `rmtree_force()` helper that clears the read-only bit in the rmtree `onerror`/`onexc` hook and retries.
- **The crash had a worse downstream symptom than the error suggested.** `main()` aborted before `.godotmaker/version` was stamped, so any caller re-invoking `publish.py` on `installed_version != target_version` would re-trigger the same crash on every retry — looking like an "infinite republish" symptom from the caller's side rather than a one-off filesystem error.

No migration script is required — this is a runtime fix to `publish.py` itself; nothing about target-project layout or content changes.

### Changed

- `tools/publish.py` — added `rmtree_force()` helper and `_rmtree_handle_readonly()` onerror/onexc hook (signature compatible with Python 3.10–3.11 onerror and 3.12+ onexc). Replaced all three `shutil.rmtree(...)` call sites: `copy_tree()`, the MAJOR `--force` cleanup loop, and the `elif args.force` skills cleanup branch.
- `tests/tools/test_publish.py` — added `TestPublishMainForceRmtree` driving real `publish.main(--force)` against a target seeded with `.godotmaker/version=0.3.1` and a read-only `pack-*.idx` under `.claude/skills/godot-api/doc_source/.git/objects/pack/`. Mutation-verified: reverting the rmtree fix makes the test fail with the real `PermissionError [WinError 5]`. This branch had zero integration coverage before — `tests/tools/test_publish.py` was unit-only and the only main()-driving test (`tests/tools/test_migrate.py::TestPublishMainMigrationRouting`) seeded an empty target so the `elif args.force and skills_target.exists()` branch was never exercised. Also added `TestRmtreeForce` unit tests, with cross-platform notes in both classes' docstrings (the read-only failure is Windows-only by nature; on Linux/macOS the tests verify the helper doesn't break the normal-tree path).

### Fixed

- Windows users upgrading from any prior version that cloned `godot-docs` no longer hit `PermissionError [WinError 5]` when running `publish.py --force`. The crash previously aborted the entire publish before `.godotmaker/version` was stamped, leaving downstream version-comparing callers stuck in a re-trigger loop.

## [0.3.2] — 2026-05-08

PATCH bump rolling up two in-tag refinements to the build/fixgap loop and a small template cleanup:

- **Reviewer cycle refactor.** The mid-cycle "every ≥5 worker" verify+review trigger is gone — `gm-build` now runs ONE verify+review pass at the end of each cycle iteration after `PLAN.md` is clean, and loops back to dispatch only if the reviewer added ACCEPTED tasks. Aligns with `gm-fixgap` Step 4's existing single-pass model.
- **Three-option reviewer triage (ACCEPT / REJECT / SKIP).** Every finding regardless of severity now goes through the same three-option triage; defaults are critical/major → ACCEPT and minor → SKIP; citation is mandatory for critical/major REJECT/SKIP and optional for minor. Forbidden REJECT reasons listed explicitly. REJECT/SKIP records land in a new `MEMORY.md` "Reviewer Triage Log" section, and `/gm-accept` surfaces the current tag's triage decisions to the user as the final audit gate. Retry limit raised from 3 to 5.
- **Presentation video task removed from `templates/PLAN.md`.** The template used to ask `/gm-build` to render a ~30s cinematic MP4 to `screenshots/presentation/gameplay.mp4`; it served no verification purpose (visual-qa already covers everything via `e2e/screenshots/` PNG frame sequences) and the unexplained recording confused users.

No migration script is required — the new shared reference doc is deployed automatically by `publish_shared_refs()` on next publish; template changes only affect freshly-generated PLAN/MEMORY (existing per-tag files are not rewritten).

### Added

- `skills/core/_shared/reviewer-finding-triage.md` — New shared reference doc defining the **ACCEPT / REJECT / SKIP** triage rules for every reviewer finding regardless of severity. Defaults: critical/major → ACCEPT; minor → SKIP. Citation is mandatory for critical/major REJECT/SKIP and optional for minor. Forbidden reject reasons listed explicitly. Deployed to `gm-build` and `gm-fixgap` via the manifest.
- `skills/core/gm-accept/SKILL.md` — "Reviewer Triage Decisions for This Tag" table added to the user-facing tag summary (with a Decision column for REJECT vs SKIP); user is the final gate on whether the agent's triage was justified.
- `templates/MEMORY.md` — New "Reviewer Triage Log" section between Workarounds and Component Design Decisions. Records every REJECT and SKIP with finding/severity/decision/reason/citation. Cross-tag accumulating audit trail.
- `tests/test_reviewer_finding_triage.py` — Structural regression gate that locks in the three-option model, severity-conditional citation requirement, and the forbidden-reasons list against silent weakening.

### Changed

- `skills/core/gm-build/SKILL.md` — Mid-cycle "every ≥5 worker" verify+review trigger removed. New Step 2 "Verify + Review Pass" runs once per cycle iteration after `PLAN.md` is clean and loops back to dispatch if the reviewer added ACCEPTED tasks. Hard Rule 5/6 reworded; reviewer subsection now uses the three-option triage. Retry limit raised from 3 to 5.
- `skills/core/gm-fixgap/SKILL.md` — Step 4 reviewer subsection now uses the three-option triage (ACCEPT / REJECT / SKIP per `references/reviewer-finding-triage.md`). Hard Rule 6 reworded. Retry limit raised from 3 to 5.
- `skills/core/_shared/reviewer-dispatch.md` — Outdated "every completed worker task" wording fixed; new "Handling the Reviewer's Report" section describes the three-option triage and points to the triage doc.
- Wiki (EN + zh) — `02-concepts/the-9-roles.md`, `02-concepts/how-it-works.md`, `03-skills/reviewer-skills.md`, `07-contributing/writing-a-skill.md`, `08-reference/faq.md`, `08-reference/glossary.md` updated to describe the new "PLAN clean → one verify+review pass → ACCEPT/REJECT/SKIP triage" model.

### Removed

- `templates/PLAN.md` — "Presentation video" task removed. The template used to ask `/gm-build` to write `test/Presentation.gd` and render a ~30s cinematic MP4 to `screenshots/presentation/gameplay.mp4`; the file served no verification purpose (visual-qa uses `e2e/screenshots/` PNG frames) and confused users who saw an unexplained recording appear in their project. Both the Verify-list bullet and the `| V | Presentation video |` Task Status row are gone.

## [0.3.1] — 2026-05-08

PATCH bump rolling up:

- a macOS-only path-comparison fix that the new macOS CI matrix surfaced
  (asset-permission hook compared `/var/...` against `/private/var/...`
  on tempdir-based tests and rejected legitimate writes — pre-existed
  since 0.2.x);
- a pre-push lint cleanup;
- a `godot-e2e` pinning bump to v1.2.0 for Godot 4.5+ (4.3 and 4.4 stay
  on v1.1.0); plus wiki + README realignment recommending Godot 4.5+
  as the project's main target.

### Changed

- `config/addon_versions.json` — Godot 4.5 entry's `godot-e2e` tag bumped from `v1.1.0` to `v1.2.0`. Godot 4.3 and 4.4 stay on `v1.1.0`.
- `tools/check_env.py` — Godot minimum is now 4.5 (was 4.4) so the diagnostic matches the project's recommended target. Older Godots produce a clear "too old" failure rather than a quiet warning.
- Wiki + README (EN + zh) — installation / faq / check-env / development-setup / addon-versions all recommend Godot 4.5+. README keeps a "(recommended; 4.3/4.4 still supported)" softener since `addon_versions.json` still pins the older addon line for those Godot versions.

### Fixed

- `hooks/check_file_permissions.py:_is_project_root_assets_md` — switched `os.path.abspath` to `os.path.realpath` so symlinked temp directories on macOS (`/var/folders/...` → `/private/var/folders/...`) no longer skew the comparison and reject legitimately project-root ASSETS.md writes. Bug pre-existed since 0.2.x; the new macOS CI matrix surfaced it.
- `tests/tools/test_migration_introduce_tag_based_pipeline.py` — drop unused `os` import flagged by pre-push ruff (the project's pre-commit doesn't run ruff; only pre-push does).

## [0.3.0] — 2026-05-07

MINOR bump combining two co-landing changes: the **tag-iterative
pipeline** (each `/gm-gdd → /gm-finalize` round ships ONE SemVer
tag) and the **`verify_report.json` feedback channel** (closes the
retry loop where verify failures had no machine-readable signal to
drive the next iteration).

Existing projects upgrade via
`migrations/20260507120000_introduce_tag_based_pipeline.py`, which
moves the pre-existing GDD/PLAN/STRUCTURE/SCENES/ASSETS into
`docs/tags/v0.1.0/` and writes a stub `ROADMAP.md`. The migration is
idempotent and runs automatically on the first publish after upgrade.
The verify-report side is fully additive on the state side and ships
no migration of its own — see the upgrade note below for the SKILL
redeploy step.

### Added

#### Tag-iterative pipeline
- Tag-iterative pipeline (`ROADMAP.md` + `docs/tags/<Tag>/` archives + `git tag <Tag>` per round). The earliest entry in `ROADMAP.md` without a corresponding `git tag` is the **current tag**; per-tag root docs (`PLAN.md`, `STRUCTURE.md`, `SCENES.md`) are scoped to it, while `GDD.md`, `ROADMAP.md`, `MEMORY.md`, and `ASSETS.md` accumulate across tags (ASSETS rows carry a `Tag` column marking the introducing tag).
- Playable-closed-loop hard gate in `/gm-evaluate`: every tag must boot `godot --headless --quit`, run at least one core mechanic E2E, and have at least one of {death, win, exit} reachable. The single `e2e/` suite runs every still-supported mechanic on every evaluation; any failing inherited mechanic blocks approval.
- `/gm-rescue` diagnostic skill (`skills/core/gm-rescue/`) — outside the main pipeline. Reads runtime artifacts, walks godotmaker layers (hooks → SKILL.md → config → templates → shared refs → tools), determines whether a framework defect is the cause; outputs to chat ONLY (no file writes, no code changes), drafts a GitHub issue text the user reviews and posts upstream. Privacy default: drafts exclude absolute project paths, project source code, and GDD content.
- Migration script (`migrations/20260507120000_introduce_tag_based_pipeline.py`) for upgrading existing projects to the new layout. Idempotent; does NOT auto-`git tag`.
- `templates/ROADMAP.md` template with SemVer convention header. PLAN.md / STRUCTURE.md / SCENES.md templates gain `**Tag:** vX.Y.Z` headers (ASSETS.md and MEMORY.md stay cross-tag — ASSETS gains a `Tag` column, MEMORY is snapshotted). PLAN.md adds `Tag Mechanics` and `Inherited Mechanics` sections; `/gm-evaluate` reads them to maintain the single `e2e/` suite.
- `hooks/stage_reminder.py` `check_tag_archived` programmatic check; `hooks/metrics/get_current_tag()` helper; SessionStart banner now surfaces the current tag (or "no current tag — run /gm-gdd to start one").
- 38 new tests covering migration / hooks / metrics / `gm-rescue` structural contract.

#### Verify-report feedback channel
- **`.godotmaker/verify_report.json` — structured feedback channel from `/gm-verify` to `/gm-build` and `/gm-fixgap`.** `/gm-verify` now writes this file on every run (PASS or FAIL) with per-check results: `checks.build.errors[]`, `checks.unit_tests.failures[]`, `checks.lint.{issues, format_drift}`, `checks.static_check.issues[]`, plus `tooling_notes[]` for verification-tool crashes (gdlint / gdformat / godot etc.) carrying a `suggested_fallback` discriminator (`exclude_file` / `scope_narrow` / `add_gdlintrc_rule` / `skip_check` / `escalate`) and a matching structured operand (`crashed_on` / `narrowed_command` / `rule_name` / `check_name`) so consumers can apply the fix deterministically without parsing free-text `error` strings. Per-check `result` is a 4-value enum `pass | warn | fail | error` — `error` distinguishes "tool crashed, project status unknown" (consumer applies a config fallback) from `fail` "project has problems" (consumer dispatches a code fix). On their next invocation, `/gm-build` and `/gm-fixgap` Resume Checks read this report — when its `ts` is newer than the last `build`/`fixgap` event in `stage.jsonl` and overall `result == "fail"`, they translate each failure into pending PLAN.md / GAP.md tasks before resuming. Producers that cannot fill the required operand for a non-`escalate` fallback MUST emit `escalate` instead; consumers that see a non-`escalate` fallback with a missing operand MUST degrade to `escalate`. This closes the retry loop where verify failures had no machine-readable channel to drive the next iteration.
- `gm-verify` SKILL.md "Output Format" split into A. chat-readable report and B. machine-readable JSON, with the full schema documented inline. Permission section adds `verify_report.json` as a third write exception alongside `current_role` and `stage.jsonl`.
- `gm-build` SKILL.md "Step 0 — Process Verify Feedback" — runs only when Resume Check flags a fresh `verify_report.json`; per-check translation rules cover compile errors, test failures, lint issues, format drift, static-check issues, and tooling-note fallbacks (config-only fixes, never code deletions).
- `gm-fixgap` SKILL.md "Step 1b — Pull failures from `verify_report.json`" — same translation rules as gm-build. Verify-source tasks share the existing `C` / `J` severity prefixes with evaluation-source tasks but are listed first within each letter so the mechanical layer is fixed before product-layer fixes are dispatched. Per-task `Source: verify_report.json | evaluation.json` line records origin.
- `templates/GAP.md` — adds optional `Source Verify` header section, per-task `Source:` line, and a `Source` column in the Task Status table.
- Wiki — `common-problems.md` (EN + zh) adds "`/gm-verify` keeps failing on the same issues and `/gm-build` retries forever" diagnostic with the three failure modes (missing report, stale report, old SKILL.md deployed) and step-by-step fixes.

### Changed

#### Tag-iterative pipeline
- `/gm-gdd` rewritten with initial vs subsequent mode (auto-detected by `ROADMAP.md` presence). Initial: full Socratic interview → derives ROADMAP → mandatory user confirmation gate → writes v0.1.0 docs. Subsequent: focuses earliest un-git-tagged ROADMAP entry, optionally updates `GDD.md` (old features marked `(superseded by …)` instead of deleted) and `ROADMAP.md`, generates this tag's working docs with explicit refactor tasks for cross-tag changes.
- `/gm-finalize` drops release packaging entirely (deferred to a future release skill). New responsibilities: archive working docs to `docs/tags/<Tag>/`, generate per-tag CHANGELOG, run `git tag <Tag>` locally (does NOT push), reset per-tag runtime state.
- `/gm-evaluate` maintains a single `e2e/` suite that always reflects the current game (adds tests for new Tag Mechanics, prunes tests for mechanics removed by an explicit Main Build refactor task); `evaluation.json` schema gains `tag`, `tag_mechanics`, `inherited_mechanics`, `e2e_tests`, and `orphan_tests`.
- Per-tag scope discipline enforced across `/gm-build`, `/gm-fixgap`, `/gm-asset`, `/gm-accept`. Workers may touch files from previous tags only when PLAN.md has an explicit refactor task naming those files; "cleanup detours" are forbidden.
- Decomposer agent rewritten to consume GDD + ROADMAP + prior tag archives + cross-tag refactor hints; overwrites per-tag root artifacts with `**Tag:**` headers; never modifies GDD/ROADMAP/archives; supports initial / subsequent modes.
- `templates/game-claude.md` rewritten with tag-iterative flow framing and the new doc-scope rules; notes `gm-rescue`'s position outside the main flow.
- `config/stage_schemas.json`: `ROADMAP.md` added to `gdd` outputs; `finalize` gains `tag_archived` programmatic check; new no-op `rescue` stage schema.
- `hooks/check_file_permissions.py` `PLANNING_DOCS` includes `roadmap.md` so subagents (other than the decomposer) cannot mutate it.
- Wiki `the-9-roles.md` and `glossary.md` (EN + zh) updated for the tag model.

#### Verify-report feedback channel
- `config/stage_schemas.json` `verify` entry now declares `files: [".godotmaker/verify_report.json"]`. The existing `stage_reminder.py` path validator automatically blocks the `verify` completion event from being appended to `stage.jsonl` when the report file is missing — same gate mechanism as `evaluate` already uses for `evaluation.json`.
- `hooks/check_file_permissions.py` — `VERIFY_ALLOWED_GM_FILES` adds `.godotmaker/verify_report.json`. The block message lists all three allowed paths.

### Upgrade note (v0.2.x → v0.3.0)

The verify-report feedback channel only takes effect once the **deployed** SKILL.md files (under each project's `.claude/skills/`) are the v0.3.0 versions. The `tools/publish.py` upgrade flow normally handles this on a MINOR bump, but a project that was last published before v0.3.0 will keep running the old `gm-build` / `gm-fixgap` SKILLs (and the retry-loop bug the channel fixes) until you redeploy. To force a clean SKILL refresh:

```
python tools/publish.py --force <project_dir>
```

`--force` overwrites `.claude/skills/`, hooks, `stage_schemas.json`, and templates; it leaves your project state (`.godotmaker/stage.jsonl`, `evaluation.json`, `PLAN.md`, `GAP.md`, etc.) untouched.

For the tag-pipeline side, no `--force` is needed — the migration runs automatically on the first publish and is idempotent. The state side is fully additive (verify-report). The tag-pipeline migration relocates pre-existing root docs into `docs/tags/v0.1.0/` and injects `**Tag:** v0.1.0` into root `PLAN.md` so post-migration `/gm-evaluate` and `/gm-finalize` can read the current tag without first re-running `/gm-gdd`. `gm-fixgap`'s Resume Check has a per-row backward-compat clause for `GAP.md` files written under the v0.2.x format.

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
