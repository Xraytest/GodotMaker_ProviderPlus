# Installation

GodotMaker turns a plain-English description into a playable Godot 4 game. To do that it needs five pieces of software working together: Godot (the game engine that runs your game), Git (version control that lets the AI keep a safe history of every change), Node.js (a runtime that GodotMaker uses to talk to Godot from the command line), Python (runs the asset-generation pipeline and the environment checker), and Claude Code (the AI assistant that drives the whole process). This guide gets all five installed, adds the API key needed for image generation, and confirms everything is working before you make your first game.

## Prerequisites

| Tool | Minimum version | Why GodotMaker needs it | Where to get it |
|------|-----------------|-------------------------|-----------------|
| Godot | 4.5+ | Compiles and runs the generated game | https://godotengine.org/download |
| Git | 2.30+ | Tracks every file change; lets the AI work in parallel without conflicts | https://git-scm.com/downloads |
| Node.js | 18+ | Provides `npx`, which GodotMaker uses to connect Claude Code to Godot | https://nodejs.org (choose the LTS version) |
| Python | 3.9+ | Generates art, runs the environment check, and drives end-to-end tests | https://python.org/downloads |
| Claude Code | Latest | The AI assistant you type commands into | `npm install -g @anthropic-ai/claude-code` |

Install each one using the links above, then continue.

## API keys

GodotMaker uses Google Gemini to create the art in your game (sprites, backgrounds, icons). This requires a free API key. Two other keys are optional and only add extra image-generation providers.

| Key | Required? | What it unlocks |
|-----|-----------|-----------------|
| `GOOGLE_API_KEY` | **Yes** | Image generation and visual quality checks — required for every project. Get one free at https://aistudio.google.com/apikey |
| `XAI_API_KEY` | Optional | Uses xAI Grok as a second image-generation option (sometimes cheaper). Get one at https://console.x.ai |
| `TRIPO3D_API_KEY` | Optional | Generates 3D models, only useful for 3D games. Get one at https://www.tripo3d.ai |

### Setting the keys on Windows (PowerShell)

This stores the key permanently for your Windows user account. You only need to do this once.

```powershell
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key-here", "User")
```

To add the optional keys, run the same command with the other key names.

Close and reopen your terminal after running these commands so the new values take effect.

### Setting the keys on macOS or Linux

Add the following lines to your shell profile file (`~/.bashrc` if you use Bash, `~/.zshrc` if you use Zsh), then restart your terminal.

```bash
export GOOGLE_API_KEY="your-key-here"
# Optional:
# export XAI_API_KEY="your-key-here"
# export TRIPO3D_API_KEY="your-key-here"
```

## Step-by-step install

### 1. Clone the GodotMaker repository

This downloads GodotMaker's tools and skill definitions to your machine. You only need to do this once. The folder you clone into is the GodotMaker framework — it is not your game project.

```bash
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker
```

### 2. Set your Git identity

Git records who made each change. If you have never set these, run:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Install Python dependencies

```bash
pip install -r tools/requirements.txt
```

This installs the Python packages that handle image generation, visual quality checks, and end-to-end tests.

### 4. Run the environment check

```bash
python tools/check_env.py
```

The checker verifies every prerequisite and prints a result for each:

- `[PASS]` — all good
- `[WARN]` — an optional feature is missing; your game will still generate but some capabilities are unavailable
- `[FAIL]` — a required item is missing; fix it before continuing

Fix every `[FAIL]` line before moving on. `[WARN]` lines are safe to skip unless you want the optional feature they describe.

## What's next

Once the environment check reports no `[FAIL]` items, you are ready to make your first game. Head to [Your first game](first-game.md).
