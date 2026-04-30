# Release Checklist

Steps to follow when publishing a new version of GodotMaker.

## Pre-release

1. **Finalize `docs/update/next.md`**
   - Review all entries, fix typos, group by category
   - Rename `next.md` to `vX.Y.Z.md` (e.g., `v0.5.0.md`) as a permanent archive
   - Create a new empty `next.md` by copying `next.template.md`
   ```bash
   cd docs/update
   mv next.md vX.Y.Z.md
   cp next.template.md next.md
   ```

2. **Check migration scripts** (any bump level — applied tracking is decoupled from the version)
   - If this release rewrites files inside existing target projects (moved
     paths, renamed config keys, hook fix-ups, etc.), scaffold a migration:
     ```bash
     python tools/migrate.py --new <slug>
     # writes migrations/<utc-timestamp>_<slug>.py
     ```
   - Test migrations against a real target project:
     ```bash
     python tools/migrate.py /path/to/test-project
     ```
   - See `migrations/README.md` for script format and the applied-tracking model
   - **MAJOR bump:** old migration scripts are NOT deleted at release time.
     The timestamp series is monotonic and global; existing scripts stay on
     disk as historical record. MAJOR upgrades use `--force` full rebuild,
     and `baseline_applied()` re-marks every current migration as applied
     after re-deploy.
   - **Recommended — release that introduces applied-tracking machinery.**
     The release that *first* ships the applied-tracking subsystem (see
     `migrations/README.md` Transition note) should ship with `migrations/`
     **empty**. That way legacy targets reach the bootstrap branch and
     emerge as "tracked, zero applied", and the next release that ships
     V files just goes through the normal pending path. **This is the
     preferred path.** If V files do ship in the same release as the
     machinery, legacy users will hit `LegacyTargetWithMigrationsError`
     on first contact and have to pick a recovery path manually
     (`--baseline` if their project is already on the latest format,
     or manually creating an empty tracker if the V files actually need
     to run) — supported but a worse user experience than the
     empty-migrations rollout. (Note: `publish --force` is NOT a
     recovery option for non-MAJOR upgrades; the cleanup loop only
     runs on MAJOR.) Once
     applied-tracking is in any released version, this guidance no
     longer applies — drop it from your release notes for that release.

3. **Update version numbers**
   - `pyproject.toml` — update `version = "X.Y.Z"`
   - `CHANGELOG.md` — add a new `## [X.Y.Z] — YYYY-MM-DD` section with entries from the archived `next.md`

4. **Run all tests locally**
   ```bash
   pytest --tb=short
   gitleaks detect --source . --config .gitleaks.toml
   ```

5. **Cross-layer consistency gates** — these catch the contract drifts that
   shipped past previous releases. Run before tagging.

   - **README + wiki entry-flow consistency.** The first command shown in
     `README.md`, `README.zh-CN.md`, and `docs/wiki/01-getting-started/first-game.md`
     must match. For a new project this is `/gm-scaffold`; `/gm-gdd` is the
     entry only when starting a new milestone on an existing project.
   - **New config keys are in `config.yaml.default`.** Any `*_model` field
     newly referenced by a skill must also be declared in
     `config/config.yaml.default` with the same default value. The automated
     check is `tests/test_config_consistency.py`; if you add a new
     `<role>_model`, run pytest before tagging.
   - **Documented artifacts match real outputs.** If a wiki page or skill
     description claims a role produces a file (e.g., `.godotmaker/foo.json`),
     either the role's `SKILL.md` actually writes that file or the doc claim
     is removed. There is no "documented but not produced" file in the
     pipeline.
   - **Release notes are visible.** Every new `docs/update/vX.Y.Z.md` must
     appear under the `Release Notes` section of `mkdocs.yml`. Adding the
     archive without the nav entry hides it from the published site.
   - **Chinese release-note policy.** Release notes under `docs/update/` are
     **English-only by design** — the i18n plugin shows the same English
     page on the Chinese site rather than maintaining a parallel translation
     track. If this policy ever changes, mirror notes under `docs/zh/update/`
     and update this checklist.

6. **Commit and push**
   ```bash
   git add -A
   git commit -m "chore: prepare release vX.Y.Z"
   git push origin main
   ```

## Publish

7. **Create a git tag and push**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
   This triggers the `release.yml` workflow, which automatically:
   - Reads release notes from `docs/update/vX.Y.Z.md`
   - Creates a GitHub Release (source code archives are attached by GitHub)

8. **Verify the release**
   - Check the [Releases page](https://github.com/RandallLiuXin/GodotMaker/releases)
   - Verify release notes match `CHANGELOG.md`

## Post-release

9. **Announce** (optional)
   - Post on relevant communities (Godot forums, Reddit, etc.)
