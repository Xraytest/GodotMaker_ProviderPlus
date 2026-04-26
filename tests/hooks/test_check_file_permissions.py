"""Tests for check_file_permissions.py hook."""
import pytest
from .helpers import run_hook, is_blocked, cleanup_metrics

HOOK = "check_file_permissions.py"


@pytest.fixture(autouse=True)
def clean():
    yield
    cleanup_metrics()


class TestOrchestratorBlocked:
    """Main agent (no agent_id) should be blocked from writing game code."""

    @pytest.mark.parametrize("ext", [".gd", ".tscn", ".tres"])
    def test_block_game_code_extensions(self, ext):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": f"scripts/player{ext}"},
            "agent_id": "",
        })
        assert is_blocked(parsed), f"Should block orchestrator writing {ext}"

    def test_allow_planning_docs(self):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "PLAN.md"},
            "agent_id": "",
        })
        assert not is_blocked(parsed), "Orchestrator should be allowed to write PLAN.md"

    def test_allow_memory(self):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Edit",
            "tool_input": {"file_path": "MEMORY.md"},
            "agent_id": "",
        })
        assert not is_blocked(parsed), "Orchestrator should be allowed to edit MEMORY.md"


class TestWorkerBlocked:
    """Subagents (with agent_id) should be blocked from writing planning docs."""

    @pytest.mark.parametrize("doc", ["PLAN.md", "STRUCTURE.md", "ASSETS.md"])
    def test_block_planning_docs(self, doc):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Edit",
            "tool_input": {"file_path": doc},
            "agent_id": "worker-123",
        })
        assert is_blocked(parsed), f"Worker should be blocked from writing {doc}"

    def test_allow_game_code(self):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "scripts/player.gd"},
            "agent_id": "worker-123",
        })
        assert not is_blocked(parsed), "Worker should be allowed to write .gd files"

    def test_allow_test_files(self):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "test/test_player.gd"},
            "agent_id": "worker-456",
        })
        assert not is_blocked(parsed), "Worker should be allowed to write test files"


class TestEdgeCases:
    """Edge cases and non-file-write tools."""

    def test_non_write_tool_allowed(self):
        _, code, parsed = run_hook(HOOK, {
            "tool_name": "Read",
            "tool_input": {"file_path": "scripts/player.gd"},
            "agent_id": "",
        })
        assert code == 0
        assert not is_blocked(parsed), "Non-write tools should always pass"

    def test_empty_input(self):
        _, code, _ = run_hook(HOOK, {})
        assert code == 0, "Empty input should not crash"

    def test_missing_file_path(self):
        _, code, _ = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {},
            "agent_id": "",
        })
        assert code == 0, "Missing file_path should not crash"

    def test_windows_backslash_path(self):
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "scripts\\player_system.gd"},
            "agent_id": "",
        })
        assert is_blocked(parsed), "Should handle Windows backslash paths"
