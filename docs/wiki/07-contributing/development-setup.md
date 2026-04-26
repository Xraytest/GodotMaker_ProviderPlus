# Development Setup

This guide walks you through setting up a local development environment for GodotMaker.

## Prerequisites

- Python 3.11+
- Git
- Godot 4.4+ (for end-to-end testing)
- Node.js / npm (for godot-mcp, optional)

## Clone the Repository

```bash
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker
```

## Install Python Dependencies

GodotMaker has two sets of dependencies:

**Core tools** (required for hooks, publish, and testing):

```bash
pip install pytest
```

**Full toolchain** (includes AI asset generation, background removal, etc.):

```bash
pip install -r tools/requirements.txt
```

The full requirements include `xai-sdk`, `google-genai`, `pillow`, `rembg`, `onnxruntime-gpu`, and others. You only need these if you plan to work on the asset generation or VQA tools.

## Run Tests

The test suite uses pytest. From the repository root:

```bash
python -m pytest tests/ -x -q
```

This runs all 193 tests across hooks and tools. The `-x` flag stops on first failure; `-q` produces compact output.

To run a specific test file:

```bash
python -m pytest tests/hooks/test_check_worker_report.py -x -q
python -m pytest tests/tools/test_publish.py -x -q
```

The `pyproject.toml` configures `pythonpath = ["hooks"]` so that hook imports resolve correctly.

## Project Structure Overview

| Directory | Purpose |
|---|---|
| `hooks/` | 8 Python hook scripts enforcing pipeline rules |
| `hooks/metrics/` | Metrics subsystem (collector, schema, state, reporter, highlights) |
| `skills/core/` | 15 core skill definitions for the orchestrator and workers |
| `skills/reviewer/` | 8 domain-specific reviewer skills |
| `tools/` | 10 Python CLI tools (publish, check_env, asset_gen, etc.) |
| `config/` | 4 config files (settings.json, stage_schemas.json, etc.) |
| `templates/` | 9 markdown templates for game design documents |
| `shell/` | 5 shell scripts for publishing and reporting |
| `tests/` | Test suite (hooks + tools) |

## Testing Changes Locally

After making changes to hooks, tools, or skills, you should verify them in two ways:

### 1. Run the test suite

```bash
python -m pytest tests/ -x -q
```

### 2. Publish to a test project

Create a throwaway Godot project directory and publish into it:

```bash
mkdir /tmp/test-project
python tools/publish.py /tmp/test-project
```

This copies skills, tools, config, and templates into the target project's `.claude/` directory, and hooks into `.godotmaker/hooks/`. Inspect the output to verify everything deployed correctly.

To re-publish with a clean slate:

```bash
python tools/publish.py --force /tmp/test-project
```

### 3. Run hooks manually

Hook scripts read JSON from stdin and write JSON to stdout. You can test them directly:

```bash
echo '{"hook_event_name": "SessionStart"}' | python .godotmaker/hooks/session_start.py
```

For hooks that check file permissions or stage prerequisites, you need to provide the appropriate event data structure. See `tests/hooks/helpers.py` for the `run_hook` function that automates this pattern.

### 4. Verify environment setup

After publishing to a test project, run the environment checker:

```bash
cd /tmp/test-project
python tools/check_env.py
```

This validates that Godot, required addons, and MCP are configured correctly.
