"""Tests for stage_reminder.py hook."""
import json
import os
import pytest
import tempfile
from .helpers import run_hook, cleanup_metrics

HOOK = "stage_reminder.py"


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


class TestNonStageWrites:
    def test_ignores_non_write_tool(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": ".godotmaker/stage.json"},
        })
        assert code == 0
        assert parsed is None

    def test_ignores_non_stage_file(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "src/main.gd",
                "content": "extends Node",
            },
        })
        assert code == 0
        assert parsed is None

    def test_ignores_wrong_event(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": '{"completed_stage": 1}',
            },
        })
        assert code == 0
        assert parsed is None


class TestStageReminder:
    def test_stage1_complete_reminds_stage2(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": '{"completed_stage": 1}',
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Stage 2" in ctx
        assert "stage2_architecture.md" in ctx

    def test_stage6_complete_reminds_stage7(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": '{"completed_stage": 6}',
            },
        })
        assert code == 0
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Stage 7" in ctx
        assert "stage7_integration.md" in ctx

    def test_stage8_complete_no_reminder(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": '{"completed_stage": 8}',
            },
        })
        assert code == 0
        # No next stage, no output
        assert parsed is None

    def test_windows_path(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "D:\\Games\\MyGame\\.godotmaker\\stage.json",
                "content": '{"completed_stage": 3}',
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "stage4_assets.md" in ctx

    def test_edit_tool(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "old_string": '{"completed_stage": 2}',
                "new_string": '{"completed_stage": 3}',
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "stage4_assets.md" in ctx

    def test_invalid_json_content(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": "not json",
            },
        })
        assert code == 0
        assert parsed is None  # Silently ignores

    def test_missing_completed_stage(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": '{"other_field": 1}',
            },
        })
        assert code == 0
        assert parsed is None

    def test_never_blocks(self, project_dir):
        """Stage reminder should ALWAYS allow, never block."""
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.json",
                "content": '{"completed_stage": 5}',
            },
        })
        assert code == 0
        if parsed:
            assert "decision" not in parsed or parsed.get("decision") != "block"


class TestProgressReminder:
    def test_check_worker_report_includes_progress(self, project_dir):
        """check_worker_report.py should include progress via hookSpecificOutput."""
        # Create metrics with some worker events
        os.makedirs(".godotmaker", exist_ok=True)
        with open(".godotmaker/metrics_current.jsonl", "w") as f:
            f.write(json.dumps({
                "event": "subagent_stop", "report_type": "worker",
                "status": "DONE"
            }) + "\n")
            f.write(json.dumps({
                "event": "subagent_stop", "report_type": "verifier",
                "status": "PASS"
            }) + "\n")

        worker_report = (
            "## Report: Movement\n"
            "### Status: DONE\n"
            "### Files Changed\n- systems/move.gd\n- e2e/test_move.py\n"
            "### Tests\n#### Unit Tests\ntest_move.gd: 3 passed, 0 failed\n"
            "#### E2E Tests\ne2e/test_move.py: e2e 1 scenario passed, 0 failed\n"
            "### Build\ngodot --headless --quit: OK\n"
            "### Memory Entry\nMovement uses velocity component.\n"
        )

        _, code, parsed = run_hook("check_worker_report.py", {
            "hook_event_name": "SubagentStop",
            "last_assistant_message": worker_report,
        })
        assert code == 0
        if parsed:
            hso = parsed.get("hookSpecificOutput", {})
            ctx = hso.get("additionalContext", "")
            assert "Workers:" in ctx
            assert "Verifiers:" in ctx
