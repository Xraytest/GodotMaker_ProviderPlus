"""Tests for check_project.py."""
import os
import subprocess
import sys
import pytest
import tempfile

# tests/tools/ → project_root/tools/
CHECK_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools", "check_project.py"
)


def run_check(project_dir: str, *flags: str) -> tuple[str, int]:
    """Run check_project.py and return (stdout, exit_code)."""
    result = subprocess.run(
        [sys.executable, CHECK_SCRIPT, project_dir, *flags],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout, result.returncode


@pytest.fixture
def project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestBuildCheck:
    def test_no_project_godot(self, project_dir):
        stdout, code = run_check(project_dir, "--build")
        assert code == 1
        assert "[FAIL]" in stdout
        assert "project.godot" in stdout

    def test_with_project_godot(self, project_dir):
        with open(os.path.join(project_dir, "project.godot"), "w") as f:
            f.write("[application]\nconfig/name=\"Test\"\n")
        stdout, code = run_check(project_dir, "--build")
        assert code == 0
        assert "[PASS]" in stdout

    def test_missing_application_section(self, project_dir):
        with open(os.path.join(project_dir, "project.godot"), "w") as f:
            f.write("[rendering]\n")
        stdout, code = run_check(project_dir, "--build")
        assert code == 1
        assert "[FAIL]" in stdout
        assert "[application]" in stdout


class TestEcsCheck:
    def test_no_gecs_addon(self, project_dir):
        stdout, code = run_check(project_dir, "--ecs")
        assert code == 1
        assert "[FAIL]" in stdout
        assert "gecs" in stdout

    def test_with_gecs_and_components(self, project_dir):
        os.makedirs(os.path.join(project_dir, "addons", "gecs"))
        comp_dir = os.path.join(project_dir, "components")
        os.makedirs(comp_dir)
        with open(os.path.join(comp_dir, "health.gd"), "w") as f:
            f.write("extends Component\nvar current: int = 100\n")
        sys_dir = os.path.join(project_dir, "systems")
        os.makedirs(sys_dir)
        with open(os.path.join(sys_dir, "movement_system.gd"), "w") as f:
            f.write("extends System\nfunc _process(delta):\n\tpass\n")

        stdout, code = run_check(project_dir, "--ecs")
        assert code == 0
        assert "[PASS]" in stdout


class TestTestsCheck:
    def test_no_gdunit(self, project_dir):
        stdout, code = run_check(project_dir, "--tests")
        assert code == 1
        assert "gdUnit4" in stdout

    def test_system_without_test(self, project_dir):
        os.makedirs(os.path.join(project_dir, "addons", "gdunit4"))
        sys_dir = os.path.join(project_dir, "systems")
        os.makedirs(sys_dir)
        with open(os.path.join(sys_dir, "move.gd"), "w") as f:
            f.write("extends System\n")

        stdout, code = run_check(project_dir, "--tests")
        assert code == 1
        assert "[FAIL]" in stdout
        assert "test" in stdout.lower()

    def test_system_with_test(self, project_dir):
        os.makedirs(os.path.join(project_dir, "addons", "gdunit4"))
        sys_dir = os.path.join(project_dir, "systems")
        os.makedirs(sys_dir)
        with open(os.path.join(sys_dir, "move.gd"), "w") as f:
            f.write("extends System\n")
        test_dir = os.path.join(project_dir, "test")
        os.makedirs(test_dir)
        with open(os.path.join(test_dir, "test_move.gd"), "w") as f:
            f.write("extends GdUnitTestSuite\n")

        stdout, code = run_check(project_dir, "--tests")
        assert code == 0


class TestPlanCheck:
    def test_no_plan(self, project_dir):
        stdout, code = run_check(project_dir, "--plan")
        assert code == 1
        assert "PLAN.md" in stdout

    def test_with_plan_and_structure(self, project_dir):
        with open(os.path.join(project_dir, "PLAN.md"), "w") as f:
            f.write("# Plan\n## Task Status\n| 1 | Move | completed | done |\n")
        with open(os.path.join(project_dir, "STRUCTURE.md"), "w") as f:
            f.write("# Structure\n## Component Registry\n## System Schedule\n")

        stdout, code = run_check(project_dir, "--plan")
        assert code == 0
        assert "[PASS]" in stdout


class TestAllCheck:
    def test_empty_project_fails(self, project_dir):
        stdout, code = run_check(project_dir, "--all")
        assert code == 1
        assert "[FAIL]" in stdout
        assert "Result: CHECKS FAILED" in stdout

    def test_summary_counts(self, project_dir):
        stdout, code = run_check(project_dir, "--all")
        assert "Total:" in stdout
        assert "PASS:" in stdout
        assert "FAIL:" in stdout
