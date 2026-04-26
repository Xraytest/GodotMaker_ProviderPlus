"""Tests for publish.py."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools",
))

from publish import (
    read_godot_path,
    create_project_config,
    ensure_gitignore,
    publish_skills,
    DEFAULT_CONFIG_TEMPLATE,
)
from pathlib import Path


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
        lines = [l for l in content.splitlines() if l and not l.startswith("#")]
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
        lines = [l.strip() for l in content.splitlines()]
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
        lines = [l.strip() for l in content.splitlines()]
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
        lines = [l.strip() for l in content.splitlines()]
        assert ".godotmaker/" not in lines
        # Selective entries must now be present
        for entry in SELECTIVE_ENTRIES:
            assert entry in content


class TestPublishSkills:
    def _make_repo(self, tmp_path):
        """Create a minimal repo structure with fake skills."""
        repo = tmp_path / "repo"
        # core skills
        for name in ["gecs", "orchestrator"]:
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
        assert (target / "orchestrator" / "SKILL.md").exists()
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
