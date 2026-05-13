#!/usr/bin/env python3
"""Mechanical /gm-verify runner.

Executes the four checks documented in
`skills/core/gm-verify/SKILL.md` "Verification Checklist" and emits a
JSON document matching the verify_report.json schema documented in the
same SKILL's "Output Format" Section B. The /gm-verify SKILL agent
reads this document, sanity-checks it, and writes the final
`.godotmaker/verify_report.json` plus the human-readable chat summary.

Why a script: verify is non-creative, checklist-driven. Driving four
bash invocations one-by-one through an agent costs $0.45-$1.71 and
1-2 minutes per run (per 2026-05-12 AAR). Bundling them lets the agent
keep its judgement role (escalation, future check additions) while
shedding the per-call LLM friction.

Usage:
    python tools/run_verify.py [--project-path <path>]

Output (stdout):
    JSON matching skills/core/gm-verify/SKILL.md Output Format Section B
    (verify_report.json shape). Per-check pass/fail is encoded in the
    JSON, not in the exit code.

Exit codes:
    0   ran to completion
    1   runtime failure (project state malformed, OS error, JSON encoding
        failure, etc.)
    2   bad CLI usage
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# Same flags as gm-verify/SKILL.md Section 4. `--all` deliberately not
# used: it adds `--e2e` which is the Evaluator's territory.
STATIC_CHECK_FLAGS = ["--build", "--ecs", "--tests", "--plan", "--mcp"]

# Per-check timeout (seconds). headless `godot --quit` is normally <10s
# but allow 60s for cold-start + project import. gdUnit4 can take
# minutes on big test suites; bound at 600s.
BUILD_TIMEOUT = 60
UNIT_TIMEOUT = 600
STATIC_TIMEOUT = 60


def _resolve_project_path(arg: str | None) -> Path:
    return Path(arg).resolve() if arg else Path.cwd()


def _read_godot_path(project_dir: Path) -> str:
    """Read `godot_path` from `.claude/godotmaker.yaml`.

    Falls back to plain `"godot"` (PATH lookup) when the file or field
    is missing, matching gm-verify/SKILL.md "Resolve `godot` binary"
    behaviour. A subsequent FileNotFoundError from subprocess surfaces
    the misconfiguration via a tooling_note.
    """
    config = project_dir / ".claude" / "godotmaker.yaml"
    if not config.exists():
        return "godot"
    for line in config.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("godot_path:"):
            val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            return val or "godot"
    return "godot"


def _now_iso_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tooling_note(tool: str, crashed_on: str, error: str,
                  fallback: str = "escalate") -> dict:
    """Build a tooling_notes entry. We always emit `escalate` here —
    this script is the producer and per gm-verify producer rule, when
    we can't fill a routable fallback's operand we MUST emit escalate.
    Routable fallbacks (exclude_file / scope_narrow / add_gdlintrc_rule
    / skip_check) are reserved for cases with a clear remediation; a
    script crash doesn't qualify.
    """
    return {
        "tool": tool,
        "crashed_on": crashed_on,
        "error": error,
        "suggested_fallback": fallback,
        "narrowed_command": None,
        "rule_name": None,
        "check_name": None,
    }


# ---------------------------------------------------------------------------
# 1. Build
# ---------------------------------------------------------------------------

_BUILD_ERROR_LINE = re.compile(r"^\s*ERROR:\s+(.+)$", re.MULTILINE)
_GD_LOC = re.compile(r"\s+at:\s+GDScript::\w+\s+\(([^:()]+):(\d+)\)")


def _next_error_offset(text: str, start: int) -> int:
    nxt = _BUILD_ERROR_LINE.search(text, start)
    return nxt.start() if nxt else len(text)


def check_build(godot_path: str, project_dir: Path
                ) -> tuple[dict, dict | None]:
    """Run `<godot_path> --headless --quit` and parse ERROR lines."""
    try:
        proc = subprocess.run(
            [godot_path, "--headless", "--path", str(project_dir), "--quit"],
            capture_output=True, text=True, timeout=BUILD_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return (
            {"result": "error", "errors": []},
            _tooling_note(
                tool="godot",
                crashed_on="<headless-run>",
                error=f"godot --headless --quit timed out after {BUILD_TIMEOUT}s",
            ),
        )
    except FileNotFoundError as ex:
        return (
            {"result": "error", "errors": []},
            _tooling_note(
                tool="godot",
                crashed_on=godot_path,
                error=(
                    f"godot binary not found: {ex}. Set godot_path in "
                    f".claude/godotmaker.yaml or ensure godot is on PATH."
                ),
            ),
        )

    combined = (proc.stdout or "") + (proc.stderr or "")
    errors: list[dict] = []
    for m in _BUILD_ERROR_LINE.finditer(combined):
        bound = _next_error_offset(combined, m.end())
        loc_match = _GD_LOC.search(combined, m.end(), bound)
        entry: dict = {
            "file": loc_match.group(1) if loc_match else "",
            "line": int(loc_match.group(2)) if loc_match else 0,
            "message": m.group(1).strip(),
        }
        errors.append(entry)

    result = "fail" if errors else "pass"
    return ({"result": result, "errors": errors}, None)


# ---------------------------------------------------------------------------
# 2. Unit Tests
# ---------------------------------------------------------------------------

# gdUnit4 CmdTool prints a summary line we can pin against. Two shapes
# observed across stream logs:
#   "267 test cases | 0 errors | 0 failures (31 suites, exit 0)"
#   "Tests Passed: 274 | Tests Failed: 0"
_GDUNIT_SUMMARY_CASES = re.compile(
    r"(\d+)\s+test\s*cases?\s*\|\s*(\d+)\s+errors?\s*\|\s*(\d+)\s+failures?",
    re.IGNORECASE,
)
_GDUNIT_SUMMARY_PF = re.compile(
    r"Tests?\s+Passed:\s*(\d+).*?Tests?\s+Failed:\s*(\d+)",
    re.IGNORECASE | re.DOTALL,
)
# Per-failure lines. gdUnit4 prints "FAILED: <test_id> - <message>",
# where <test_id> may contain `::` (suite::test). Lazy-match the id and
# require a space-dash-space separator so the `::` does not split.
_GDUNIT_FAILURE = re.compile(
    r"^\s*FAILED:\s*(.+?)\s+-\s+(.+)$",
    re.MULTILINE,
)


def check_unit_tests(godot_path: str, project_dir: Path
                     ) -> tuple[dict, dict | None]:
    cmd = [
        godot_path, "--headless",
        "--path", str(project_dir),
        "-s", "addons/gdUnit4/bin/GdUnitCmdTool.gd",
        "--ignoreHeadlessMode",
        "--add", "test/",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=UNIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (
            {"result": "error", "passed": 0, "failed": 0, "failures": []},
            _tooling_note(
                tool="gdunit",
                crashed_on="<headless-run>",
                error=f"gdUnit4 timed out after {UNIT_TIMEOUT}s",
            ),
        )
    except FileNotFoundError as ex:
        return (
            {"result": "error", "passed": 0, "failed": 0, "failures": []},
            _tooling_note(
                tool="gdunit",
                crashed_on=godot_path,
                error=f"godot binary not found: {ex}",
            ),
        )

    combined = (proc.stdout or "") + (proc.stderr or "")

    m = _GDUNIT_SUMMARY_CASES.search(combined)
    if m:
        total = int(m.group(1))
        errs = int(m.group(2))
        fails = int(m.group(3))
        failed_count = errs + fails
        passed_count = max(total - failed_count, 0)
    else:
        m2 = _GDUNIT_SUMMARY_PF.search(combined)
        if m2:
            passed_count = int(m2.group(1))
            failed_count = int(m2.group(2))
        else:
            return (
                {"result": "error", "passed": 0, "failed": 0, "failures": []},
                _tooling_note(
                    tool="gdunit",
                    crashed_on="<headless-run>",
                    error=(
                        "could not parse gdUnit4 summary line; runner may "
                        "have crashed or test/ may be empty"
                    ),
                ),
            )

    failures: list[dict] = []
    for fm in _GDUNIT_FAILURE.finditer(combined):
        failures.append({
            "test": fm.group(1).strip(),
            "message": fm.group(2).strip(),
        })

    result = "fail" if failed_count > 0 else "pass"
    return (
        {
            "result": result,
            "passed": passed_count,
            "failed": failed_count,
            "failures": failures,
        },
        None,
    )


# ---------------------------------------------------------------------------
# 3. Lint — gdtoolkit currently disabled (gm-verify SKILL Section 3)
# ---------------------------------------------------------------------------

def check_lint() -> dict:
    return {"result": "pass", "issues": [], "format_drift": None}


# ---------------------------------------------------------------------------
# 4. Static check (delegates to tools/check_project.py)
# ---------------------------------------------------------------------------

_STATIC_FAIL_LINE = re.compile(r"^\[FAIL\]\s+(.+)$", re.MULTILINE)


def check_static(project_dir: Path) -> tuple[dict, dict | None]:
    check_project = Path(__file__).parent / "check_project.py"
    if not check_project.exists():
        return (
            {"result": "error", "issues": []},
            _tooling_note(
                tool="check_project",
                crashed_on=str(check_project),
                error="check_project.py not found alongside run_verify.py",
            ),
        )

    cmd = [sys.executable, str(check_project), str(project_dir)] + STATIC_CHECK_FLAGS
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=STATIC_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (
            {"result": "error", "issues": []},
            _tooling_note(
                tool="check_project",
                crashed_on=str(project_dir),
                error=f"check_project.py timed out after {STATIC_TIMEOUT}s",
            ),
        )

    combined = (proc.stdout or "") + (proc.stderr or "")
    issues: list[dict] = []
    for m in _STATIC_FAIL_LINE.finditer(combined):
        detail = m.group(1).strip()
        if ":" in detail:
            check_name, _, rest = detail.partition(":")
            issues.append({"check": check_name.strip(), "detail": rest.strip()})
        else:
            issues.append({"check": "static_check", "detail": detail})

    result = "fail" if issues else "pass"
    return ({"result": result, "issues": issues}, None)


# ---------------------------------------------------------------------------
# Compose final report
# ---------------------------------------------------------------------------

def build_report(project_dir: Path) -> dict[str, Any]:
    godot_path = _read_godot_path(project_dir)

    build_dict, build_note = check_build(godot_path, project_dir)
    unit_dict, unit_note = check_unit_tests(godot_path, project_dir)
    lint_dict = check_lint()
    static_dict, static_note = check_static(project_dir)

    notes: list[dict] = [n for n in (build_note, unit_note, static_note) if n]

    per_check_results = {
        build_dict["result"], unit_dict["result"],
        lint_dict["result"], static_dict["result"],
    }
    # Top-level pass iff every per-check result ∈ {pass, warn}.
    overall = "pass" if per_check_results <= {"pass", "warn"} else "fail"

    return {
        "result": overall,
        "ts": _now_iso_utc(),
        "checks": {
            "build": build_dict,
            "unit_tests": unit_dict,
            "lint": lint_dict,
            "static_check": static_dict,
        },
        "tooling_notes": notes,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run /gm-verify checks mechanically and emit the "
            "verify_report.json shape to stdout."
        ),
    )
    parser.add_argument(
        "--project-path", default=None,
        help="project root (default: current working directory)",
    )
    args = parser.parse_args(argv)

    project_dir = _resolve_project_path(args.project_path)
    if not (project_dir / ".godotmaker").is_dir():
        print(
            f"error: {project_dir} is not a godotmaker project "
            f"(.godotmaker/ missing)",
            file=sys.stderr,
        )
        return 1

    try:
        report = build_report(project_dir)
    except OSError as ex:
        print(f"error: build_report failed: {ex}", file=sys.stderr)
        return 1

    try:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    except (UnicodeError, ValueError) as ex:
        print(f"error: failed to encode report as JSON: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
