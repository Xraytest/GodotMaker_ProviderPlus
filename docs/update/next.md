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

- `config/addon_versions.json` — Godot 4.5 entry's `godot-e2e` tag bumped from `v1.1.0` to `v1.2.0`. Godot 4.3 and 4.4 stay on `v1.1.0`.
- `tools/check_env.py` — Godot minimum is now 4.5 (was 4.4) so the diagnostic matches the project's recommended target. Older Godots produce a clear "too old" failure rather than a quiet warning.
- Wiki + README (EN + zh) — installation / faq / check-env / development-setup / addon-versions all recommend Godot 4.5+. README keeps a "(recommended; 4.3/4.4 still supported)" softener since `addon_versions.json` still pins the older addon line for those Godot versions.

## Fixed

- `hooks/check_file_permissions.py:_is_project_root_assets_md` — switched `os.path.abspath` to `os.path.realpath` so symlinked temp directories on macOS (`/var/folders/...` → `/private/var/folders/...`) no longer skew the comparison and reject legitimately project-root ASSETS.md writes. Bug pre-existed since 0.2.x; the new macOS CI matrix surfaced it.
- `tests/tools/test_migration_introduce_tag_based_pipeline.py` — drop unused `os` import flagged by pre-push ruff (the project's pre-commit doesn't run ruff; only pre-push does).

## Removed
