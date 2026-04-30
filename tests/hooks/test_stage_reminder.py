"""Tests for stage_reminder.py hook (role-based pipeline)."""
import json
import os
import shutil
import pytest
import tempfile
from .helpers import run_hook, is_blocked, cleanup_metrics

SCHEMA_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "stage_schemas.json"
)

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
        # Always provide a schema so validation can run
        os.makedirs(".godotmaker", exist_ok=True)
        shutil.copy(SCHEMA_SRC, ".godotmaker/stage_schemas.json")
        yield tmpdir
        os.chdir(original)


def stage_jsonl(events: list[dict]) -> str:
    """events is a list of {"role": X, "ts": Y} dicts."""
    return "\n".join(json.dumps(e) for e in events) + "\n"


class TestNonStageWrites:
    def test_ignores_non_write_tool(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": ".godotmaker/stage.jsonl"},
        })
        assert code == 0
        assert parsed is None

    def test_ignores_non_stage_file(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/main.gd", "content": "extends Node"},
        })
        assert code == 0
        assert parsed is None

    def test_ignores_wrong_event(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "gdd", "ts": "2026-01-01T00:00:00Z"}]),
            },
        })
        assert code == 0
        assert parsed is None


class TestRoleReminder:
    def test_scaffold_complete_reminds_gdd(self, project_dir):
        open("project.godot", "w").close()
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "scaffold", "ts": "2026-01-01T00:00:00Z"}]),
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/gm-gdd" in ctx
        assert "scaffold" in ctx

    def test_gdd_complete_reminds_asset(self, project_dir):
        for f in ["GDD.md", "PLAN.md", "STRUCTURE.md", "ASSETS.md", "SCENES.md", "TOC.md"]:
            open(f, "w").close()
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "gdd", "ts": "2026-01-01T00:00:00Z"}]),
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/gm-asset" in ctx
        assert "gdd" in ctx

    def test_asset_complete_reminds_build(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "asset", "ts": "2026-01-01T00:30:00Z"}]),
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/gm-build" in ctx

    def test_evaluate_complete_reminds_accept_or_fixgap(self, project_dir):
        with open(".godotmaker/evaluation.json", "w") as f:
            f.write('{"result": "approve"}')
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([
                    {"role": "gdd", "ts": "2026-01-01T00:00:00Z"},
                    {"role": "evaluate", "ts": "2026-01-01T05:00:00Z"},
                ]),
            },
        })
        assert code == 0
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/gm-accept" in ctx and "/gm-fixgap" in ctx

    def test_finalize_complete_no_reminder(self, project_dir):
        with open(".godotmaker/final_report.json", "w") as f:
            f.write('{"status": "completed"}')
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "finalize", "ts": "2026-01-01T07:00:00Z"}]),
            },
        })
        assert code == 0
        # No next role after finalize → no additionalContext
        assert parsed is None or "additionalContext" not in parsed.get("hookSpecificOutput", {})

    def test_windows_path(self, project_dir):
        for f in ["GDD.md", "PLAN.md", "STRUCTURE.md", "ASSETS.md", "SCENES.md", "TOC.md"]:
            open(f, "w").close()
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "D:\\Games\\MyGame\\.godotmaker\\stage.jsonl",
                "content": stage_jsonl([{"role": "gdd", "ts": "2026-01-01T00:00:00Z"}]),
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/gm-asset" in ctx

    def test_edit_tool_for_gdd_event_reminds_asset(self, project_dir):
        for f in ["GDD.md", "PLAN.md", "STRUCTURE.md", "ASSETS.md", "SCENES.md", "TOC.md"]:
            open(f, "w").close()
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "old_string": '',
                "new_string": '{"role": "gdd", "ts": "2026-01-01T00:00:00Z"}\n',
            },
        })
        assert code == 0
        assert parsed is not None
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/gm-asset" in ctx


class TestValidation:
    def test_missing_required_files_blocked(self, project_dir):
        # No GDD/PLAN/STRUCTURE files
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "gdd", "ts": "2026-01-01T00:00:00Z"}]),
            },
        })
        assert is_blocked(parsed)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        assert "GDD.md" in reason or "PLAN.md" in reason

    def test_build_blocked_when_plan_has_pending(self, project_dir):
        with open("PLAN.md", "w") as f:
            f.write("# Plan\n| 1 | move | pending |\n")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "build", "ts": "2026-01-01T01:00:00Z"}]),
            },
        })
        assert is_blocked(parsed)

    def test_build_passes_when_plan_all_verified(self, project_dir):
        with open("PLAN.md", "w") as f:
            f.write("# Plan\n| 1 | move | verified |\n")
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": stage_jsonl([{"role": "build", "ts": "2026-01-01T01:00:00Z"}]),
            },
        })
        assert code == 0
        # Should produce a reminder, not block
        assert not is_blocked(parsed)


class TestEdgeCases:
    def test_invalid_json_content(self, project_dir):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": "not json",
            },
        })
        assert code == 0
        assert parsed is None

    def test_lines_without_role_or_ts_ignored(self, project_dir):
        """JSONL lines that lack role/ts fields should be skipped (no reminder)."""
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".godotmaker/stage.jsonl",
                "content": '{"other_field": 1}\n{"only_role": "setup"}\n',
            },
        })
        assert code == 0
        assert parsed is None
