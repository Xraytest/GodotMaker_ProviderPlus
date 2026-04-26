# Installation

This guide walks through setting up GodotMaker on your machine.

## Prerequisites

### Required Tools

| Tool | Minimum Version | Purpose | Install Link |
|------|----------------|---------|--------------|
| Godot | 4.4+ | Game engine (headless builds, runtime) | https://godotengine.org/download |
| Git | 2.30+ | Version control, worktree-based parallel workers | https://git-scm.com/downloads |
| Node.js | 18+ | godot-mcp runtime (npx) | https://nodejs.org |
| Python | 3.9+ | Asset pipeline, visual QA, E2E testing, environment checker | https://python.org |
| Claude Code | Latest | AI agent runtime (orchestrator + workers) | `npm install -g @anthropic-ai/claude-code` |

Verify each tool after installation:

```bash
git --version          # >= 2.30
python --version       # >= 3.9
node --version         # >= 18
godot --version        # >= 4.4
claude --version       # Claude Code CLI
```

### API Keys

| Key | Service | Required? | How to Get |
|-----|---------|-----------|------------|
| `GOOGLE_API_KEY` | Google Gemini (image generation + VQA) | **Yes** | https://aistudio.google.com/apikey |
| `XAI_API_KEY` | xAI Grok (cheaper image generation) | No | https://console.x.ai |
| `TRIPO3D_API_KEY` | Tripo3D (3D model generation) | No (3D games only) | https://www.tripo3d.ai |

For 2D-only projects, only `GOOGLE_API_KEY` is required.

**Setting API keys:**

Windows (PowerShell, permanent):
```powershell
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key-here", "User")
```

Linux/macOS (add to `~/.bashrc` or `~/.zshrc`):
```bash
export GOOGLE_API_KEY="your-key-here"
```

Restart your terminal after setting environment variables.

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/user/GodotMaker.git
cd GodotMaker
```

### 2. Configure Git

Git is required for parallel worker isolation via worktrees.

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### 3. Install Python Dependencies

```bash
pip install -r tools/requirements.txt
```

### 4. Verify Environment

Run the environment checker to confirm all prerequisites are met:

```bash
python tools/check_env.py
```

The checker reports three levels:

| Level | Meaning |
|-------|---------|
| `[PASS]` | Requirement met |
| `[WARN]` | Optional dependency missing -- some features may be unavailable |
| `[FAIL]` | Required dependency missing -- must be resolved before proceeding |

All `[FAIL]` items must be resolved. `[WARN]` items are optional.

## Publishing to a Game Project

GodotMaker does not run inside a game project directly. Instead, you **publish** skills, hooks, tools, and configuration into a target game directory.

```bash
# Linux / macOS / Git Bash
bash shell/publish.sh /path/to/my-game-project

# Windows PowerShell
.\shell\publish.ps1 /path/to/my-game-project
```

The publish script copies skills, hooks, tools, config, and templates into the target project, registers godot-mcp, and initializes a git repository for worktree-based parallel workers. For the full publish pipeline details, see [Publish](../05-tools/publish.md).

### Republishing After Upgrades

When GodotMaker is updated, republish with `--force` to update skills while preserving your configuration:

```bash
bash shell/publish.sh --force /path/to/my-game-project
# Windows: .\shell\publish.ps1 -Force /path/to/my-game-project
```

### Verifying the Publish

```bash
cd /path/to/my-game-project

cat .claude/godotmaker.yaml        # Godot path and settings
cat .godotmaker/config.yaml        # Project-level config
ls .claude/skills/                 # Published skills
claude mcp list                    # Should show "godot" server
```

## Troubleshooting

**"godot: command not found"** -- Godot is not on your PATH. Either add it to PATH, or ensure `.claude/godotmaker.yaml` contains the full absolute path to the Godot executable.

**"GOOGLE_API_KEY not set"** -- Verify the key is set (`echo $GOOGLE_API_KEY` on Linux/Mac, `echo %GOOGLE_API_KEY%` on Windows CMD). If you just set it, restart your terminal.

**"npx: command not found"** -- Node.js is not installed. Install from https://nodejs.org (LTS version).

**Publish script errors** -- Ensure Python 3.9+ is installed. On Windows, use PowerShell or Git Bash. As a fallback, run the Python script directly: `python tools/publish.py <target>`.

**Skills not loading in Claude Code** -- Skills must be at `.claude/skills/<name>/SKILL.md` (not nested under core/ or reviewer/). Republish with `--force` and restart Claude Code.
