"""Tests for check_worker_report.py hook."""
import json
import os
import shutil

import pytest
from .helpers import run_hook, is_blocked, cleanup_metrics

HOOK = "check_worker_report.py"

COMPLETE_WORKER = (
    "## Report: PlayerMovement\n\n"
    "### Status: DONE\n\n"
    "### Files Changed\n- player_system.gd: created\n- e2e/test_player_e2e.gd: created\n\n"
    "### Tests\n#### Unit Tests\n- test/test_player.gd: 3 tests, 3 passed\n"
    "- Commands run: godot --headless\n"
    "#### E2E Tests\n- e2e/test_player_e2e.gd: e2e scenario 1 passed, 0 failed\n"
    "- Commands run: godot-e2e tests/e2e/\n\n"
    "### Build\n- Status: PASS\n\n"
    "### Memory Entry\nLearned about movement"
)

COMPLETE_VERIFIER = (
    "## Verification Report: Integration\n\n"
    "### Overall: PASS\n\n"
    "### Results\n### Check: build\n**Command run:** godot --headless\n\n"
    "### Adversarial Probes\n### Check: boundary\n**Command run:** test edge"
)

COMPLETE_REVIEWER = (
    "## Review Report: PlayerSystem\n\n"
    "### Reviewers Matched\n| physics | yes | uses CharacterBody2D |\n\n"
    "### ECS Review\n- Components pure data: PASS — C_Velocity and C_Health contain only exported vars, no logic\n"
    "- System read/write declarations match actual usage in process() — verified DAG is clean\n\n"
    "### Issues Found\n| # | Severity | Domain | Issue | Location |\n"
    "| 1 | minor | physics | collision mask not set for enemy layer | player.gd:10 |\n\n"
    "### Summary\n1 minor issue found, no critical blockers"
)


@pytest.fixture(autouse=True)
def clean():
    yield
    cleanup_metrics()


class TestWorkerReport:
    def test_complete_report_allowed(self):
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": COMPLETE_WORKER,
        })
        assert not is_blocked(parsed)

    @pytest.mark.parametrize("missing_section,remove", [
        ("Status", "### Status: DONE"),
        ("Tests", "### Tests"),
        ("Build", "### Build"),
        ("Memory Entry", "### Memory Entry"),
    ])
    def test_missing_section_blocked(self, missing_section, remove):
        msg = COMPLETE_WORKER.replace(remove, "### REMOVED")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), f"Should block when {missing_section} missing"

    def test_empty_tests_section_blocked(self):
        msg = COMPLETE_WORKER.replace(
            "#### Unit Tests\n- test/test_player.gd: 3 tests, 3 passed\n"
            "- Commands run: godot --headless\n"
            "#### E2E Tests\n- e2e/test_player_e2e.gd: e2e scenario 1 passed, 0 failed\n"
            "- Commands run: godot-e2e tests/e2e/",
            "Nothing here"
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), "Should block when Tests section has no substance"

    def test_missing_e2e_blocked(self):
        msg = COMPLETE_WORKER.replace(
            "#### E2E Tests\n- e2e/test_player_e2e.gd: e2e scenario 1 passed, 0 failed\n"
            "- Commands run: godot-e2e tests/e2e/",
            ""
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), "Should block when e2e mention missing"


class TestVerifierReport:
    def test_complete_report_allowed(self):
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "v1",
            "last_assistant_message": COMPLETE_VERIFIER,
        })
        assert not is_blocked(parsed)

    def test_missing_adversarial_blocked(self):
        msg = COMPLETE_VERIFIER.replace("### Adversarial Probes", "### REMOVED")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "v1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed)


class TestReviewerReport:
    def test_complete_report_allowed(self):
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "r1",
            "last_assistant_message": COMPLETE_REVIEWER,
        })
        assert not is_blocked(parsed)

    @pytest.mark.parametrize("section", [
        "### Reviewers Matched", "### ECS Review",
        "### Issues Found", "### Summary",
    ])
    def test_missing_section_blocked(self, section):
        msg = COMPLETE_REVIEWER.replace(section, "### REMOVED")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "r1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed)


class TestE2ERunResults:
    """Tests that worker reports must include actual e2e run results, not just file paths."""

    def test_e2e_mention_without_results_blocked(self):
        """e2e mentioned but no pass/fail output → blocked."""
        msg = COMPLETE_WORKER.replace(
            "e2e scenario 1 passed, 0 failed",
            "test file created"
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), "Should block when e2e has no run results"

    def test_e2e_placeholder_in_results_blocked(self):
        """e2e results say 'placeholder' → blocked."""
        msg = COMPLETE_WORKER.replace(
            "e2e scenario 1 passed, 0 failed",
            "e2e: placeholder ready, 0 scenarios"
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), "Should block when e2e results are placeholder"

    def test_e2e_with_actual_results_allowed(self):
        """e2e with real pass/fail output → allowed."""
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": COMPLETE_WORKER,
        })
        assert not is_blocked(parsed)


class TestFlexibleMarkerDetection:
    """Tests that report type is detected even with heading level variations."""

    def test_single_hash_worker(self):
        msg = COMPLETE_WORKER.replace("## Report:", "# Report:")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed)

    def test_triple_hash_worker(self):
        msg = COMPLETE_WORKER.replace("## Report:", "### Report:")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed)

    def test_triple_hash_verifier(self):
        msg = COMPLETE_VERIFIER.replace("## Verification Report:", "### Verification Report:")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "v1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed)

    def test_triple_hash_reviewer(self):
        msg = COMPLETE_REVIEWER.replace("## Review Report:", "### Review Report:")
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "r1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed)

    def test_fallback_worker_by_status_section(self):
        """Worker detected by Status section when heading is missing entirely."""
        msg = (
            "Here is my report.\n\n"
            "### Status: DONE\n\n"
            "### Files Changed\n- player_system.gd: created\n- e2e/test_player_e2e.gd: created\n\n"
            "### Tests\n#### Unit Tests\n- test/test_player.gd: 3 tests, 3 passed\n"
            "- Commands run: godot --headless\n"
            "#### E2E Tests\n- e2e/test_player_e2e.gd: e2e scenario 1 passed, 0 failed\n"
            "- Commands run: godot-e2e tests/e2e/\n\n"
            "### Build\n- Status: PASS\n\n"
            "### Memory Entry\nLearned about movement"
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed)

    def test_fallback_verifier_by_overall_section(self):
        """Verifier detected by Overall section when heading is missing."""
        msg = (
            "Verification complete.\n\n"
            "### Overall: PASS\n\n"
            "### Results\n### Check: build\n**Command run:** godot --headless\n\n"
            "### Adversarial Probes\n### Check: boundary\n**Command run:** test edge"
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "v1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed)


class TestEdgeCases:
    def test_unknown_report_type_allowed(self):
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "x1",
            "last_assistant_message": "Just a regular message",
        })
        assert code == 0
        assert not is_blocked(parsed)

    def test_non_stop_event_ignored(self):
        _, code, _ = run_hook(HOOK, {
            "hook_event_name": "SubagentStart",
            "agent_id": "w1",
        })
        assert code == 0

    def test_empty_message(self):
        _, code, _ = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "w1",
            "last_assistant_message": "",
        })
        assert code == 0


class TestDeadloopProtection:
    """Tests for per-agent block counter and force-allow after BLOCK_LIMIT."""

    def _block_agent_n_times(self, agent_id: str, n: int):
        """Send a bad report n times to accumulate blocks."""
        msg = COMPLETE_WORKER.replace("### Status: DONE", "### REMOVED")
        for _ in range(n):
            run_hook(HOOK, {
                "hook_event_name": "SubagentStop",
                "agent_id": agent_id,
                "last_assistant_message": msg,
            })

    def test_blocks_under_limit(self):
        """Agent blocked fewer than BLOCK_LIMIT (2) times is still blocked."""
        msg = COMPLETE_WORKER.replace("### Status: DONE", "### REMOVED")
        self._block_agent_n_times("dl1", 1)
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "dl1",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), "Should still block under limit"

    def test_force_allow_at_limit(self):
        """Agent blocked BLOCK_LIMIT (2) times is force-allowed."""
        msg = COMPLETE_WORKER.replace("### Status: DONE", "### REMOVED")
        self._block_agent_n_times("dl2", 2)
        # Next attempt should be force-allowed (output on stderr, not stdout)
        _, code, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "dl2",
            "last_assistant_message": msg,
        })
        assert code == 0
        assert not is_blocked(parsed), "Should force-allow after BLOCK_LIMIT"

    def test_per_agent_isolation(self):
        """Block count for one agent does not affect another."""
        msg = COMPLETE_WORKER.replace("### Status: DONE", "### REMOVED")
        self._block_agent_n_times("dl3", 2)
        # Different agent should still be blocked normally
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "dl4",
            "last_assistant_message": msg,
        })
        assert is_blocked(parsed), "Different agent should not be affected"


class TestWorktreeFileResolution:
    """Tests that e2e file checks resolve paths in worktree directories."""

    WORKTREE_BASE = os.path.join(".claude", "worktrees", "agent-test123")

    @pytest.fixture(autouse=True)
    def setup_worktree(self):
        """Create a fake worktree with an e2e test file."""
        e2e_dir = os.path.join(self.WORKTREE_BASE, "tests", "e2e")
        os.makedirs(e2e_dir, exist_ok=True)
        # Write a real e2e test file (must be > 50 chars, no placeholder keywords)
        e2e_file = os.path.join(e2e_dir, "test_spawn.py")
        with open(e2e_file, "w") as f:
            f.write(
                "def test_enemies_spawn(game):\n"
                "    game.wait_seconds(3)\n"
                "    count = game.call('/root/Main/World', 'get_child_count')\n"
                "    assert count > 0, 'Expected enemies to spawn'\n"
            )
        # Also create a .gd file for resource path checks
        src_dir = os.path.join(self.WORKTREE_BASE, "src", "systems")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(src_dir, "s_spawn.gd"), "w") as f:
            f.write('class_name SpawnSystem extends System\n')
        yield
        if os.path.isdir(self.WORKTREE_BASE):
            shutil.rmtree(self.WORKTREE_BASE)

    def test_e2e_file_found_in_worktree(self):
        """e2e file only in worktree should be found and pass check."""
        # The report references tests/e2e/test_spawn.py which only exists in worktree
        msg = (
            "## Report: SpawnSystem\n\n"
            "### Status: DONE\n\n"
            "### Files Changed\n"
            "- `src/systems/s_spawn.gd`: created\n"
            "- `tests/e2e/test_spawn.py`: created\n\n"
            "### Tests\n"
            "#### Unit Tests\n- test/test_spawn.gd: 3 tests, 3 passed\n"
            "#### E2E Tests\n- tests/e2e/test_spawn.py: e2e scenario 1 passed\n\n"
            "### Build\n- Status: PASS\n\n"
            "### Memory Entry\nSpawn system done"
        )
        _, _, parsed = run_hook(HOOK, {
            "hook_event_name": "SubagentStop",
            "agent_id": "wt1",
            "last_assistant_message": msg,
        })
        assert not is_blocked(parsed), (
            "Should pass when e2e file exists in worktree"
        )
