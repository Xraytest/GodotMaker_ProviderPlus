# Getting Started

First-time setup guide for using GodotMaker to generate Godot games.

## Quick Start

```bash
# 1. Check environment
python tools/check_env.py

# 2. Install Python dependencies
pip install -r tools/requirements.txt

# 3. Publish to your game project
bash shell/publish.sh /path/to/my-game-project             # Linux/macOS/Git Bash
# .\shell\publish.ps1 /path/to/my-game-project             # Windows PowerShell

# 4. Start making games
cd /path/to/my-game-project
claude
```

## Prerequisites

### Required Tools

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| **Godot** | 4.4+ | Game engine | https://godotengine.org/download |
| **Git** | 2.30+ | Version control, parallel workers | https://git-scm.com/downloads |
| **Node.js** | 18+ | godot-mcp runtime (npx) | https://nodejs.org |
| **Python** | 3.9+ | Asset pipeline, visual-qa, E2E testing | https://python.org |
| **Claude Code** | Latest | AI agent runtime | `npm install -g @anthropic-ai/claude-code` |

### API Keys

| Key | Service | How to Get | Required? |
|-----|---------|-----------|-----------|
| **GOOGLE_API_KEY** | Google Gemini | https://aistudio.google.com/apikey → Create API key | **Yes** (image gen + VQA) |
| XAI_API_KEY | xAI Grok | https://console.x.ai → API Keys | No (cheaper image gen, optional) |
| TRIPO3D_API_KEY | Tripo3D | https://www.tripo3d.ai → Dashboard → API | No (3D model gen, only for 3D games) |

**For 2D-only projects**, you only need `GOOGLE_API_KEY`. Grok and Tripo3D are optional.

## Step-by-Step Setup

### Step 1: Install Tools

Install each prerequisite tool. After installation, verify each one:

```bash
git --version          # expect >= 2.30
python --version       # expect >= 3.9
node --version         # expect >= 18
godot --version        # expect >= 4.4 (or provide full path later)
claude --version       # Claude Code CLI
```

### Step 2: Configure Git

Git is required for parallel worker isolation (worktrees).

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### Step 3: Set API Keys

**Windows (PowerShell, permanent):**
```powershell
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key-here", "User")
```

**Windows (CMD, current session):**
```cmd
set GOOGLE_API_KEY=your-key-here
```

**Linux/macOS (add to ~/.bashrc or ~/.zshrc):**
```bash
export GOOGLE_API_KEY="your-key-here"
```

Restart your terminal after setting environment variables.

### Step 4: Install Python Dependencies

```bash
cd /path/to/GodotMaker
pip install -r tools/requirements.txt
```

### Step 5: Verify Environment

Run the environment checker to confirm everything is ready:

```bash
python tools/check_env.py
```

All `[FAIL]` items must be resolved before proceeding. `[WARN]` items are optional.

### Step 6: Publish to Game Project

Create a directory for your game and publish GodotMaker skills into it:

```bash
# Create game directory
mkdir my-game-project

# Linux/macOS/Git Bash
bash shell/publish.sh my-game-project

# Windows PowerShell
# .\shell\publish.ps1 my-game-project
```

The publish script will:
- Copy all skills to `.claude/skills/` (flattened structure)
- Copy tools, hooks, config, and templates
- Prompt for your Godot executable path and create `.claude/godotmaker.yaml`
- Create `.godotmaker/config.yaml` with default project settings
- Register godot-mcp as an MCP server (requires Node.js/npx)
- Create `.gitignore` to exclude `.claude/` and selectively ignore `.godotmaker/` runtime state files (hooks, config, and version are tracked for worktree support)
- Initialize git repo with initial commit (see [User Notice](user-notice.md) for details)

### Step 7: Verify Publish

```bash
cd my-game-project

# Check godotmaker.yaml was created
cat .claude/godotmaker.yaml

# Check project config was created
cat .godotmaker/config.yaml

# Check skills were published
ls .claude/skills/

# Check godot-mcp registration (should show "godot" server)
claude mcp list

# Verify Gemini API key works
python -c "from google import genai; c = genai.Client(); print('Gemini OK')"
```

### Step 8: Generate a Game

```bash
cd my-game-project
claude
```

In Claude Code, explicitly invoke the orchestrator skill to start:

```
/orchestrator Make a 2D game where a ball bounces around the screen.
The ball starts in the center and moves in a random direction.
It bounces off all four walls. No player input needed.
```

**Important:** Always use `/orchestrator` to start game creation or modification. This loads the full pipeline with stage gates, worker dispatch, and verification hooks. Without it, Claude may attempt to write game code directly, which bypasses all quality controls.

## Project Configuration

After publishing, `.godotmaker/config.yaml` contains project-level settings:

```yaml
# VQA model for visual quality checks (any Gemini model name)
vqa_model: gemini-3-flash
```

| Key | Default | Description |
|-----|---------|-------------|
| `vqa_model` | `gemini-3-flash` | Gemini model used for visual QA. Change to any supported Gemini model name. |

To modify, edit `.godotmaker/config.yaml` directly.

## Republishing

To update skills after a GodotMaker upgrade:

```bash
bash shell/publish.sh --force /path/to/my-game-project
# Windows: .\shell\publish.ps1 -Force /path/to/my-game-project
```

`--force` cleans `.claude/skills/` before republishing. Your `godotmaker.yaml` and `.godotmaker/config.yaml` are preserved.

## Troubleshooting

### "godot: command not found"

Your Godot executable is not on PATH. Either:
- Add it to PATH, or
- The path in `.claude/godotmaker.yaml` must be the full absolute path

### "GOOGLE_API_KEY not set" or Gemini errors

- Verify the key: `echo $GOOGLE_API_KEY` (Linux/Mac) or `echo %GOOGLE_API_KEY%` (Windows CMD)
- Test: `python -c "from google import genai; c = genai.Client(); print('OK')"`
- If you just set it, restart your terminal

### "npx: command not found"

Node.js is not installed. Install from https://nodejs.org (LTS version).

### Publish script errors

- Ensure Python 3.9+ is installed: `python --version`
- On Windows, use PowerShell (`.\shell\publish.ps1`) or Git Bash (`bash shell/publish.sh`)
- As fallback, run the Python script directly: `python tools/publish.py <target>`

### Skills not loading in Claude Code

- Check skills are at `.claude/skills/<name>/SKILL.md` (not nested under core/ or reviewer/)
- Run `bash shell/publish.sh --force <target>` to re-publish
- Restart Claude Code session

### Environment checker fails

Run `python tools/check_env.py` and fix each `[FAIL]` item. The output includes install instructions for each missing component.

## What Happens During Game Generation

The orchestrator follows an 8-stage pipeline:

1. **Requirements** — Clarifies what game to build (game-planner skill)
2. **Design** — Creates PLAN.md (task breakdown) and STRUCTURE.md (architecture)
3. **Scaffold** — Creates project structure, addons, base components (project-scaffold skill)
4. **Assets** — Generates reference image and game assets via Gemini API
5. **Implementation** — Dispatches Sonnet workers for each system/scene/UI
6. **Integration** — Cross-system testing and conflict resolution
7. **Verification** — Builds, tests, lints, visual QA against reference
8. **Final** — End-to-end gameplay verification and polish

You can interrupt at any point to give feedback or redirect.
