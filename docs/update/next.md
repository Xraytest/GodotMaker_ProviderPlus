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

- Shared reference docs mechanism (`skills/core/_shared/`) — cross-skill reference docs (`worker-dispatch.md`, `verifier-dispatch.md`, `reviewer-dispatch.md`, `analyst-dispatch.md`) live as a single source of truth and are reverse-deployed by `publish_shared_refs()` into each consumer's `references/` with an `<!-- AUTO-GENERATED -->` header. Schema and authoring rules in `docs/contributing/shared-refs.md`.
- Per-scene visual targets — `/gm-asset` Step 3 generates `references/scene_*.png` per `SCENES.md` entry; `/gm-evaluate` Phase 3 invokes the `visual-qa` skill with Static / Dynamic templates to compare running screenshots against these targets. Frame sequences for animated scenes live under per-scene subdirs `e2e/screenshots/scene_{name}/frame_*.png`.

## Changed

- Pipeline split into 9 role-based skills — replaced the monolithic `/orchestrator` skill with `/gm-scaffold`, `/gm-gdd`, `/gm-asset`, `/gm-build`, `/gm-verify`, `/gm-evaluate`, `/gm-fixgap`, `/gm-accept`, `/gm-finalize`. Each role owns a single phase and a write-permission scope; `.godotmaker/current_role` enforces the lock at hook level. Role transitions are recorded in `.godotmaker/stage.jsonl` (was `stage.json`).
- Hook rewrite for the role model — `check_stage_prerequisites.py` keys off `PREREQ_ROLE` (`build` requires `gdd`; `fixgap` requires `evaluate`); `stage_reminder.py` validates per-role outputs from `config/stage_schemas.json` whose keys are role names instead of stage numbers; `on_subagent_stop.py` serialises `log_subagent` + `check_worker_report` to avoid the `metrics_current.jsonl` parallel-write race.

## Fixed

## Removed
