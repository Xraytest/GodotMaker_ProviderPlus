"""Tests for check_file_permissions.py hook."""
import os
import tempfile
import pytest
from .helpers import run_hook, is_blocked, cleanup_metrics, write_current_role

HOOK = "check_file_permissions.py"


@pytest.fixture(autouse=True)
def clean():
    yield
    cleanup_metrics()


@pytest.fixture
def project_dir():
    """Temp dir to isolate .godotmaker/current_role per test."""
    original = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(original)


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


class TestRoleBased:
    """Role-based permissions per current_role file."""

    @pytest.mark.parametrize("ext", [".gd", ".tscn", ".tres"])
    def test_scaffold_can_write_game_code(self, project_dir, ext):
        write_current_role("scaffold")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": f"scripts/x{ext}"},
            "agent_id": "",
        })
        assert not is_blocked(parsed), "Scaffold may write game code"

    def test_scaffold_can_write_e2e_conftest(self, project_dir):
        """Scaffold creates the initial e2e/conftest.py — permissive role."""
        write_current_role("scaffold")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "e2e/conftest.py"},
            "agent_id": "",
        })
        assert not is_blocked(parsed), "Scaffold must be able to seed e2e/conftest.py"

    @pytest.mark.parametrize("role", ["gdd", "asset", "build", "fixgap", "accept", "finalize"])
    def test_main_blocked_from_e2e(self, project_dir, role):
        write_current_role(role)
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "e2e/test_player.py"},
            "agent_id": "",
        })
        assert is_blocked(parsed), f"role={role} must not write to e2e/"

    @pytest.mark.parametrize("role", ["build", "fixgap"])
    def test_orchestrator_blocked_from_game_code(self, project_dir, role):
        write_current_role(role)
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "scripts/move.gd"},
            "agent_id": "",
        })
        assert is_blocked(parsed)

    def test_gdd_can_write_planning_docs(self, project_dir):
        write_current_role("gdd")
        for path in ["GDD.md", "PLAN.md", "STRUCTURE.md", "ASSETS.md", "SCENES.md", "TOC.md"]:
            _, _, parsed = run_hook(HOOK, {
                "tool_name": "Write",
                "tool_input": {"file_path": path},
                "agent_id": "",
            })
            assert not is_blocked(parsed), f"gdd must allow {path}"

    def test_gdd_can_write_project_godot(self, project_dir):
        write_current_role("gdd")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Edit",
            "tool_input": {"file_path": "project.godot"},
            "agent_id": "",
        })
        assert not is_blocked(parsed), "gdd may tweak project.godot for design changes"

    @pytest.mark.parametrize("ext", [".gd", ".tscn", ".tres"])
    def test_gdd_blocked_from_game_code(self, project_dir, ext):
        write_current_role("gdd")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": f"src/x{ext}"},
            "agent_id": "",
        })
        assert is_blocked(parsed), f"gdd must not write {ext}"

    def test_gdd_blocked_from_assets_dir(self, project_dir):
        write_current_role("gdd")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "assets/sprite.png"},
            "agent_id": "",
        })
        assert is_blocked(parsed), "gdd must not write to assets/"

    def test_asset_can_write_assets_md(self, project_dir):
        write_current_role("asset")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "ASSETS.md"},
            "agent_id": "",
        })
        assert not is_blocked(parsed)

    def test_asset_can_write_godotmaker(self, project_dir):
        write_current_role("asset")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": ".godotmaker/state.json"},
            "agent_id": "",
        })
        assert not is_blocked(parsed)

    def test_asset_blocked_from_other_files(self, project_dir):
        write_current_role("asset")
        for path in ["assets/sprite.png", "PLAN.md", "STRUCTURE.md", "SCENES.md",
                     "GAP.md", "src/x.gd", "GDD.md", "subdir/ASSETS.md"]:
            _, _, parsed = run_hook(HOOK, {
                "tool_name": "Write",
                "tool_input": {"file_path": path},
                "agent_id": "",
            })
            assert is_blocked(parsed), f"asset orchestrator must block {path}"

    def test_verify_is_read_only(self, project_dir):
        write_current_role("verify")
        for path in ["scripts/x.gd", "PLAN.md", "e2e/test.py"]:
            _, _, parsed = run_hook(HOOK, {
                "tool_name": "Write",
                "tool_input": {"file_path": path},
                "agent_id": "",
            })
            assert is_blocked(parsed), f"verify must block {path}"

    def test_evaluate_can_write_e2e(self, project_dir):
        write_current_role("evaluate")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "e2e/test_game.py"},
            "agent_id": "",
        })
        assert not is_blocked(parsed)

    def test_evaluate_can_write_evaluation_json(self, project_dir):
        write_current_role("evaluate")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": ".godotmaker/evaluation.json"},
            "agent_id": "",
        })
        assert not is_blocked(parsed)

    def test_evaluate_can_write_stage_jsonl(self, project_dir):
        """Evaluate must append its completion event to .godotmaker/stage.jsonl
        (per gm-evaluate SKILL.md 'When Done')."""
        write_current_role("evaluate")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Edit",
            "tool_input": {"file_path": ".godotmaker/stage.jsonl"},
            "agent_id": "",
        })
        assert not is_blocked(parsed)

    def test_evaluate_blocked_from_other_files(self, project_dir):
        write_current_role("evaluate")
        for path in ["scripts/x.gd", "PLAN.md", "MEMORY.md", "config.yaml"]:
            _, _, parsed = run_hook(HOOK, {
                "tool_name": "Write",
                "tool_input": {"file_path": path},
                "agent_id": "",
            })
            assert is_blocked(parsed), f"evaluate must block {path}"

    def test_finalize_can_update_docs(self, project_dir):
        write_current_role("finalize")
        for path in ["GDD.md", "MEMORY.md", "STRUCTURE.md", ".godotmaker/final_report.json"]:
            _, _, parsed = run_hook(HOOK, {
                "tool_name": "Write",
                "tool_input": {"file_path": path},
                "agent_id": "",
            })
            assert not is_blocked(parsed), f"finalize must allow {path}"


class TestSubagentInRole:
    """Subagent rules apply on top of role rules."""

    def test_worker_blocked_from_e2e_in_build(self, project_dir):
        write_current_role("build")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "e2e/test_x.py"},
            "agent_id": "worker-1",
        })
        assert is_blocked(parsed)

    def test_worker_can_write_game_code(self, project_dir):
        write_current_role("build")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "systems/move.gd"},
            "agent_id": "worker-1",
        })
        assert not is_blocked(parsed)

    def test_worker_blocked_from_planning_docs(self, project_dir):
        write_current_role("build")
        _, _, parsed = run_hook(HOOK, {
            "tool_name": "Write",
            "tool_input": {"file_path": "PLAN.md"},
            "agent_id": "worker-1",
        })
        assert is_blocked(parsed)
