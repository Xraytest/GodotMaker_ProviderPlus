"""Tests for migrations/20260507120000_introduce_tag_based_pipeline.py.

Migration moves an existing GodotMaker game project (with a single
all-of-game PLAN.md and no ROADMAP.md) into the new tag-based layout:
docs/tags/v0.1.0/ archive + a stub ROADMAP.md. Idempotent — second run
is a no-op.
"""
import importlib.util
from pathlib import Path

import pytest


MIGRATION_PATH = Path(__file__).resolve().parents[2] / "migrations" / "20260507120000_introduce_tag_based_pipeline.py"


@pytest.fixture
def migration_module():
    spec = importlib.util.spec_from_file_location("tag_migration", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project(tmp_path):
    """A pre-tag-pipeline project: GDD, PLAN, the usual root docs, no ROADMAP."""
    (tmp_path / "GDD.md").write_text(
        "# Game Design Document: Tiny Test Game\n\nDesign content here.",
        encoding="utf-8",
    )
    (tmp_path / "PLAN.md").write_text(
        "# Game Plan: Tiny Test Game\n\n"
        "## Main Build\n\n"
        "### Systems & Components\n\n"
        "| System | Components | Purpose |\n"
        "|---|---|---|\n"
        "| MovementSystem | Transform | move things |\n"
        "| RenderSystem | Sprite | draw things |\n"
        "| HealthSystem | Health | track HP |\n",
        encoding="utf-8",
    )
    (tmp_path / "STRUCTURE.md").write_text("# Structure", encoding="utf-8")
    (tmp_path / "SCENES.md").write_text("# Scenes", encoding="utf-8")
    (tmp_path / "ASSETS.md").write_text("# Assets", encoding="utf-8")
    (tmp_path / "MEMORY.md").write_text("# Memory", encoding="utf-8")
    return tmp_path


class TestMigration:
    def test_first_run_creates_archive_and_roadmap(self, migration_module, project):
        migration_module.migrate(project)
        assert (project / "ROADMAP.md").is_file()
        archive = project / "docs" / "tags" / "v0.1.0"
        assert archive.is_dir()
        assert (archive / "GDD-snapshot.md").is_file()
        assert (archive / "PLAN.md").is_file()
        assert (archive / "STRUCTURE.md").is_file()
        assert (archive / "SCENES.md").is_file()
        assert (archive / "MEMORY.md").is_file()
        # ASSETS.md is cross-tag; not archived
        assert not (archive / "ASSETS.md").exists()

    def test_first_run_preserves_root_files(self, migration_module, project):
        migration_module.migrate(project)
        # Root files MUST stay — gm-gdd subsequent-mode picks them up
        for f in ("GDD.md", "PLAN.md", "STRUCTURE.md", "SCENES.md", "ASSETS.md", "MEMORY.md"):
            assert (project / f).is_file(), f"{f} disappeared from root"

    def test_first_run_injects_tag_header_into_root_plan(self, migration_module, project):
        migration_module.migrate(project)
        plan_text = (project / "PLAN.md").read_text(encoding="utf-8")
        assert "**Tag:** v0.1.0" in plan_text, \
            "migration must inject `**Tag:** v0.1.0` so check_tag_archived passes"
        # Header should sit just below the first H1, not at the very top
        lines = plan_text.splitlines()
        h1_idx = next(i for i, line in enumerate(lines) if line.startswith("# "))
        tag_idx = next(i for i, line in enumerate(lines) if line.strip() == "**Tag:** v0.1.0")
        assert tag_idx > h1_idx, "Tag header must come after the H1 title"

    def test_archived_plan_carries_tag_header(self, migration_module, project):
        migration_module.migrate(project)
        archived = (project / "docs" / "tags" / "v0.1.0" / "PLAN.md").read_text(encoding="utf-8")
        assert "**Tag:** v0.1.0" in archived

    def test_first_run_does_not_create_git_tag(self, migration_module, project):
        # Migration explicitly does not auto-tag — the user decides
        migration_module.migrate(project)
        # No .git/refs/tags/ since no git repo and no auto-tag attempt
        assert not (project / ".git" / "refs" / "tags").exists()

    def test_roadmap_has_v010_entry_with_extracted_features(self, migration_module, project):
        migration_module.migrate(project)
        roadmap = (project / "ROADMAP.md").read_text(encoding="utf-8")
        assert "v0.1.0" in roadmap
        # Features should be extracted from the PLAN system table
        assert "MovementSystem" in roadmap
        assert "RenderSystem" in roadmap

    def test_roadmap_uses_project_name_from_gdd(self, migration_module, project):
        migration_module.migrate(project)
        roadmap = (project / "ROADMAP.md").read_text(encoding="utf-8")
        # _extract_project_name strips the "Game Design Document:" prefix
        assert "Tiny Test Game" in roadmap

    def test_second_run_is_noop(self, migration_module, project):
        migration_module.migrate(project)
        # Capture state after first run
        roadmap_before = (project / "ROADMAP.md").read_text(encoding="utf-8")
        archived_plan_before = (project / "docs" / "tags" / "v0.1.0" / "PLAN.md").read_text(encoding="utf-8")

        migration_module.migrate(project)

        # No changes — second run detected "already migrated" via ROADMAP.md presence
        roadmap_after = (project / "ROADMAP.md").read_text(encoding="utf-8")
        archived_plan_after = (project / "docs" / "tags" / "v0.1.0" / "PLAN.md").read_text(encoding="utf-8")
        assert roadmap_before == roadmap_after
        assert archived_plan_before == archived_plan_after

    def test_skip_when_no_gdd_or_plan(self, migration_module, tmp_path):
        # Empty project — should skip without writing anything
        migration_module.migrate(tmp_path)
        assert not (tmp_path / "ROADMAP.md").exists()
        assert not (tmp_path / "docs").exists()

    def test_partial_archive_completes_on_rerun(self, migration_module, project):
        # If a previous run was interrupted (mkdir succeeded but ROADMAP write
        # didn't get there), re-running must complete the migration rather than
        # bail out as "already migrated". The completed-end-state guard checks
        # ROADMAP.md AND archived GDD-snapshot.md — both absent here.
        (project / "docs" / "tags" / "v0.1.0").mkdir(parents=True)
        migration_module.migrate(project)
        assert (project / "ROADMAP.md").is_file()
        assert (project / "docs" / "tags" / "v0.1.0" / "GDD-snapshot.md").is_file()

    def test_aborts_cleanly_on_non_utf8_plan(self, migration_module, project, capsys):
        # CP-1252-encoded PLAN.md (\xe9 = é) is not valid UTF-8 — strict read
        # at the top of migrate() must abort BEFORE any mutation.
        (project / "PLAN.md").write_bytes(b"# Game Plan: Latin1\n\n\xe9clair section\n")
        migration_module.migrate(project)
        # No mutations: neither ROADMAP.md nor docs/tags/ created
        assert not (project / "ROADMAP.md").exists()
        assert not (project / "docs").exists()
        # Original PLAN.md byte-for-byte preserved
        assert (project / "PLAN.md").read_bytes() == b"# Game Plan: Latin1\n\n\xe9clair section\n"
        out = capsys.readouterr().out
        assert "[error]" in out and "UTF-8" in out

    def test_handles_missing_optional_root_files(self, migration_module, tmp_path):
        # GDD + PLAN required; others optional. Migration should still succeed.
        (tmp_path / "GDD.md").write_text("# Game Design Document: Minimal\n", encoding="utf-8")
        (tmp_path / "PLAN.md").write_text("# Game Plan: Minimal\n", encoding="utf-8")
        migration_module.migrate(tmp_path)
        assert (tmp_path / "ROADMAP.md").is_file()
        archive = tmp_path / "docs" / "tags" / "v0.1.0"
        assert (archive / "GDD-snapshot.md").is_file()
        assert (archive / "PLAN.md").is_file()
        # SCENES/ASSETS/STRUCTURE/MEMORY were skipped — not in archive
        assert not (archive / "STRUCTURE.md").is_file()


class TestTagHeaderInjection:
    def test_injects_after_first_h1(self, migration_module, tmp_path):
        plan = tmp_path / "PLAN.md"
        plan.write_text("# Game Plan: X\n\nbody\n", encoding="utf-8")
        modified = migration_module._inject_tag_header(plan, "v0.1.0")
        assert modified is True
        content = plan.read_text(encoding="utf-8")
        assert content.startswith("# Game Plan: X\n\n**Tag:** v0.1.0\n")

    def test_idempotent_when_header_already_present(self, migration_module, tmp_path):
        plan = tmp_path / "PLAN.md"
        original = "# Game Plan: X\n\n**Tag:** v0.5.0\n\nbody\n"
        plan.write_text(original, encoding="utf-8")
        modified = migration_module._inject_tag_header(plan, "v0.1.0")
        assert modified is False
        # Existing header (even with a different tag value) must not be overwritten
        assert plan.read_text(encoding="utf-8") == original

    def test_prepends_when_no_h1(self, migration_module, tmp_path):
        plan = tmp_path / "PLAN.md"
        plan.write_text("just plain prose\n", encoding="utf-8")
        modified = migration_module._inject_tag_header(plan, "v0.1.0")
        assert modified is True
        assert plan.read_text(encoding="utf-8").startswith("**Tag:** v0.1.0\n")


class TestProjectNameExtraction:
    def test_strips_gdd_prefix(self, migration_module, tmp_path):
        gdd = tmp_path / "GDD.md"
        gdd.write_text("# Game Design Document: My Game\n", encoding="utf-8")
        plan = tmp_path / "PLAN.md"
        plan.write_text("# something else\n", encoding="utf-8")
        assert migration_module._extract_project_name(gdd, plan) == "My Game"

    def test_strips_plan_prefix(self, migration_module, tmp_path):
        gdd = tmp_path / "GDD.md"
        gdd.write_text("not a heading\n", encoding="utf-8")
        plan = tmp_path / "PLAN.md"
        plan.write_text("# Game Plan: Survivor Clone\n", encoding="utf-8")
        assert migration_module._extract_project_name(gdd, plan) == "Survivor Clone"

    def test_falls_back_to_untitled(self, migration_module, tmp_path):
        gdd = tmp_path / "GDD.md"
        gdd.write_text("plain text\n", encoding="utf-8")
        plan = tmp_path / "PLAN.md"
        plan.write_text("plain text\n", encoding="utf-8")
        assert migration_module._extract_project_name(gdd, plan) == "Untitled"
