"""Tests for check_stage_prerequisites.py hook.

The hook reads stage_schemas.json + .godotmaker/stage.json to determine
which stages are completed, then checks that their output files exist.
"""
import json
import os
import pytest
import tempfile
from .helpers import run_hook, is_blocked, cleanup_metrics, write_stage_json

HOOK = "check_stage_prerequisites.py"

AGENT_INPUT = {
    "tool_name": "Agent",
    "tool_input": {"prompt": "implement player"},
    "agent_id": "",
}


@pytest.fixture(autouse=True)
def clean():
    yield
    cleanup_metrics()


@pytest.fixture
def project_dir():
    """Create a temp directory with stage_schemas.json and chdir to it."""
    original = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        # Create schema file where the hook can find it
        config_dir = os.path.join(".godotmaker")
        os.makedirs(config_dir, exist_ok=True)
        schema = {
            "1": {"files": ["GDD.md", "PLAN.md", "ASSETS.md", "SCENES.md", "TOC.md"]},
            "2": {"files": ["STRUCTURE.md"]},
            "3": {"files": ["project.godot", "addons/gecs/"]},
        }
        with open(os.path.join(config_dir, "stage_schemas.json"), "w") as f:

            json.dump(schema, f)
        yield tmpdir
        os.chdir(original)


def mark_stage_complete(stage: int):
    """Write stage.json marking stages 1..stage as complete."""
    write_stage_json(stage)


class TestStagePrerequisites:
    def test_allow_when_no_stages_completed(self, project_dir):
        """No stage.json means completed=0, nothing to check."""
        _, _, parsed = run_hook(HOOK, AGENT_INPUT)
        assert not is_blocked(parsed), "Should allow when no stages completed yet"

    def test_block_when_stage1_complete_but_files_missing(self, project_dir):
        """Stage 1 marked complete but PLAN.md etc don't exist."""
        mark_stage_complete(1)
        _, _, parsed = run_hook(HOOK, AGENT_INPUT)
        assert is_blocked(parsed), "Should block when stage 1 files missing"

    def test_block_when_partial_files(self, project_dir):
        """Stage 1 complete, some files exist but not all."""
        mark_stage_complete(1)
        open("GDD.md", "w").close()
        open("PLAN.md", "w").close()
        # Missing: ASSETS.md, SCENES.md, TOC.md
        _, _, parsed = run_hook(HOOK, AGENT_INPUT)
        assert is_blocked(parsed), "Should block when some stage 1 files missing"

    def test_allow_when_all_stage1_files_present(self, project_dir):
        """Stage 1 complete with all files present."""
        mark_stage_complete(1)
        for f in ["GDD.md", "PLAN.md", "ASSETS.md", "SCENES.md", "TOC.md"]:
            open(f, "w").close()
        _, _, parsed = run_hook(HOOK, AGENT_INPUT)
        assert not is_blocked(parsed), "Should allow when all stage 1 files present"

    def test_block_when_stage2_file_missing(self, project_dir):
        """Stages 1+2 complete, stage 2 file missing."""
        mark_stage_complete(2)
        for f in ["GDD.md", "PLAN.md", "ASSETS.md", "SCENES.md", "TOC.md"]:
            open(f, "w").close()
        # Missing: STRUCTURE.md
        _, _, parsed = run_hook(HOOK, AGENT_INPUT)
        assert is_blocked(parsed), "Should block when STRUCTURE.md missing"

    def test_allow_all_stages_present(self, project_dir):
        """Stages 1-3 complete with all files."""
        mark_stage_complete(3)
        for f in ["GDD.md", "PLAN.md", "ASSETS.md", "SCENES.md", "TOC.md",
                   "STRUCTURE.md", "project.godot"]:
            open(f, "w").close()
        os.makedirs("addons/gecs", exist_ok=True)
        _, _, parsed = run_hook(HOOK, AGENT_INPUT)
        assert not is_blocked(parsed), "Should allow when all stage files present"

    def test_non_agent_tool_ignored(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "foo.gd"},
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed), "Non-Agent tools should pass through"

    def test_subagent_dispatch_ignored(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "tool_name": "Agent",
            "tool_input": {"prompt": "verify build"},
            "agent_id": "worker-123",
        })
        assert code == 0
        assert not is_blocked(parsed), "Subagent dispatching sub-subagent should pass"
