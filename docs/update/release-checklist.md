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

2. **Check migration scripts** (MINOR bumps only)
   - If this release changes behavior or file locations, ensure migration
     scripts exist in `migrations/{old}_to_{new}/`
   - Test migrations against a real target project:
     ```bash
     python tools/migrate.py /path/to/test-project --from X.Y.0 --to X.Z.0
     ```
   - See `migrations/README.md` for script format
   - **MAJOR bump only:** delete all migration directories from the previous
     MAJOR version (e.g., remove all `0.x_to_0.y/` dirs when releasing 1.0).
     MAJOR upgrades use `--force` full rebuild, not incremental migration.

3. **Update version numbers**
   - `pyproject.toml` — update `version = "X.Y.Z"`
   - `CHANGELOG.md` — add a new `## [X.Y.Z] — YYYY-MM-DD` section with entries from the archived `next.md`

4. **Run all tests locally**
   ```bash
   pytest --tb=short
   gitleaks detect --source . --config .gitleaks.toml
   ```

5. **Commit and push**
   ```bash
   git add -A
   git commit -m "chore: prepare release vX.Y.Z"
   git push origin main
   ```

## Publish

5. **Create a git tag and push**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
   This triggers the `release.yml` workflow, which automatically:
   - Reads release notes from `docs/update/vX.Y.Z.md`
   - Creates a GitHub Release (source code archives are attached by GitHub)

6. **Verify the release**
   - Check the [Releases page](https://github.com/RandallLiuXin/GodotMaker/releases)
   - Verify release notes match `CHANGELOG.md`

## Post-release

7. **Announce** (optional)
   - Post on relevant communities (Godot forums, Reddit, etc.)
