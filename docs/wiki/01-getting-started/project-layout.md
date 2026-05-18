# Project layout

After you run all nine commands, your game folder contains a lot of files. Most of them are maintained by the AI and you don't need to touch them. This page explains what each folder and file is for so you know where to look when something interests you — and what to leave alone.

```
my-game/
├── project.godot
├── src/
├── scenes/
├── addons/
├── assets/
├── GDD.md
├── PLAN.md
├── STRUCTURE.md
├── SCENES.md
├── ASSETS.md
├── TOC.md
├── MEMORY.md
├── test/
├── e2e/
├── CLAUDE.md
├── .claude/
├── .godotmaker/
├── .git/
└── .gitignore
```

---

## Where the game lives

These are the folders that contain the actual game Godot will run.

**`project.godot`** — The Godot project file. Every Godot project has one; it records the main scene, display settings, and which add-ons are active. You can open this in Godot or double-click it in your file manager to launch the editor. The AI creates it during `/gm-scaffold` and updates it as needed. You do not normally edit it by hand.

**`src/`** — All the game code. GodotMaker uses an approach called ECS (Entity-Component-System, explained below) where code is split into two kinds of files: components (small files that hold data, like a `Health` value or a `Position`) and systems (small files that contain the logic that acts on that data, like "move everything that has a Position"). The AI writes and updates everything here. You can read these files freely; editing them yourself is fine but the AI may overwrite your changes in a future session if a task touches the same file.

**`scenes/`** — Godot scene files (`.tscn`). A scene (think of it as a "level" or a "screen") describes what appears on screen and how it is laid out. The AI generates scenes according to the plan in `SCENES.md`. You can open and inspect them in the Godot editor.

**`addons/`** — Three Godot plugins that GodotMaker requires. `gecs` is the ECS framework the game code is built on. `gdUnit4` is the unit-testing framework (runs individual code checks). `godot_e2e` is the end-to-end testing framework (runs the whole game and takes screenshots). These are installed by `/gm-scaffold` and should not be edited.

**`assets/`** — Images, audio, and fonts for the game. The AI generates art here during `/gm-asset`. If you want to replace a generated image with one of your own, drop your file into the relevant subfolder and re-run `/gm-asset` — the AI will detect the new file and update the asset list.

---

## Where the design documents live

These Markdown files are the "source of truth" the AI reads before making decisions. You can read all of them. Some you may want to edit; each entry notes whether that's a good idea.

**`GDD.md`** (Game Design Document) — Describes what the game is: the goal, the mechanics, the visual style, the win and lose conditions. Written by `/gm-gdd`. If you want to change the game's direction mid-project, editing this file and then re-running `/gm-gdd` is the right way to do it.

**`PLAN.md`** — The task list. The AI tracks every implementation task here — what has been done, what is pending, what failed. You can read it to see progress. The AI updates it automatically; editing it yourself is not recommended.

**`STRUCTURE.md`** — The technical architecture: which components and systems exist, what data each component holds, what each system does. Written by `/gm-gdd`, updated by the build step. Reading it gives you the clearest picture of how the game code is organised.

**`SCENES.md`** — A description of every scene: what it contains and how the game objects in it map to ECS entities. Written by `/gm-gdd`. The AI uses this as a blueprint when generating `.tscn` files.

**`ASSETS.md`** — A list of every asset the game needs: the logical name, the file path, and the generation settings used. Written and updated by `/gm-asset`. If you add your own art files, the AI updates this list to include them.

**`TOC.md`** — Table of contents for all the documents above. Generated automatically. Useful as a quick index if you're not sure which document to look at.

**`MEMORY.md`** — A log of discoveries, past mistakes, and important decisions that the AI wants to remember across sessions. Written and updated automatically. Reading it is useful if you want to understand why the AI made a particular choice in an earlier session.

---

## Where the tests live

GodotMaker generates tests alongside game code so problems can be caught early.

**`test/`** — Unit tests. Each test file checks one small piece of the game code in isolation (for example, "does the movement system move an entity the right distance in one frame?"). Run by `/gm-verify` automatically. You can also run them manually from the command line with Godot's headless mode.

**`e2e/`** — End-to-end tests. These run the whole game and check whether it behaves correctly at the "player experience" level — does the ball actually bounce, does the score increment, does the game end when it should? Written by `/gm-evaluate`. The `e2e/screenshots/` subfolder holds captured frames from those test runs.

---

## Framework bookkeeping

These two hidden folders are managed entirely by GodotMaker. You should not edit files inside them unless a specific instruction tells you to.

**`.claude/`** — Contains the AI skills (the instructions each `/gm-*` command follows), the agent definitions for the sub-agents, the hook registrations, and the host-specific configuration like the path to your Godot executable (`godotmaker.yaml`). Everything here is deployed by `publish.py` and refreshed when you republish.

**`.godotmaker/`** — Runtime state for the current project. Key files:

- `version` — which version of GodotMaker was published here. Used to detect when an upgrade is available.
- `current_role` — a one-word file that records which command is currently running (`build`, `evaluate`, etc.). Hook scripts read this to enforce what the AI is and isn't allowed to write at any given moment.
- `stage.jsonl` — an append-only log of every completed command, with timestamps. This is how the AI knows where you left off if you resume a session.
- `config.yaml` — per-project preferences such as which AI model to use for image generation. You can edit this file if you want to change those preferences.
- `hooks/` — the Python hook scripts that enforce the rules (which files can be written, whether all required outputs exist, etc.). Managed automatically.
- `evaluation.json` and `final_report.json` — outputs from `/gm-evaluate` and `/gm-finalize`. Useful for reading the AI's assessment of the current build.
- `gaps/<n>/` — archived `GAP.md` files from each `/gm-fixgap` run, kept for reference.

---

## Version control

**`.git/`** — The Git repository. Created by `/gm-scaffold`. The AI commits changes after each major step so you always have a history to fall back on. You can use standard Git commands (`git log`, `git diff`, `git checkout`) to explore or recover earlier states.

**`.gitignore`** — Tells Git which files not to track (large binary outputs, temporary state, local config). Managed automatically.

---

## If you only edit one file

**`CLAUDE.md`** — This file contains the per-project instructions that Claude Code reads at the start of every session. It tells the AI the rules for this specific project. If you want the AI to always follow a particular convention (use a specific colour palette, never add sound effects, keep the code comments in a certain language), add it here and it will apply to every future session. This is the one file that is genuinely yours to customise.

Second to that: **`GDD.md`** is the most useful document to read and occasionally update. It is the single place that describes what the game is supposed to be. If the game drifts from your vision, updating `GDD.md` and re-running from `/gm-gdd` is the right correction.
