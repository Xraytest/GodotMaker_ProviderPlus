# Your First Game

This walkthrough generates a complete Godot game from a natural language description using GodotMaker's 8-stage pipeline.

## Before You Start

Make sure you have completed the [installation](installation.md) steps:
- All prerequisites installed and verified
- `GOOGLE_API_KEY` set in your environment
- GodotMaker repository cloned and Python dependencies installed

## Step 1: Create a Game Project Directory

```bash
mkdir my-bouncing-ball
```

## Step 2: Publish GodotMaker into It

```bash
# From the GodotMaker repository root
bash shell/publish.sh /path/to/my-bouncing-ball

# Windows PowerShell
# .\shell\publish.ps1 /path/to/my-bouncing-ball
```

The script will ask for your Godot executable path during setup. After publishing, the directory contains `.claude/` (skills, hooks, config) and `.godotmaker/` (project state).

## Step 3: Start Claude Code

```bash
cd /path/to/my-bouncing-ball
claude
```

## Step 4: Invoke the Orchestrator

In the Claude Code session, use `/orchestrator` followed by your game description:

```
/orchestrator Make a 2D game where a ball bounces around the screen.
The ball starts in the center and moves in a random direction.
It bounces off all four walls. No player input needed.
```

**Important:** Always use `/orchestrator` to start game creation. Without it, Claude may write game code directly, bypassing the pipeline's quality controls (stage gates, worker dispatch, verification hooks).

## What Happens: The 8 Stages

Once invoked, the orchestrator runs through a mandatory 8-stage pipeline. Here is what you see at each stage:

### Stage 1: Requirements and Game Design

The orchestrator analyzes your description and produces a Game Design Document (GDD). It may ask clarifying questions (screen size, art style, specific mechanics). You can provide feedback or approve to continue.

**Output:** `GDD.md`

### Stage 2: Architecture

The orchestrator creates the technical plan: which ECS components and systems are needed, how they connect, what the scene structure looks like.

**Output:** `PLAN.md` (task breakdown), `STRUCTURE.md` (components, systems, scenes)

### Stage 3: Scaffold

A worker creates the project skeleton: `project.godot`, directory structure, base component definitions, gecs/gdUnit4/godot-e2e addon stubs.

**Output:** `project.godot`, `components/`, `systems/`, `test/`, `e2e/`, addon directories

### Stage 4: Assets

The orchestrator generates a reference image showing what the game should look like, then generates game assets (sprites, audio placeholders) via the Gemini API.

**Output:** `references/reference.png`, `assets/sprites/`, `ASSETS.md`

### Stage 5: Risk Implementation

High-risk systems (those most likely to fail or block other work) are implemented first. Each system is built by a worker and verified by a separate verifier.

**Output:** Implemented systems with unit tests, e2e test stubs

### Stage 6: Main Implementation

Remaining systems, scenes, and UI are implemented through worker dispatch. Each worker receives a structured brief, implements code + tests, and reports back.

**Output:** All remaining `systems/`, `components/`, scene files, `test/` files

### Stage 7: Integration Verification

Cross-system testing: headless build, full test suite, GDScript linting, visual QA (screenshots compared against the reference image).

**Output:** `screenshots/`, verification reports, bug fixes if needed

### Stage 8: Final Acceptance

End-to-end gameplay verification. The game is run, screenshots are captured, and visual QA confirms the game matches expectations. The orchestrator performs final polish.

**Output:** Final `screenshots/`, `MEMORY.md` updated, `TOC.md` updated

## Step 5: Run the Generated Game

After the pipeline completes, open the project in Godot:

```bash
# Open in Godot editor
godot --editor --path /path/to/my-bouncing-ball

# Or run directly
godot --path /path/to/my-bouncing-ball
```

## What the Output Looks Like

After generation, your project directory contains:

```
my-bouncing-ball/
  project.godot              # Godot project file
  CLAUDE.md                  # Project-specific AI instructions
  GDD.md                     # Game design document
  PLAN.md                    # Task breakdown with status tracking
  STRUCTURE.md               # ECS architecture (components, systems, scenes)
  ASSETS.md                  # Asset manifest
  SCENES.md                  # Scene definitions
  MEMORY.md                  # Persistent context for future sessions
  TOC.md                     # Table of contents
  components/                # ECS component definitions (.gd)
  systems/                   # ECS system implementations (.gd)
  test/                      # Unit tests (gdUnit4)
  e2e/                       # End-to-end tests (godot-e2e)
  assets/                    # Game assets (sprites, audio, fonts)
  screenshots/               # Captured gameplay screenshots
  references/                # Reference images for visual QA
  addons/                    # gecs, gdunit4, godot_e2e
  .claude/                   # Skills, config (gitignored)
  .godotmaker/               # Hooks, pipeline state, metrics (partially tracked)
```

## Iterating on Your Game

To add features or make changes to an existing game, start a new Claude Code session in the same directory and invoke `/orchestrator` again:

```
/orchestrator Add a score counter in the top-left corner that increments
each time the ball bounces off a wall.
```

The orchestrator detects the existing project, reads its state, and runs only the stages needed for the change (typically Stage 6 through Stage 8).

## Tips

- **Be specific in your description.** "A ball that bounces" is fine for a demo, but for real games, describe mechanics, art style, screen layout, and win/lose conditions.
- **You can interrupt at any stage.** If the GDD does not match your vision, give feedback before the orchestrator proceeds.
- **Check screenshots.** The `screenshots/` directory shows what the game looks like at verification time -- useful for catching visual issues early.
- **Read PLAN.md for status.** The task table in PLAN.md tracks what has been implemented, what is pending, and what failed.
