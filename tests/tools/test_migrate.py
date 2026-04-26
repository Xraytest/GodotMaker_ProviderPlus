"""Tests for migrate.py and migrations/_helpers.py."""
import os
import subprocess
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools",
))

from _version import SemVer
from migrate import (
    find_migration_chain,
    collect_scripts,
    run_migration_script,
    run_migrations,
    MIGRATIONS_DIR,
)


# ---------------------------------------------------------------------------
# find_migration_chain
# ---------------------------------------------------------------------------

class TestFindMigrationChain:
    def test_same_minor_returns_empty(self):
        chain = find_migration_chain(SemVer(0, 4, 0), SemVer(0, 4, 1))
        assert chain == []

    def test_major_mismatch_returns_empty(self):
        chain = find_migration_chain(SemVer(0, 3, 0), SemVer(1, 0, 0))
        assert chain == []

    def test_downgrade_returns_empty(self):
        chain = find_migration_chain(SemVer(0, 5, 0), SemVer(0, 3, 0))
        assert chain == []

    def test_skips_missing_directory(self):
        """A version pair with no migration directory returns empty."""
        chain = find_migration_chain(SemVer(0, 4, 0), SemVer(0, 5, 0))
        assert chain == []

    def test_chain_with_synthetic_dirs(self, tmp_path, monkeypatch):
        """Create fake migration dirs and verify chain ordering."""
        for name in ["0.2_to_0.3", "0.3_to_0.4", "0.4_to_0.5"]:
            (tmp_path / name).mkdir()
        monkeypatch.setattr("migrate.MIGRATIONS_DIR", tmp_path)

        chain = find_migration_chain(SemVer(0, 2, 0), SemVer(0, 5, 0))
        assert len(chain) == 3
        assert [d.name for d in chain] == ["0.2_to_0.3", "0.3_to_0.4", "0.4_to_0.5"]


# ---------------------------------------------------------------------------
# collect_scripts
# ---------------------------------------------------------------------------

class TestCollectScripts:
    def test_collects_py_files_sorted(self, tmp_path):
        (tmp_path / "002_second.py").write_text("pass")
        (tmp_path / "001_first.py").write_text("pass")
        (tmp_path / "README.md").write_text("# doc")
        scripts = collect_scripts(tmp_path)
        assert [s.name for s in scripts] == ["001_first.py", "002_second.py"]

    def test_excludes_init(self, tmp_path):
        (tmp_path / "__init__.py").write_text("")
        (tmp_path / "001_real.py").write_text("pass")
        scripts = collect_scripts(tmp_path)
        assert [s.name for s in scripts] == ["001_real.py"]

    def test_empty_dir(self, tmp_path):
        assert collect_scripts(tmp_path) == []


# ---------------------------------------------------------------------------
# run_migration_script
# ---------------------------------------------------------------------------

class TestRunMigrationScript:
    def test_successful_script(self, tmp_path):
        marker = tmp_path / "target" / "migrated.txt"
        marker.parent.mkdir()
        script = tmp_path / "001_test.py"
        script.write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                (target / "migrated.txt").write_text("done")
        """))
        assert run_migration_script(script, marker.parent) is True
        assert marker.read_text() == "done"

    def test_script_without_migrate_function(self, tmp_path):
        script = tmp_path / "bad.py"
        script.write_text("x = 1\n")
        assert run_migration_script(script, tmp_path) is False

    def test_script_that_raises(self, tmp_path):
        script = tmp_path / "fail.py"
        script.write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                raise RuntimeError("intentional failure")
        """))
        assert run_migration_script(script, tmp_path) is False


# ---------------------------------------------------------------------------
# run_migrations (integration)
# ---------------------------------------------------------------------------

class TestRunMigrations:
    def test_major_upgrade_returns_false(self, tmp_path):
        assert run_migrations(tmp_path, SemVer(0, 3, 0), SemVer(1, 0, 0)) is False

    def test_no_chain_returns_true(self, tmp_path, monkeypatch):
        """No migration dirs → succeeds with nothing to do."""
        monkeypatch.setattr("migrate.MIGRATIONS_DIR", tmp_path)
        assert run_migrations(tmp_path, SemVer(0, 4, 0), SemVer(0, 5, 0)) is True

    def test_runs_scripts_in_order(self, tmp_path, monkeypatch):
        """Create two migration steps, verify both run in order."""
        migrations = tmp_path / "migrations"
        step1 = migrations / "0.3_to_0.4"
        step1.mkdir(parents=True)
        (step1 / "001_first.py").write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                log = target / "log.txt"
                log.write_text(log.read_text() + "step1\\n" if log.exists() else "step1\\n")
        """))

        step2 = migrations / "0.4_to_0.5"
        step2.mkdir()
        (step2 / "001_second.py").write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                log = target / "log.txt"
                log.write_text(log.read_text() + "step2\\n" if log.exists() else "step2\\n")
        """))

        monkeypatch.setattr("migrate.MIGRATIONS_DIR", migrations)

        target = tmp_path / "project"
        target.mkdir()
        assert run_migrations(target, SemVer(0, 3, 0), SemVer(0, 5, 0)) is True

        log = (target / "log.txt").read_text()
        assert log == "step1\nstep2\n"

    def test_aborts_on_failure(self, tmp_path, monkeypatch):
        """If a script fails, chain aborts and returns False."""
        migrations = tmp_path / "migrations"
        step = migrations / "0.3_to_0.4"
        step.mkdir(parents=True)
        (step / "001_ok.py").write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                (target / "ok.txt").write_text("ok")
        """))
        (step / "002_fail.py").write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                raise RuntimeError("boom")
        """))

        monkeypatch.setattr("migrate.MIGRATIONS_DIR", migrations)

        target = tmp_path / "project"
        target.mkdir()
        assert run_migrations(target, SemVer(0, 3, 0), SemVer(0, 4, 0)) is False
        # First script ran successfully
        assert (target / "ok.txt").exists()

    def test_patch_only_no_migration(self, tmp_path, monkeypatch):
        """Patch bump (same minor) should not run any migrations."""
        migrations = tmp_path / "migrations"
        step = migrations / "0.4_to_0.5"
        step.mkdir(parents=True)
        (step / "001_test.py").write_text(textwrap.dedent("""\
            from pathlib import Path
            def migrate(target: Path) -> None:
                (target / "should_not_exist.txt").write_text("bad")
        """))

        monkeypatch.setattr("migrate.MIGRATIONS_DIR", migrations)

        target = tmp_path / "project"
        target.mkdir()
        # 0.4.0 → 0.4.1 is PATCH — same minor, no migration
        assert run_migrations(target, SemVer(0, 4, 0), SemVer(0, 4, 1)) is True
        assert not (target / "should_not_exist.txt").exists()


# ---------------------------------------------------------------------------
# ensure_git_tracked (_helpers.py)
# ---------------------------------------------------------------------------

class TestEnsureGitTracked:
    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a temp git repo."""
        subprocess.run(["git", "init"], cwd=str(tmp_path),
                       capture_output=True, timeout=10)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                       cwd=str(tmp_path), capture_output=True, timeout=10)
        subprocess.run(["git", "config", "user.name", "Test"],
                       cwd=str(tmp_path), capture_output=True, timeout=10)
        return tmp_path

    def _import_helper(self):
        """Import ensure_git_tracked from migrations/_helpers.py."""
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "migrations",
        )
        if migrations_dir not in sys.path:
            sys.path.insert(0, migrations_dir)
        from _helpers import ensure_git_tracked
        return ensure_git_tracked

    def test_skips_nonexistent_path(self, tmp_path, capsys):
        ensure = self._import_helper()
        ensure(tmp_path, "no/such/path", "test")
        assert "[skip]" in capsys.readouterr().out

    def test_adds_existing_path(self, git_repo, capsys):
        ensure = self._import_helper()
        d = git_repo / ".godotmaker" / "hooks"
        d.mkdir(parents=True)
        (d / "test.py").write_text("pass")
        ensure(git_repo, ".godotmaker/hooks/", ".godotmaker/hooks/")
        out = capsys.readouterr().out
        assert "[done]" in out

    def test_idempotent(self, git_repo, capsys):
        """Running twice on the same path should succeed both times."""
        ensure = self._import_helper()
        f = git_repo / "test.txt"
        f.write_text("hello")
        ensure(git_repo, "test.txt", "test.txt")
        ensure(git_repo, "test.txt", "test.txt")
        out = capsys.readouterr().out
        assert out.count("[done]") == 2


# ---------------------------------------------------------------------------
# check_version_upgrade (VersionCheckResult)
# ---------------------------------------------------------------------------

class TestCheckVersionUpgrade:
    """Test that check_version_upgrade returns VersionCheckResult correctly."""

    def _setup_versions(self, tmp_path, source_ver, target_ver=None):
        """Create repo with VERSION file and optionally a target with version."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "VERSION").write_text(source_ver)
        (repo / "CHANGELOG.md").write_text("# Changelog\n")

        target = tmp_path / "target"
        target.mkdir()
        if target_ver:
            gm = target / ".godotmaker"
            gm.mkdir()
            (gm / "version").write_text(target_ver)

        return repo, target

    def test_fresh_install(self, tmp_path):
        from publish import check_version_upgrade, VersionCheckResult
        repo, target = self._setup_versions(tmp_path, "0.4.0")
        result = check_version_upgrade(repo, target, force=False)
        assert isinstance(result, VersionCheckResult)
        assert result.proceed is True
        assert result.level == "FRESH"
        assert result.target_ver is None

    def test_same_version(self, tmp_path):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.4.0", "0.4.0")
        result = check_version_upgrade(repo, target, force=False)
        assert result.proceed is True
        assert result.level == "SAME"

    def test_patch_upgrade(self, tmp_path):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.4.1", "0.4.0")
        result = check_version_upgrade(repo, target, force=False)
        assert result.proceed is True
        assert result.level == "PATCH"

    def test_minor_upgrade_without_force_prompts(self, tmp_path, monkeypatch):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.5.0", "0.4.0")
        monkeypatch.setattr("builtins.input", lambda _: "y")
        result = check_version_upgrade(repo, target, force=False)
        assert result.proceed is True
        assert result.level == "MINOR"

    def test_minor_upgrade_declined(self, tmp_path, monkeypatch):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.5.0", "0.4.0")
        monkeypatch.setattr("builtins.input", lambda _: "n")
        result = check_version_upgrade(repo, target, force=False)
        assert result.proceed is False
        assert result.level == "MINOR"

    def test_minor_upgrade_with_force(self, tmp_path):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.5.0", "0.4.0")
        result = check_version_upgrade(repo, target, force=True)
        assert result.proceed is True
        assert result.level == "MINOR"

    def test_major_upgrade_without_force_prompts(self, tmp_path, monkeypatch):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "1.0.0", "0.4.0")
        monkeypatch.setattr("builtins.input", lambda _: "n")
        result = check_version_upgrade(repo, target, force=False)
        assert result.proceed is False
        assert result.level == "MAJOR"

    def test_major_upgrade_with_force(self, tmp_path):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "1.0.0", "0.4.0")
        result = check_version_upgrade(repo, target, force=True)
        assert result.proceed is True
        assert result.level == "MAJOR"

    def test_downgrade_blocked(self, tmp_path):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.3.0", "0.4.0")
        result = check_version_upgrade(repo, target, force=False)
        assert result.proceed is False
        assert result.level == "DOWNGRADE"

    def test_downgrade_with_force(self, tmp_path):
        from publish import check_version_upgrade
        repo, target = self._setup_versions(tmp_path, "0.3.0", "0.4.0")
        result = check_version_upgrade(repo, target, force=True)
        assert result.proceed is True
        assert result.level == "DOWNGRADE"
