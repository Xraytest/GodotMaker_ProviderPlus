"""Tests for session_start.py hook."""
import json
import os
import pytest
import tempfile
from .helpers import run_hook, cleanup_metrics

HOOK = "session_start.py"


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


class TestSessionStart:
    def test_clears_current_metrics(self, project_dir):
        # Create pre-existing current metrics
        os.makedirs(".godotmaker", exist_ok=True)
        with open(".godotmaker/metrics_current.jsonl", "w") as f:
            f.write('{"event": "old_event"}\n')

        _, code, _ = run_hook(HOOK, {})
        assert code == 0

        # Current should be empty
        with open(".godotmaker/metrics_current.jsonl") as f:
            assert f.read().strip() == ""

    def test_resets_state(self, project_dir):
        # Create pre-existing state with block count
        os.makedirs(".godotmaker", exist_ok=True)
        with open(".godotmaker/state.json", "w") as f:
            json.dump({"stop_block_count": 5}, f)

        _, code, _ = run_hook(HOOK, {})
        assert code == 0

        with open(".godotmaker/state.json") as f:
            state = json.load(f)
        assert state["stop_block_count"] == 0

    def test_never_blocks(self, project_dir):
        _, code, parsed = run_hook(HOOK, {})
        assert code == 0
