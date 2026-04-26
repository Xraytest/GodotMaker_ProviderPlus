#!/usr/bin/env python3
"""Static project checker for GodotMaker-generated projects.

Validates that a Godot project meets GodotMaker requirements:
ECS setup, tests, planning documents, build readiness.

Usage:
    python tools/check_project.py <project_dir> --all
    python tools/check_project.py <project_dir> --ecs --tests --plan
"""
import argparse
import os
import re
import sys
from pathlib import Path

PLACEHOLDER_KEYWORDS = ["placeholder", "todo", "stub", "not implemented"]


class CheckResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def ok(self, msg: str):
        self.passed.append(msg)
        print(f"[PASS] {msg}")

    def fail(self, msg: str):
        self.failed.append(msg)
        print(f"[FAIL] {msg}")

    def warn(self, msg: str):
        self.warnings.append(msg)
        print(f"[WARN] {msg}")

    @property
    def success(self) -> bool:
        return len(self.failed) == 0


def find_gd_files(project_dir: Path, pattern: str) -> list[Path]:
    """Find .gd files matching a naming pattern."""
    results = []
    for root, _, files in os.walk(project_dir):
        # Skip addons, .godot, .claude directories
        rel = Path(root).relative_to(project_dir)
        parts = rel.parts
        if any(p.startswith(".") or p == "addons" for p in parts):
            continue
        for f in files:
            if f.endswith(".gd") and re.search(pattern, f):
                results.append(Path(root) / f)
    return results


def check_build(project_dir: Path, result: CheckResult):
    """Check that project.godot exists and basic structure is present."""
    print("\n--- Build Readiness ---")

    project_file = project_dir / "project.godot"
    if project_file.exists():
        result.ok("project.godot exists")
    else:
        result.fail("project.godot not found")
        return

    # Check project.godot has basic required sections
    content = project_file.read_text(encoding="utf-8", errors="replace")
    if "[application]" in content:
        result.ok("project.godot has [application] section")
    else:
        result.fail("project.godot missing [application] section")


def check_ecs(project_dir: Path, result: CheckResult):
    """Check ECS framework (gecs) setup."""
    print("\n--- ECS (gecs) ---")

    # Check gecs addon
    gecs_dir = project_dir / "addons" / "gecs"
    if gecs_dir.exists():
        result.ok(f"gecs addon found at {gecs_dir.relative_to(project_dir)}")
    else:
        result.fail("gecs addon not found (expected addons/gecs/)")

    # Check for Component files (files that extend Component or have Component in class)
    component_files = find_gd_files(project_dir, r"(?i)component|_comp")
    # Also check files that contain "extends Component" or "class_name.*Component"
    actual_components = []
    for gd_file in project_dir.rglob("*.gd"):
        rel = gd_file.relative_to(project_dir)
        if any(p.startswith(".") or p == "addons" for p in rel.parts):
            continue
        try:
            text = gd_file.read_text(encoding="utf-8", errors="replace")
            if "extends Component" in text or "extends GECSComponent" in text:
                actual_components.append(gd_file)
        except OSError:
            pass

    if actual_components:
        result.ok(f"Found {len(actual_components)} Component file(s): "
                  + ", ".join(f.stem for f in actual_components[:5]))
    else:
        if component_files:
            result.warn(f"Found {len(component_files)} files with 'component' in name, "
                       "but none extend Component class")
        else:
            result.fail("No Component files found (files extending Component)")

    # Check for System files
    actual_systems = []
    for gd_file in project_dir.rglob("*.gd"):
        rel = gd_file.relative_to(project_dir)
        if any(p.startswith(".") or p == "addons" for p in rel.parts):
            continue
        try:
            text = gd_file.read_text(encoding="utf-8", errors="replace")
            if "extends System" in text or "extends GECSSystem" in text:
                actual_systems.append(gd_file)
        except OSError:
            pass

    if actual_systems:
        result.ok(f"Found {len(actual_systems)} System file(s): "
                  + ", ".join(f.stem for f in actual_systems[:5]))
    else:
        result.fail("No System files found (files extending System)")


def check_tests(project_dir: Path, result: CheckResult):
    """Check that unit tests exist for systems."""
    print("\n--- Unit Tests (gdUnit4) ---")

    # Check gdUnit4 addon
    gdunit_dir = project_dir / "addons" / "gdunit4"
    if gdunit_dir.exists():
        result.ok("gdUnit4 addon found")
    else:
        result.fail("gdUnit4 addon not found (expected addons/gdunit4/)")

    # Find all system files
    system_files = []
    for gd_file in project_dir.rglob("*.gd"):
        rel = gd_file.relative_to(project_dir)
        if any(p.startswith(".") or p == "addons" for p in rel.parts):
            continue
        try:
            text = gd_file.read_text(encoding="utf-8", errors="replace")
            if "extends System" in text or "extends GECSSystem" in text:
                system_files.append(gd_file)
        except OSError:
            pass

    if not system_files:
        result.warn("No system files found — cannot check test coverage")
        return

    # Find test files
    test_files = []
    for gd_file in project_dir.rglob("*.gd"):
        rel = gd_file.relative_to(project_dir)
        if any(p.startswith(".") or p == "addons" for p in rel.parts):
            continue
        if "test" in str(rel).lower():
            test_files.append(gd_file)

    if test_files:
        result.ok(f"Found {len(test_files)} test file(s)")
    else:
        result.fail("No test files found")
        return

    # Check coverage: each system should have a corresponding test
    test_names = {f.stem.lower() for f in test_files}
    missing_tests = []
    for sys_file in system_files:
        sys_name = sys_file.stem.lower()
        # Look for test_xxx or xxx_test patterns
        has_test = any(
            f"test_{sys_name}" in t or f"{sys_name}_test" in t or f"test{sys_name}" in t
            for t in test_names
        )
        if not has_test:
            missing_tests.append(sys_file.stem)

    if missing_tests:
        result.fail(f"Systems without test files: {', '.join(missing_tests)}")
    else:
        result.ok(f"All {len(system_files)} systems have corresponding test files")


def check_e2e(project_dir: Path, result: CheckResult):
    """Check that e2e tests exist."""
    print("\n--- E2E Tests (godot-e2e) ---")

    # Check for godot-e2e plugin
    project_file = project_dir / "project.godot"
    has_plugin = False
    if project_file.exists():
        content = project_file.read_text(encoding="utf-8", errors="replace")
        if "godot_e2e/plugin.cfg" in content or "godot-e2e/plugin.cfg" in content:
            has_plugin = True
            result.ok("godot-e2e plugin enabled in project.godot")

    if not has_plugin:
        # Check for addon directory
        e2e_dir = project_dir / "addons" / "godot_e2e"
        e2e_dir2 = project_dir / "addons" / "godot-e2e"
        if e2e_dir.exists() or e2e_dir2.exists():
            result.warn("godot-e2e addon found but plugin not enabled in [editor_plugins]")
        else:
            result.fail("godot-e2e not found (no addon directory, plugin not enabled)")

    # Check for e2e test files in standard directory: tests/e2e/
    e2e_dir = project_dir / "tests" / "e2e"
    e2e_files = []
    if e2e_dir.exists():
        e2e_files = list(e2e_dir.glob("test_*.py"))

    # Fallback: check legacy locations (files with "e2e" in path)
    if not e2e_files:
        e2e_patterns = ["e2e", "end_to_end", "integration_test"]
        for py_file in project_dir.rglob("*.py"):
            rel = py_file.relative_to(project_dir)
            if any(p.startswith(".") or p in {"addons", "venv", "node_modules"} for p in rel.parts):
                continue
            if any(p in str(rel).lower() for p in e2e_patterns):
                e2e_files.append(py_file)

    # Check conftest.py exists
    conftest = e2e_dir / "conftest.py" if e2e_dir.exists() else None
    if conftest and conftest.exists():
        result.ok("tests/e2e/conftest.py exists")
    else:
        result.warn("tests/e2e/conftest.py not found — E2E tests may use wrong imports")

    if e2e_files:
        result.ok(f"Found {len(e2e_files)} e2e test file(s): "
                  + ", ".join(f.name for f in e2e_files[:5]))

        # Content quality checks for each e2e test file
        for e2e_file in e2e_files:
            try:
                content = e2e_file.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                continue

            if len(content) < 50:
                result.fail(f"e2e file {e2e_file.name} is too short "
                            f"({len(content)} chars) — likely a placeholder")
            elif not re.search(r"def test_", content):
                result.fail(f"e2e file {e2e_file.name} has no test functions "
                            "(expected 'def test_...')")
            elif any(kw in content.lower() for kw in PLACEHOLDER_KEYWORDS):
                result.warn(f"e2e file {e2e_file.name} may contain "
                            "placeholder content (TODO/stub)")
    else:
        result.fail("No e2e test files found in tests/e2e/")


def check_plan(project_dir: Path, result: CheckResult):
    """Check PLAN.md exists and has task statuses."""
    print("\n--- Planning Documents ---")

    plan_file = project_dir / "PLAN.md"
    if plan_file.exists():
        result.ok("PLAN.md exists")
        content = plan_file.read_text(encoding="utf-8", errors="replace")

        # Check for Task Status table
        if "Task Status" in content or "Status" in content:
            # Count tasks with status markers
            status_markers = re.findall(
                r"\|\s*(?:pending|in_progress|completed|failed|done|skip)\s*\|",
                content, re.IGNORECASE
            )
            if status_markers:
                result.ok(f"PLAN.md has {len(status_markers)} tasks with status")
            else:
                result.warn("PLAN.md has Status section but no task status markers found")
        else:
            result.fail("PLAN.md missing Task Status section")
    else:
        result.fail("PLAN.md not found")

    # Check STRUCTURE.md
    structure_file = project_dir / "STRUCTURE.md"
    if structure_file.exists():
        result.ok("STRUCTURE.md exists")
        content = structure_file.read_text(encoding="utf-8", errors="replace")

        has_components = ("Component" in content and
                         ("Registry" in content or "|" in content))
        has_systems = "System" in content and "Schedule" in content

        if has_components:
            result.ok("STRUCTURE.md has Component definitions")
        else:
            result.fail("STRUCTURE.md missing Component Registry")

        if has_systems:
            result.ok("STRUCTURE.md has System Schedule")
        else:
            result.fail("STRUCTURE.md missing System Schedule")
    else:
        result.fail("STRUCTURE.md not found")

    # Check MEMORY.md
    memory_file = project_dir / "MEMORY.md"
    if memory_file.exists():
        result.ok("MEMORY.md exists")
    else:
        result.warn("MEMORY.md not found (optional but recommended)")

    # Check ASSETS.md
    assets_file = project_dir / "ASSETS.md"
    if assets_file.exists():
        result.ok("ASSETS.md exists")
    else:
        result.warn("ASSETS.md not found (optional for text-only games)")


def check_mcp(project_dir: Path, result: CheckResult):
    """Check MCP server registration."""
    print("\n--- MCP (godot-mcp) ---")

    mcp_file = project_dir / ".mcp.json"
    if mcp_file.exists():
        content = mcp_file.read_text(encoding="utf-8", errors="replace")
        if '"godot"' in content:
            result.ok("godot-mcp registered in .mcp.json")
        else:
            result.warn(".mcp.json exists but no 'godot' server entry")
    else:
        result.warn(".mcp.json not found — godot-mcp not registered")


def main():
    parser = argparse.ArgumentParser(
        description="Check GodotMaker project structure and completeness"
    )
    parser.add_argument("project_dir", help="Path to the Godot project directory")
    parser.add_argument("--build", action="store_true", help="Check build readiness")
    parser.add_argument("--ecs", action="store_true", help="Check ECS (gecs) setup")
    parser.add_argument("--tests", action="store_true", help="Check unit test coverage")
    parser.add_argument("--e2e", action="store_true", help="Check e2e test setup")
    parser.add_argument("--plan", action="store_true", help="Check planning documents")
    parser.add_argument("--mcp", action="store_true", help="Check MCP registration")
    parser.add_argument("--all", action="store_true", help="Run all checks")

    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"Error: project directory does not exist: {project_dir}")
        sys.exit(2)

    run_all = args.all or not any([
        args.build, args.ecs, args.tests, args.e2e, args.plan, args.mcp
    ])

    result = CheckResult()

    print(f"Checking project: {project_dir}")

    if run_all or args.build:
        check_build(project_dir, result)
    if run_all or args.ecs:
        check_ecs(project_dir, result)
    if run_all or args.tests:
        check_tests(project_dir, result)
    if run_all or args.e2e:
        check_e2e(project_dir, result)
    if run_all or args.plan:
        check_plan(project_dir, result)
    if run_all or args.mcp:
        check_mcp(project_dir, result)

    # Summary
    print(f"\n{'='*50}")
    total = len(result.passed) + len(result.failed) + len(result.warnings)
    print(f"Total: {total} checks")
    print(f"  PASS: {len(result.passed)}")
    print(f"  FAIL: {len(result.failed)}")
    print(f"  WARN: {len(result.warnings)}")

    if result.success:
        print("\nResult: ALL CHECKS PASSED")
    else:
        print("\nResult: CHECKS FAILED")
        print("Failed checks:")
        for f in result.failed:
            print(f"  - {f}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
