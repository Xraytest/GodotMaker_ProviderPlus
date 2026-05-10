"""Tests for publish.py."""
import os
import stat
import subprocess
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools",
))

import publish
from publish import (
    read_godot_path,
    create_godotmaker_yaml,
    create_project_config,
    ensure_gitignore,
    ensure_worktreeinclude,
    publish_skills,
    rmtree_force,
    _verify_godot_path,
    DEFAULT_CONFIG_TEMPLATE,
)


class TestReadGodotPath:
    def test_missing_file(self, tmp_path):
        assert read_godot_path(tmp_path / "nope.yaml") == "godot"

    def test_quoted_path(self, tmp_path):
        f = tmp_path / "godotmaker.yaml"
        f.write_text('godot_path: "C:/Godot/godot.exe"\n')
        assert read_godot_path(f) == "C:/Godot/godot.exe"

    def test_unquoted_path(self, tmp_path):
        f = tmp_path / "godotmaker.yaml"
        f.write_text("godot_path: /usr/bin/godot\n")
        assert read_godot_path(f) == "/usr/bin/godot"

    def test_empty_value_returns_default(self, tmp_path):
        f = tmp_path / "godotmaker.yaml"
        f.write_text("godot_path:\n")
        assert read_godot_path(f) == "godot"

    def test_single_quoted(self, tmp_path):
        f = tmp_path / "godotmaker.yaml"
        f.write_text("godot_path: 'C:/Godot/godot.exe'\n")
        assert read_godot_path(f) == "C:/Godot/godot.exe"


def _ok_run(stdout="Godot Engine v4.4-stable\n"):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def _fail_run(returncode=1, stderr="boom"):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr=stderr)


class TestVerifyGodotPath:
    def test_returns_ok_when_godot_runs(self):
        with patch.object(publish.subprocess, "run", return_value=_ok_run()):
            ok, msg = _verify_godot_path("/fake/godot")
        assert ok is True
        assert "v4.4" in msg

    def test_returns_failure_when_executable_missing(self):
        with patch.object(publish.subprocess, "run", side_effect=FileNotFoundError):
            ok, msg = _verify_godot_path("/no/such/godot")
        assert ok is False
        assert "not found" in msg

    def test_returns_failure_when_godot_exits_nonzero(self):
        with patch.object(publish.subprocess, "run", return_value=_fail_run()):
            ok, msg = _verify_godot_path("/fake/godot")
        assert ok is False
        assert "exited" in msg

    def test_returns_failure_on_timeout(self):
        with patch.object(
            publish.subprocess, "run",
            side_effect=subprocess.TimeoutExpired(cmd="godot", timeout=15),
        ):
            ok, msg = _verify_godot_path("/slow/godot")
        assert ok is False
        assert "did not return" in msg

    def test_zero_exit_with_empty_stdout_is_accepted(self):
        """Lock-in: an executable that exits 0 but prints no version line
        is treated as 'verified' with `?` as the version. This is
        intentional — wrapper scripts (`godot.cmd`, ssh wrappers, sandbox
        runners) sometimes suppress stdout while still launching Godot
        correctly. If you ever decide to tighten this and require a
        version pattern in stdout, change this test deliberately."""
        with patch.object(publish.subprocess, "run",
                          return_value=_ok_run(stdout="")):
            ok, msg = _verify_godot_path("/silent/godot")
        assert ok is True
        assert msg == "?"

    def test_zero_exit_with_non_version_stdout_is_accepted(self):
        """Lock-in counterpart to the empty-stdout case — even non-version
        text (e.g. a wrapper banner) is currently accepted as long as the
        process returns 0."""
        with patch.object(publish.subprocess, "run",
                          return_value=_ok_run(stdout="hello world\n")):
            ok, msg = _verify_godot_path("/wrapped/godot")
        assert ok is True
        assert msg == "hello world"

    def test_returns_failure_on_oserror(self):
        """An OSError other than FileNotFoundError (e.g. PermissionError,
        OSError when the path is a directory) is the third hand-written
        exception branch in `_verify_godot_path` and must surface a
        readable message instead of crashing."""
        with patch.object(publish.subprocess, "run",
                          side_effect=PermissionError("Permission denied")):
            ok, msg = _verify_godot_path("/no/perms/godot")
        assert ok is False
        assert "cannot run" in msg
        assert "Permission denied" in msg


class TestCreateGodotmakerYaml:
    """create_godotmaker_yaml must reject empty / unverifiable paths and
    only write godotmaker.yaml when --version succeeds. The previous
    behaviour silently fell back to godot_path: 'godot' when the user
    pressed Enter, which then re-asked downstream in /gm-scaffold."""

    def test_skips_when_file_exists(self, tmp_path, capsys):
        config = tmp_path / "godotmaker.yaml"
        config.write_text('godot_path: "/existing"\n', encoding="utf-8")
        create_godotmaker_yaml(config)
        assert config.read_text(encoding="utf-8") == 'godot_path: "/existing"\n'

    def test_writes_yaml_when_path_verifies(self, tmp_path):
        config = tmp_path / "godotmaker.yaml"
        with patch("builtins.input", return_value="/usr/bin/godot"), \
             patch.object(publish.subprocess, "run", return_value=_ok_run()):
            create_godotmaker_yaml(config)
        assert config.exists()
        content = config.read_text(encoding="utf-8")
        assert 'godot_path: "/usr/bin/godot"' in content

    def test_strips_quotes_from_user_input(self, tmp_path):
        config = tmp_path / "godotmaker.yaml"
        with patch("builtins.input", return_value='"C:/Godot/godot.exe"'), \
             patch.object(publish.subprocess, "run", return_value=_ok_run()):
            create_godotmaker_yaml(config)
        assert 'godot_path: "C:/Godot/godot.exe"' in config.read_text(encoding="utf-8")

    def test_reprompts_on_empty_then_accepts_valid(self, tmp_path):
        config = tmp_path / "godotmaker.yaml"
        inputs = iter(["", "  ", "/usr/bin/godot"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)), \
             patch.object(publish.subprocess, "run", return_value=_ok_run()):
            create_godotmaker_yaml(config)
        assert config.exists(), "must accept the third valid input after two empties"

    def test_reprompts_on_invalid_then_accepts_valid(self, tmp_path):
        config = tmp_path / "godotmaker.yaml"
        inputs = iter(["/bogus/path", "/usr/bin/godot"])
        runs = iter([_fail_run(), _ok_run()])
        with patch("builtins.input", side_effect=lambda _: next(inputs)), \
             patch.object(publish.subprocess, "run", side_effect=lambda *a, **k: next(runs)):
            create_godotmaker_yaml(config)
        assert 'godot_path: "/usr/bin/godot"' in config.read_text(encoding="utf-8")

    def test_interleaved_empty_invalid_valid_within_budget(self, tmp_path):
        """Mixed retry path — empty (no subprocess call), invalid (fail),
        valid (ok). Pins that the same attempt counter governs both kinds
        of rejection, so an `empty + invalid + ...` sequence still has
        budget for a final successful attempt."""
        config = tmp_path / "godotmaker.yaml"
        inputs = iter(["", "/bogus/path", "/usr/bin/godot"])
        # `_verify_godot_path` only runs subprocess for non-empty inputs,
        # so the run side_effect lines up with the 2nd and 3rd entries.
        runs = iter([_fail_run(), _ok_run()])
        with patch("builtins.input", side_effect=lambda _: next(inputs)), \
             patch.object(publish.subprocess, "run",
                          side_effect=lambda *a, **k: next(runs)):
            create_godotmaker_yaml(config)
        assert 'godot_path: "/usr/bin/godot"' in config.read_text(encoding="utf-8")

    def test_does_not_write_when_user_aborts(self, tmp_path):
        config = tmp_path / "godotmaker.yaml"
        with patch("builtins.input", side_effect=EOFError):
            create_godotmaker_yaml(config)
        assert not config.exists(), (
            "Ctrl+D / EOF must NOT silently write a fallback path — "
            "that was the original bug. Better: leave config absent so "
            "publish can be re-run."
        )

    def test_does_not_write_when_user_sigints(self, tmp_path):
        """Sibling of test_does_not_write_when_user_aborts — Ctrl+C
        (KeyboardInterrupt) must follow the same no-fallback contract.
        The exception handler catches `(EOFError, KeyboardInterrupt)`
        as a tuple, but only the EOFError half was previously tested."""
        config = tmp_path / "godotmaker.yaml"
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            create_godotmaker_yaml(config)
        assert not config.exists()

    def test_gives_up_after_max_attempts_without_writing(self, tmp_path):
        config = tmp_path / "godotmaker.yaml"
        # 5 invalid attempts in a row → no file
        with patch("builtins.input", return_value="/bogus"), \
             patch.object(publish.subprocess, "run", return_value=_fail_run()):
            create_godotmaker_yaml(config)
        assert not config.exists()


class TestCreateProjectConfig:
    def test_creates_config_with_defaults(self, tmp_path):
        create_project_config(tmp_path)
        config = tmp_path / ".godotmaker" / "config.yaml"
        assert config.exists()
        content = config.read_text()
        assert "vqa_model: gemini-3-flash" in content

    def test_skips_if_exists(self, tmp_path):
        config_dir = tmp_path / ".godotmaker"
        config_dir.mkdir()
        config = config_dir / "config.yaml"
        config.write_text("vqa_model: custom-model\n")
        create_project_config(tmp_path)
        assert config.read_text() == "vqa_model: custom-model\n"

    def test_default_config_template_is_valid_yaml(self):
        assert DEFAULT_CONFIG_TEMPLATE.exists(), "config.yaml.default template must exist"
        content = DEFAULT_CONFIG_TEMPLATE.read_text(encoding="utf-8")
        assert "vqa_model:" in content
        assert "worker_model:" in content
        lines = [line for line in content.splitlines() if line and not line.startswith("#")]
        for line in lines:
            assert ":" in line, f"Non-comment line missing ':' — {line}"


SELECTIVE_ENTRIES = [
    ".claude/",
    ".godotmaker/state.json",
    ".godotmaker/metrics.jsonl",
    ".godotmaker/metrics_current.jsonl",
]


class TestEnsureGitignore:
    def test_creates_new_gitignore(self, tmp_path):
        ensure_gitignore(tmp_path)
        content = (tmp_path / ".gitignore").read_text()
        assert ".claude/" in content
        for entry in SELECTIVE_ENTRIES:
            assert entry in content
        # Blanket ignore must NOT be present (selective entries only)
        lines = [line.strip() for line in content.splitlines()]
        assert ".godotmaker/" not in lines

    def test_appends_missing_entries(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("*.pyc\n")
        ensure_gitignore(tmp_path)
        content = gi.read_text()
        assert "*.pyc" in content
        assert ".claude/" in content
        for entry in SELECTIVE_ENTRIES:
            assert entry in content
        # Blanket ignore must NOT be present
        lines = [line.strip() for line in content.splitlines()]
        assert ".godotmaker/" not in lines

    def test_skips_existing_selective_entries(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("\n".join(SELECTIVE_ENTRIES) + "\n")
        ensure_gitignore(tmp_path)
        content = gi.read_text()
        # Each selective entry should appear exactly once
        for entry in SELECTIVE_ENTRIES:
            assert content.count(entry) == 1

    def test_partial_missing(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text(".claude/\n")
        ensure_gitignore(tmp_path)
        content = gi.read_text()
        for entry in SELECTIVE_ENTRIES:
            assert entry in content
        assert content.count(".claude/") == 1

    def test_migration_removes_blanket_godotmaker(self, tmp_path):
        """Old .godotmaker/ blanket line is replaced by selective entries on upgrade."""
        gi = tmp_path / ".gitignore"
        gi.write_text("*.log\n.godotmaker/\n*.tmp\n")
        ensure_gitignore(tmp_path)
        content = gi.read_text()
        # Original non-godotmaker lines must be preserved
        assert "*.log" in content
        assert "*.tmp" in content
        # Blanket ignore must be gone
        lines = [line.strip() for line in content.splitlines()]
        assert ".godotmaker/" not in lines
        # Selective entries must now be present
        for entry in SELECTIVE_ENTRIES:
            assert entry in content


WORKTREEINCLUDE_ENTRIES = [".claude/", "!.claude/worktrees/"]


class TestEnsureWorktreeinclude:
    """`.worktreeinclude` carries `.claude/` (godotmaker.yaml + skills/) into
    sub-agent worktrees. Without it, sub-agents dispatched with
    `isolation: "worktree"` see only git-tracked files and miss host config.
    See https://code.claude.com/docs/en/worktrees.
    """

    def test_creates_new_file(self, tmp_path):
        ensure_worktreeinclude(tmp_path)
        wt = tmp_path / ".worktreeinclude"
        assert wt.exists()
        content = wt.read_text(encoding="utf-8")
        for entry in WORKTREEINCLUDE_ENTRIES:
            assert entry in content
        # Header should explain WHY the file exists.
        assert "worktree" in content.lower()

    def test_appends_missing_entries(self, tmp_path):
        wt = tmp_path / ".worktreeinclude"
        wt.write_text("# user-managed\nsome/custom/path\n", encoding="utf-8")
        ensure_worktreeinclude(tmp_path)
        content = wt.read_text(encoding="utf-8")
        # User content preserved
        assert "some/custom/path" in content
        assert "# user-managed" in content
        # Required entries appended
        for entry in WORKTREEINCLUDE_ENTRIES:
            assert entry in content

    def test_idempotent_when_already_present(self, tmp_path):
        wt = tmp_path / ".worktreeinclude"
        wt.write_text("\n".join(WORKTREEINCLUDE_ENTRIES) + "\n",
                      encoding="utf-8")
        ensure_worktreeinclude(tmp_path)
        content = wt.read_text(encoding="utf-8")
        # Each entry appears exactly once as a standalone line.
        # (substring count would double-count: ".claude/" is a substring
        # of "!.claude/worktrees/".)
        lines = [line.strip() for line in content.splitlines()]
        for entry in WORKTREEINCLUDE_ENTRIES:
            assert lines.count(entry) == 1

    def test_partial_missing(self, tmp_path):
        wt = tmp_path / ".worktreeinclude"
        wt.write_text(".claude/\n", encoding="utf-8")
        ensure_worktreeinclude(tmp_path)
        content = wt.read_text(encoding="utf-8")
        lines = [line.strip() for line in content.splitlines()]
        # The negation entry was missing; should be appended.
        assert "!.claude/worktrees/" in lines
        # The pre-existing entry should not be duplicated.
        assert lines.count(".claude/") == 1


class TestPublishSkills:
    def _make_repo(self, tmp_path):
        """Create a minimal repo structure with fake skills."""
        repo = tmp_path / "repo"
        # core skills
        for name in ["gecs", "gm-scaffold"]:
            skill_dir = repo / "skills" / "core" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {name}\n")
        # reviewer skills
        for name in ["physics", "ui"]:
            skill_dir = repo / "skills" / "reviewer" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {name}\n")
        # __pycache__ in a skill (should be cleaned)
        cache = repo / "skills" / "core" / "gecs" / "__pycache__"
        cache.mkdir()
        (cache / "mod.pyc").write_text("x")
        # _read_config.sh
        shell_dir = repo / "shell"
        shell_dir.mkdir(parents=True)
        (shell_dir / "_read_config.sh").write_text("#!/bin/bash\n")
        return repo

    def test_flattens_skills(self, tmp_path):
        repo = self._make_repo(tmp_path)
        target = tmp_path / "target"
        target.mkdir()
        count = publish_skills(repo, target)
        assert count == 4
        assert (target / "gecs" / "SKILL.md").exists()
        assert (target / "gm-scaffold" / "SKILL.md").exists()
        assert (target / "physics" / "SKILL.md").exists()
        assert (target / "ui" / "SKILL.md").exists()

    def test_cleans_pycache(self, tmp_path):
        repo = self._make_repo(tmp_path)
        target = tmp_path / "target"
        target.mkdir()
        publish_skills(repo, target)
        assert not (target / "gecs" / "__pycache__").exists()

    def test_copies_read_config(self, tmp_path):
        repo = self._make_repo(tmp_path)
        target = tmp_path / "target"
        target.mkdir()
        publish_skills(repo, target)
        assert (target / "_read_config.sh").exists()

    def test_overwrites_existing_skill(self, tmp_path):
        repo = self._make_repo(tmp_path)
        target = tmp_path / "target"
        target.mkdir()
        # First publish
        publish_skills(repo, target)
        # Modify source
        (repo / "skills" / "core" / "gecs" / "SKILL.md").write_text("# updated\n")
        # Second publish
        publish_skills(repo, target)
        assert (target / "gecs" / "SKILL.md").read_text() == "# updated\n"


class TestRmtreeForce:
    """Unit tests for rmtree_force().

    Cross-platform note: the read-only-file scenario only stresses the
    onerror/onexc handler on Windows, because Linux/macOS happily unlink
    read-only files when the parent dir is writable. On non-Windows
    platforms these tests just verify the helper doesn't break the
    normal-tree path; the real "is the bug fixed" assertion is
    Windows-only by nature.
    """

    def test_removes_readonly_files(self, tmp_path):
        # Mirrors the real failure: cloned godot doc source contains
        # git pack-*.idx files that git writes as r--r--r--, and
        # plain shutil.rmtree raises PermissionError on Windows.
        target = tmp_path / "doc_source"
        target.mkdir()
        nested = target / ".git" / "objects" / "pack"
        nested.mkdir(parents=True)
        pack = nested / "pack-deadbeef.idx"
        pack.write_bytes(b"fake pack idx")
        pack.chmod(stat.S_IREAD)
        try:
            rmtree_force(target)
            assert not target.exists()
        finally:
            # Best-effort cleanup if the helper itself failed.
            if pack.exists():
                pack.chmod(stat.S_IWRITE)

    def test_removes_normal_tree(self, tmp_path):
        target = tmp_path / "tree"
        (target / "a" / "b").mkdir(parents=True)
        (target / "a" / "b" / "c.txt").write_text("hi")
        rmtree_force(target)
        assert not target.exists()


class TestPublishMainForceRmtree:
    """End-to-end: publish.main --force must survive a target whose
    .claude/skills contains read-only files (e.g. git pack-*.idx from a
    prior version that cloned godot-docs as a git repo).

    Reproduces the v0.3.2 release-blocker where Windows users upgrading
    from <=0.3.1 hit PermissionError [WinError 5] in shutil.rmtree because
    the rmtree call had no read-only handler. This test exercises the
    elif args.force branch in main(); the MAJOR-force branch above it
    rmtree's the same files via the same helper, so coverage carries.

    Cross-platform note: Linux/macOS unlink read-only files without
    needing the onerror handler, so on those platforms the test only
    proves main() doesn't otherwise break; the actual bug is
    Windows-only and only this OS exercises the fix path.
    """

    @pytest.fixture
    def env(self, tmp_path, monkeypatch):
        # Stub list mirrors every helper publish.main() calls (excluding
        # rmtree_force itself, which we want to exercise). If main() gains
        # a new helper that hits the network or filesystem and isn't stubbed
        # here, this test will start doing real work or failing — re-sync
        # with main() at that point.
        target = tmp_path / "target"
        target.mkdir()

        def _no_op(*a, **kw):
            return None

        for name in (
            "publish_skills", "publish_shared_refs", "publish_directory",
            "deploy_settings", "deploy_claude_md", "create_godotmaker_yaml",
            "create_project_config", "deploy_stage_schemas",
            "create_project_dirs", "register_mcp", "ensure_gitignore",
            "ensure_worktreeinclude", "ensure_git_repo", "write_target_version",
        ):
            monkeypatch.setattr(publish, name, _no_op)
        # Migration entry points must be truthy — main() exits 1 on falsy run.
        monkeypatch.setattr(publish, "baseline_applied", lambda _: 0)
        monkeypatch.setattr(publish, "run_migrations", lambda _: True)
        monkeypatch.setattr(publish, "read_godot_path",
                            lambda *a, **kw: "godot")
        return {"target": target}

    def _seed_target_version(self, target, version):
        gm = target / ".godotmaker"
        gm.mkdir(exist_ok=True)
        (gm / "version").write_text(version + "\n")

    def _force_source_version(self, monkeypatch, major, minor, patch):
        from _version import SemVer
        monkeypatch.setattr(publish, "read_source_version",
                            lambda _: SemVer(major, minor, patch))

    def _seed_readonly_pack(self, target):
        # Mirror the actual on-disk shape: prior versions cloned the
        # godot doc repo into .claude/skills/godot-api/doc_source, and
        # git writes pack-*.idx as r--r--r--.
        pack_dir = (target / ".claude" / "skills" / "godot-api"
                    / "doc_source" / ".git" / "objects" / "pack")
        pack_dir.mkdir(parents=True)
        pack = pack_dir / "pack-deadbeef.idx"
        pack.write_bytes(b"fake pack idx")
        pack.chmod(stat.S_IREAD)
        return pack

    def test_force_patch_upgrade_clears_readonly_skill_files(
        self, env, monkeypatch
    ):
        target = env["target"]
        self._seed_target_version(target, "0.3.1")
        self._force_source_version(monkeypatch, 0, 3, 3)
        readonly_pack = self._seed_readonly_pack(target)

        monkeypatch.setattr(sys, "argv",
                            ["publish.py", str(target), "--force"])
        try:
            publish.main()  # would raise PermissionError before the fix
        finally:
            if readonly_pack.exists():
                readonly_pack.chmod(stat.S_IWRITE)

        # The elif branch in main() rmtree's only skills_target then
        # mkdir's it back empty; the seeded read-only file must be gone.
        skills = target / ".claude" / "skills"
        assert skills.exists()
        assert list(skills.iterdir()) == []
