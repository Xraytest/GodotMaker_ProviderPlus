"""Tests for tools/run_verify.py — the mechanical /gm-verify runner.

Subprocess is mocked at the module-under-test level (`run_verify.subprocess.run`)
to avoid actually launching godot. The composed report is then validated
against `tests/test_verify_report_fixtures.validate_report` so producer
output stays pinned to the schema the build/fixgap consumers expect.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "run_verify.py"


def _load_run_verify():
    spec = importlib.util.spec_from_file_location("run_verify_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_verify = _load_run_verify()

# Reuse the schema validator that pins the producer/consumer contract.
sys.path.insert(0, str(REPO_ROOT / "tests"))
from test_verify_report_fixtures import validate_report  # noqa: E402


def _make_proc(stdout: str = "", stderr: str = "", returncode: int = 0):
    p = MagicMock()
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / ".godotmaker").mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "godotmaker.yaml").write_text(
        'godot_path: "/usr/bin/godot"\n'
    )
    return tmp_path


# ---------- build ----------

def test_check_build_pass():
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout="Setting Up MainLoop...\nDone.\n")
        result, note = run_verify.check_build("/usr/bin/godot", Path("/x"))
    assert result == {"result": "pass", "errors": []}
    assert note is None


def test_check_build_fail_with_errors_and_locations():
    output = (
        "ERROR: Parse Error: Identifier 'bar' not declared.\n"
        "   at: GDScript::reload (src/foo.gd:42)\n"
        "ERROR: Failed loading resource: res://scenes/main.tscn.\n"
    )
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output)
        result, note = run_verify.check_build("/usr/bin/godot", Path("/x"))
    assert result["result"] == "fail"
    assert len(result["errors"]) == 2
    assert result["errors"][0]["file"] == "src/foo.gd"
    assert result["errors"][0]["line"] == 42
    assert "Identifier 'bar'" in result["errors"][0]["message"]
    # Second ERROR has no GDScript location → file empty, line 0
    assert result["errors"][1]["file"] == ""
    assert result["errors"][1]["line"] == 0
    assert note is None


def test_check_build_locations_are_scoped_to_each_error():
    """A GDScript location after ERROR_B must not be attributed to ERROR_A."""
    output = (
        "ERROR: Cannot open file 'res://scenes/main.tscn'.\n"
        "ERROR: Parse Error.\n"
        "   at: GDScript::reload (src/bar.gd:7)\n"
    )
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output)
        result, _ = run_verify.check_build("/usr/bin/godot", Path("/x"))
    assert result["errors"][0]["file"] == ""
    assert result["errors"][0]["line"] == 0
    assert result["errors"][1]["file"] == "src/bar.gd"
    assert result["errors"][1]["line"] == 7


def test_check_build_timeout_returns_escalate():
    with patch.object(
        run_verify.subprocess, "run",
        side_effect=subprocess.TimeoutExpired(cmd="godot", timeout=60),
    ):
        result, note = run_verify.check_build("/usr/bin/godot", Path("/x"))
    assert result["result"] == "error"
    assert result["errors"] == []
    assert note["tool"] == "godot"
    assert note["suggested_fallback"] == "escalate"


def test_check_build_missing_binary_returns_escalate():
    with patch.object(
        run_verify.subprocess, "run", side_effect=FileNotFoundError("no godot"),
    ):
        result, note = run_verify.check_build("nope-godot", Path("/x"))
    assert result["result"] == "error"
    assert note["tool"] == "godot"
    assert note["crashed_on"] == "nope-godot"


# ---------- unit tests ----------

def test_check_unit_tests_pass_with_cases_summary():
    output = "267 test cases | 0 errors | 0 failures (31 suites, exit 0)\n"
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output)
        result, note = run_verify.check_unit_tests("/usr/bin/godot", Path("/x"))
    assert result == {"result": "pass", "passed": 267, "failed": 0, "failures": []}
    assert note is None


def test_check_unit_tests_pass_with_pf_summary():
    output = "Tests Passed: 274 | Tests Failed: 0 (some other text)\n"
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output)
        result, note = run_verify.check_unit_tests("/usr/bin/godot", Path("/x"))
    assert result["result"] == "pass"
    assert result["passed"] == 274
    assert result["failed"] == 0
    assert note is None


def test_check_unit_tests_fail_with_failures():
    output = (
        "267 test cases | 0 errors | 2 failures (31 suites, exit 1)\n"
        "FAILED: test_player::test_jump - expected 10, got 0\n"
        "FAILED: test_hud::test_score - expected 100, got 50\n"
    )
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output, returncode=1)
        result, note = run_verify.check_unit_tests("/usr/bin/godot", Path("/x"))
    assert result["result"] == "fail"
    assert result["passed"] == 265
    assert result["failed"] == 2
    assert len(result["failures"]) == 2
    assert result["failures"][0] == {
        "test": "test_player::test_jump",
        "message": "expected 10, got 0",
    }
    assert note is None


def test_check_unit_tests_errors_count_as_failed():
    """gdUnit4 reports errors separately from failures; both contribute to
    'failed' from the consumer's perspective (test runner result was not
    a clean pass)."""
    output = "100 test cases | 3 errors | 1 failures (10 suites, exit 1)\n"
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output)
        result, _ = run_verify.check_unit_tests("/usr/bin/godot", Path("/x"))
    assert result["failed"] == 4
    assert result["passed"] == 96


def test_check_unit_tests_unparseable_output_is_error():
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout="??? garbage ???\n")
        result, note = run_verify.check_unit_tests("/usr/bin/godot", Path("/x"))
    assert result["result"] == "error"
    assert note["tool"] == "gdunit"
    assert note["suggested_fallback"] == "escalate"


def test_check_unit_tests_timeout_is_error():
    with patch.object(
        run_verify.subprocess, "run",
        side_effect=subprocess.TimeoutExpired(cmd="godot", timeout=600),
    ):
        result, note = run_verify.check_unit_tests("/usr/bin/godot", Path("/x"))
    assert result["result"] == "error"
    assert result == {"result": "error", "passed": 0, "failed": 0, "failures": []}
    assert note["suggested_fallback"] == "escalate"


# ---------- lint ----------

def test_check_lint_is_always_pass_with_null_format_drift():
    """gdtoolkit is disabled pipeline-wide; lint always emits a stub pass."""
    assert run_verify.check_lint() == {
        "result": "pass", "issues": [], "format_drift": None,
    }


# ---------- static check ----------

def test_check_static_pass():
    output = "[PASS] project.godot exists\n[PASS] tests directory exists\n"
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output)
        result, note = run_verify.check_static(Path("/x"))
    assert result == {"result": "pass", "issues": []}
    assert note is None


def test_check_static_fail_parses_check_name_prefix():
    output = (
        "[PASS] project.godot exists\n"
        "[FAIL] missing_unit_test: s_hud has no test file\n"
        "[FAIL] orphan_test: test_x.gd refers to deleted system\n"
    )
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output, returncode=1)
        result, note = run_verify.check_static(Path("/x"))
    assert result["result"] == "fail"
    assert result["issues"] == [
        {"check": "missing_unit_test", "detail": "s_hud has no test file"},
        {"check": "orphan_test", "detail": "test_x.gd refers to deleted system"},
    ]
    assert note is None


def test_check_static_fail_without_check_prefix():
    output = "[FAIL] something generic went wrong\n"
    with patch.object(run_verify.subprocess, "run") as run:
        run.return_value = _make_proc(stdout=output, returncode=1)
        result, _ = run_verify.check_static(Path("/x"))
    assert result["issues"] == [
        {"check": "static_check", "detail": "something generic went wrong"},
    ]


def test_check_static_timeout_is_error():
    with patch.object(
        run_verify.subprocess, "run",
        side_effect=subprocess.TimeoutExpired(cmd="check_project", timeout=60),
    ):
        result, note = run_verify.check_static(Path("/x"))
    assert result["result"] == "error"
    assert result["issues"] == []
    assert note["tool"] == "check_project"


# ---------- godot_path resolution ----------

def test_read_godot_path_returns_configured_value(project_dir: Path):
    assert run_verify._read_godot_path(project_dir) == "/usr/bin/godot"


def test_read_godot_path_falls_back_to_godot_when_missing(tmp_path: Path):
    """SKILL says fall back to plain 'godot' when the yaml is absent."""
    (tmp_path / ".godotmaker").mkdir()
    assert run_verify._read_godot_path(tmp_path) == "godot"


def test_read_godot_path_falls_back_when_field_empty(tmp_path: Path):
    (tmp_path / ".godotmaker").mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "godotmaker.yaml").write_text("godot_path: \n")
    assert run_verify._read_godot_path(tmp_path) == "godot"


# ---------- build_report composition ----------

def _fake_run_factory(*, build="ok", unit="ok", static="ok"):
    """Build a subprocess.run fake. Each arg selects per-tool behaviour:

    - "ok"      → clean pass output
    - "fail"    → output that parses to a failing result
    - "timeout" → raise TimeoutExpired
    """
    BUILD_OK = "Setting Up MainLoop...\nDone.\n"
    BUILD_FAIL = "ERROR: Cannot open file 'res://x.tscn'.\n"
    UNIT_OK = "100 test cases | 0 errors | 0 failures (10 suites, exit 0)\n"
    UNIT_FAIL = (
        "100 test cases | 0 errors | 1 failures (10 suites, exit 1)\n"
        "FAILED: test_x::test_y - boom\n"
    )
    STATIC_OK = "[PASS] all good\n"
    STATIC_FAIL = "[FAIL] missing_unit_test: s_hud has no test file\n"

    def fake_run(cmd, *args, **kwargs):
        # Identify which check this call is from.
        cmd_str = " ".join(str(c) for c in cmd)
        if "GdUnitCmdTool" in cmd_str:
            if unit == "timeout":
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=600)
            return _make_proc(stdout=UNIT_FAIL if unit == "fail" else UNIT_OK)
        if "check_project.py" in cmd_str:
            if static == "timeout":
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=60)
            return _make_proc(stdout=STATIC_FAIL if static == "fail" else STATIC_OK)
        # Otherwise: godot --headless --quit
        if build == "timeout":
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=60)
        return _make_proc(stdout=BUILD_FAIL if build == "fail" else BUILD_OK)
    return fake_run


def test_build_report_all_pass_is_schema_valid(project_dir: Path):
    with patch.object(run_verify.subprocess, "run",
                      side_effect=_fake_run_factory()):
        report = run_verify.build_report(project_dir)
    assert report["result"] == "pass"
    assert report["tooling_notes"] == []
    assert report["checks"]["lint"]["format_drift"] is None
    assert validate_report(report) == []


def test_build_report_unit_fail_makes_overall_fail(project_dir: Path):
    with patch.object(run_verify.subprocess, "run",
                      side_effect=_fake_run_factory(unit="fail")):
        report = run_verify.build_report(project_dir)
    assert report["result"] == "fail"
    assert report["checks"]["unit_tests"]["failed"] == 1
    assert validate_report(report) == []


def test_build_report_build_timeout_pairs_with_tooling_note(project_dir: Path):
    with patch.object(run_verify.subprocess, "run",
                      side_effect=_fake_run_factory(build="timeout")):
        report = run_verify.build_report(project_dir)
    assert report["result"] == "fail"
    assert report["checks"]["build"]["result"] == "error"
    notes = report["tooling_notes"]
    assert len(notes) == 1
    assert notes[0]["tool"] == "godot"
    assert notes[0]["suggested_fallback"] == "escalate"
    assert validate_report(report) == []


def test_build_report_multiple_tool_errors_emit_multiple_notes(project_dir: Path):
    """build + static both timing out → 2 entries in tooling_notes."""
    with patch.object(
        run_verify.subprocess, "run",
        side_effect=_fake_run_factory(build="timeout", static="timeout"),
    ):
        report = run_verify.build_report(project_dir)
    assert report["result"] == "fail"
    tools = sorted(n["tool"] for n in report["tooling_notes"])
    assert tools == ["check_project", "godot"]
    assert validate_report(report) == []


def test_build_report_static_fail_is_schema_valid(project_dir: Path):
    with patch.object(run_verify.subprocess, "run",
                      side_effect=_fake_run_factory(static="fail")):
        report = run_verify.build_report(project_dir)
    assert report["result"] == "fail"
    assert report["checks"]["static_check"]["issues"][0]["check"] == "missing_unit_test"
    assert validate_report(report) == []


# ---------- main / CLI ----------

def test_main_missing_godotmaker_dir_returns_1(tmp_path: Path, capsys):
    rc = run_verify.main(["--project-path", str(tmp_path)])
    assert rc == 1
    assert "not a godotmaker project" in capsys.readouterr().err


def test_main_emits_json_to_stdout(project_dir: Path, capsys):
    with patch.object(run_verify.subprocess, "run",
                      side_effect=_fake_run_factory()):
        rc = run_verify.main(["--project-path", str(project_dir)])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert validate_report(parsed) == []
    assert parsed["result"] == "pass"
    assert "ts" in parsed and parsed["ts"].endswith("Z")


def test_main_defaults_to_cwd(project_dir: Path, capsys, monkeypatch):
    monkeypatch.chdir(project_dir)
    with patch.object(run_verify.subprocess, "run",
                      side_effect=_fake_run_factory()):
        rc = run_verify.main([])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["result"] == "pass"


def test_main_subprocess_invocation_real(project_dir: Path):
    """End-to-end via real subprocess — godot/gdunit/check_project all fail
    to launch, so we expect rc=0 with a JSON whose checks.* are 'error'.

    Important: this guards against the script breaking at import time
    (syntax errors, missing imports) — the rest of the file mocks at
    module level and would miss those.
    """
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--project-path", str(project_dir)],
        capture_output=True, text=True, timeout=30,
        # Avoid hitting a real godot on the dev machine: point PATH at an
        # empty dir for this call.
        env={**os.environ, "PATH": str(project_dir)},
    )
    assert proc.returncode == 0, proc.stderr
    parsed = json.loads(proc.stdout)
    # godot not on PATH → build + unit are 'error'. Lint stub-passes.
    assert parsed["checks"]["build"]["result"] == "error"
    assert parsed["checks"]["unit_tests"]["result"] == "error"
    assert parsed["checks"]["lint"]["result"] == "pass"
    # check_project.py runs (sys.executable is still found) so static_check
    # depends on whether it errors out on the empty project; tolerate
    # either pass or fail/error here — the assertion that matters is that
    # the script ran end-to-end and produced a schema-valid JSON.
    assert validate_report(parsed) == []
