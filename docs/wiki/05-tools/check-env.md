# Environment Checker

`check_env.py` verifies that all prerequisites for using GodotMaker are installed and correctly configured on the current machine.

## Usage

```bash
python tools/check_env.py
```

Run this after publishing GodotMaker to a project, or any time you suspect environment issues.

## What It Checks

The checker runs six categories of checks in order:

### Git

| Check | Requirement | Fix |
|---|---|---|
| Git installed | >= 2.30 | Install from https://git-scm.com/downloads |
| `user.name` configured | Non-empty | `git config --global user.name "..."` |
| `user.email` configured | Non-empty | `git config --global user.email "..."` |

### Python

| Check | Requirement | Fix |
|---|---|---|
| Python version | >= 3.9 | Install from https://python.org |
| `google-genai` package | Importable | `pip install google-genai` |
| `requests` package | Importable | `pip install requests` |
| `pillow` package | Importable | `pip install pillow` |
| `numpy` package | Importable | `pip install numpy` |

### Node.js

| Check | Requirement | Fix |
|---|---|---|
| Node.js version | >= 18 | Install from https://nodejs.org |
| `npx` available | On PATH | Should come with Node.js |

### Godot

| Check | Requirement | Fix |
|---|---|---|
| Godot version | >= 4.4 | Install from https://godotengine.org; ensure `godot` or `godot4` is on PATH |

The checker tries both `godot` and `godot4` commands. If neither is found, it issues a warning (not a failure) since the full path can be provided via `godotmaker.yaml` instead.

### Claude Code

| Check | Requirement | Fix |
|---|---|---|
| `claude` CLI | On PATH | `npm install -g @anthropic-ai/claude-code` |

### API Keys

| Key | Status | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | **Required** | Image generation + VQA (visual quality assurance) |
| `XAI_API_KEY` | Optional | Cheaper image generation via xAI Grok |
| `TRIPO3D_API_KEY` | Optional | 3D model generation via Tripo3D |

For the Google API key, the checker also verifies that `google-genai` can be imported successfully.

## Output Format

Each check prints one of three status markers:

```
[PASS] Git 2.43.0 (>= 2.30)
[FAIL] Package 'google-genai' missing. Run: pip install google-genai
[WARN] XAI_API_KEY not set (optional, cheaper image generation)
```

At the end, a summary is printed:

```
========================================
Total: 14 checks
  PASS: 12
  FAIL: 1
  WARN: 1

Failed checks:
  - Package 'google-genai' missing. Run: pip install google-genai

Fix the above issues before using GodotMaker.
```

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | All required checks passed (warnings are acceptable) |
| 1 | One or more required checks failed |
