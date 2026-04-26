"""Tests for check_completion.py hook."""
import json
import os
import pytest
import tempfile
from .helpers import run_hook, is_blocked, cleanup_metrics, write_stage_json

HOOK = "check_completion.py"


@pytest.fixture(autouse=True)
def clean():
    yield
    cleanup_metrics()


@pytest.fixture
def project_dir():
    original = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(original)


def set_enforcement_stage():
    """Set completed stage to 7+ so completion checks are enforced."""
    write_stage_json(7)


def skip_forced_review():
    """Set stop_block_count=1 so forced review (block_count==0) is skipped.
    Also ensures stage >= 7 so checks are enforced."""
    set_enforcement_stage()
    with open(os.path.join(".godotmaker", "state.json"), "w") as f:
        json.dump({"stop_block_count": 1}, f)


class TestForcedReview:
    def test_first_stop_always_blocked(self, project_dir):
        """First Stop attempt at enforcement stage must be blocked with mandatory self-review."""
        set_enforcement_stage()
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert is_blocked(parsed), "First Stop must always block for forced review"
        assert "MANDATORY SELF-REVIEW" in parsed.get("reason", "")

    def test_forced_review_includes_status(self, project_dir):
        """Forced review message should include E2E and screenshot status."""
        set_enforcement_stage()
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        reason = parsed.get("reason", "")
        assert "E2E test runs recorded" in reason
        assert "screenshots/" in reason


class TestMainAgentOnly:
    def test_subagent_not_blocked(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "worker-123",
        })
        assert code == 0
        assert not is_blocked(parsed)

    def test_no_project_godot_not_blocked(self, project_dir):
        """No project.godot and past forced review — should not block."""
        skip_forced_review()
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed)


class TestProjectCompleteness:
    def test_incomplete_project_blocked(self, project_dir):
        skip_forced_review()
        # Create minimal project.godot but missing everything else
        with open("project.godot", "w") as f:
            f.write("[application]\nconfig/name=\"Test\"\n")
        # Copy check_project.py to tools/ so the hook can find it
        os.makedirs("tools", exist_ok=True)
        import shutil
        # tests/hooks/ → project_root/tools/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        src = os.path.join(project_root, "tools", "check_project.py")
        shutil.copy(src, "tools/check_project.py")

        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert is_blocked(parsed), "Should block when project is incomplete"


class TestDiligenceCheck:
    def test_workers_without_verifiers_blocked(self, project_dir):
        # Create project with all artifacts to pass completeness check
        with open("project.godot", "w") as f:
            f.write("[application]\nconfig/name=\"Test\"\n[editor_plugins]\nenabled=PackedStringArray(\"res://addons/godot_e2e/plugin.cfg\")\n")
        with open("PLAN.md", "w") as f:
            f.write("# Plan\n## Task Status\n| 1 | Move | completed |\n")
        with open("STRUCTURE.md", "w") as f:
            f.write("# Struct\n## Component Registry\n| C | f | int |\n## System Schedule\n| 1 | S |\n")
        with open("ASSETS.md", "w") as f:
            f.write("# Assets\nN/A\n")
        with open("MEMORY.md", "w") as f:
            f.write("# Memory\n")
        os.makedirs("addons/gecs", exist_ok=True)
        os.makedirs("addons/gdunit4", exist_ok=True)
        os.makedirs("components", exist_ok=True)
        os.makedirs("systems", exist_ok=True)
        os.makedirs("test", exist_ok=True)
        os.makedirs("e2e", exist_ok=True)
        with open("components/health.gd", "w") as f:
            f.write("extends Component\n")
        with open("systems/move.gd", "w") as f:
            f.write("extends System\n")
        with open("test/test_move.gd", "w") as f:
            f.write("extends GdUnitTestSuite\n")
        with open("e2e/test_game_e2e.py", "w") as f:
            f.write("# e2e test\n")

        # Skip forced review, then test diligence check
        skip_forced_review()

        # Write current session metrics showing workers but no verifiers/reviewers
        with open(".godotmaker/metrics_current.jsonl", "w") as f:
            f.write(json.dumps({"event": "subagent_start", "agent_id": "w1", "role": "worker"}) + "\n")
            f.write(json.dumps({"event": "subagent_start", "agent_id": "w2", "role": "worker"}) + "\n")
            f.write(json.dumps({"event": "subagent_stop", "agent_id": "w1", "role": "worker", "report_type": "worker", "status": "DONE"}) + "\n")
            f.write(json.dumps({"event": "subagent_stop", "agent_id": "w2", "role": "worker", "report_type": "worker", "status": "DONE"}) + "\n")

        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert is_blocked(parsed), "Should block when no verifiers dispatched"
        assert "verifier" in parsed.get("reason", "").lower()


class TestStageAwareness:
    """Tests that completion checks are only enforced at late pipeline stages."""

    def _set_stage(self, stage: int):
        """Write a stage.json with completed stages up to the given number."""
        write_stage_json(stage)

    def test_early_stage_allows_stop(self, project_dir):
        """At stage 3, orchestrator should be able to stop without checks."""
        self._set_stage(3)
        with open("project.godot", "w") as f:
            f.write("[application]\n")
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed), "Should allow stop at early stage"

    def test_stage_6_allows_stop(self, project_dir):
        """At stage 6, still below enforcement threshold."""
        self._set_stage(6)
        with open("project.godot", "w") as f:
            f.write("[application]\n")
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed), "Should allow stop at stage 6"

    def test_stage_7_enforces_checks(self, project_dir):
        """At stage 7, full completion checks should be enforced."""
        self._set_stage(7)
        with open("project.godot", "w") as f:
            f.write("[application]\n")
        # First stop at stage 7 → forced self-review
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert is_blocked(parsed), "Should enforce checks at stage 7"

    def test_no_stage_file_allows_stop(self, project_dir):
        """No stage.json (not in a pipeline) → allow stop."""
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed), "Should allow stop when no stage file exists"


class TestAntiDeadloop:
    def test_allows_after_limit_blocks(self, project_dir):
        with open("project.godot", "w") as f:
            f.write("[application]\n")

        # Must be at enforcement stage for checks to run
        set_enforcement_stage()
        with open(".godotmaker/state.json", "w") as f:
            json.dump({"stop_block_count": 5}, f)

        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "Stop",
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed), "Should allow after BLOCK_LIMIT to prevent deadloop"
