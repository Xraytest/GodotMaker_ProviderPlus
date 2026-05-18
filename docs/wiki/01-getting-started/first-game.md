# Your first game

This walkthrough takes you from an empty folder to a playable Godot game. You will type nine commands in Claude Code — one for each step in the process. In between commands, the AI does the work while you wait; you step in when it asks you a question or when you want to review what was produced.

**Time to expect:** for a small game (a ball that bounces, a simple platformer, a basic puzzle), count on roughly 30 minutes of your own time spread across the session, plus however long the AI takes to run in the background between steps. Bigger games take longer; the commands are the same.

You can stop at any point and come back later. Each command checks what was already done and picks up from where it left off.

## Before you start

Complete [Installation](installation.md) first. You need:

- All five tools installed and passing `python tools/check_env.py`
- `GOOGLE_API_KEY` set in your environment
- The GodotMaker repository cloned locally

## Set up the game project folder

GodotMaker does not run inside the GodotMaker repository itself. You create a new empty folder for your game, then run one command from the GodotMaker folder to install everything the AI needs into that new folder.

From inside the GodotMaker repository:

```bash
python tools/publish.py /path/to/my-game
```

Replace `/path/to/my-game` with a real path, for example `C:\Games\my-bouncing-ball` on Windows or `~/games/my-bouncing-ball` on macOS/Linux. The folder will be created if it does not exist yet.

The command copies the AI skills, hook scripts, configuration, and templates into your new game folder. It will ask for the full path to your Godot executable if it cannot find Godot automatically.

Once it finishes, open Claude Code inside that new folder:

```bash
cd /path/to/my-game
claude
```

Everything from here happens inside that Claude Code session.

---

## Step 1 — `/gm-scaffold`

**What you type:**

```
/gm-scaffold
```

**What to expect:** The AI creates the empty Godot project structure — the folders, the required add-ons (gecs for game logic, gdUnit4 for tests), and the first Git commit. You will not be asked questions at this step; it runs automatically.

**What lands on disk:** `project.godot`, `addons/`, `src/`, `scenes/`, `assets/`, `test/`, `e2e/conftest.py`.

**When you know it's done:** Claude Code prints a summary and returns to the prompt. You will see a new `project.godot` file in the folder.

This step runs once per project. If you run it again on an existing project, it detects the existing scaffold and skips safely.

---

## Step 2 — `/gm-gdd`

**What you type:**

```
/gm-gdd
```

**What to expect:** The AI interviews you about the game you want. It will ask questions like: What is the goal? What does the player do? What should it look like? How many levels? You don't need to have answers ready — answer as much or as little as you know, and the AI fills in reasonable defaults for anything you leave blank.

After the interview, it writes all the planning documents: the Game Design Document, a task list, a folder structure plan, a scene list, and an asset list.

**What lands on disk:** `GDD.md`, `PLAN.md`, `STRUCTURE.md`, `SCENES.md`, `ASSETS.md`, `TOC.md`.

**When you know it's done:** The AI summarises the design and asks if you are happy with it. Read through `GDD.md` — this is your chance to correct anything before the build starts. Type your feedback or say you're happy to continue.

---

## Step 3 — `/gm-asset`

**What you type:**

```
/gm-asset
```

**What to expect:** The AI generates the art for your game — sprites, backgrounds, icons — using Google Gemini. If you want to use your own images instead, you can drop them into the `assets/` folder first and the AI will analyse what you have and fill in only what is missing.

**What lands on disk:** Image files in `assets/`, updated `ASSETS.md`.

**When you know it's done:** The AI reports which assets were generated and which already existed. You can open the `assets/` folder and look at the images; if something looks wrong, give feedback and the AI will regenerate specific items.

---

## Step 4 — `/gm-build`

**What you type:**

```
/gm-build
```

**What to expect:** This is the longest step. The AI implements the game by handing work to specialised sub-agents (think of them as assistants, each responsible for one part of the game). Each task goes through three layers automatically: one sub-agent writes the code, a second one checks that it compiles and the tests pass, and a third checks for common Godot pitfalls. You don't need to supervise this — just wait.

You will see a lot of output as tasks are dispatched and reported back. This is normal.

**What lands on disk:** Game code in `src/`, scene files in `scenes/`, unit tests in `test/`.

**When you know it's done:** The AI prints a build summary. If any tasks failed their checks, they are noted so `/gm-fixgap` can address them later.

---

## Step 5 — `/gm-verify`

**What you type:**

```
/gm-verify
```

**What to expect:** The AI runs a mechanical check — does the project compile without errors? Do the unit tests pass? Are any required files missing? This is a fast, automated step with no questions.

**What lands on disk:** A `verify` event appended to `.godotmaker/stage.jsonl` once every check passes. The detailed report is printed to the chat — nothing else is written to disk.

**When you know it's done:** The AI prints a pass/fail summary. If anything fails here, it means something in the build step needs fixing — the next two commands handle that.

---

## Step 6 — `/gm-evaluate`

**What you type:**

```
/gm-evaluate
```

**What to expect:** The AI runs the actual game in the background (without opening a window on your screen), takes screenshots, and scores the result against what the Game Design Document described. This gives an independent view of whether the game looks and behaves correctly — separate from the build step that created it.

**What lands on disk:** `.godotmaker/evaluation.json`, screenshots in `e2e/screenshots/`.

**When you know it's done:** The AI prints an evaluation score and a list of anything that didn't match the design. You can open the screenshots to see what the AI saw.

---

## Step 7 — `/gm-fixgap`

**What you type:**

```
/gm-fixgap
```

**What to expect:** The AI reads the evaluation results, figures out what needs to change, and dispatches sub-agents to fix each issue — same three-layer process as the build step. This command is safe to skip if the evaluation reported no problems.

**What lands on disk:** Updated game code, a `GAP.md` file listing what was fixed (archived to `.godotmaker/gaps/` when done).

**When you know it's done:** The AI summarises what was fixed. If significant changes were made, you can re-run `/gm-verify` and `/gm-evaluate` to confirm the fixes landed correctly.

---

## Step 8 — `/gm-accept`

**What you type:**

```
/gm-accept
```

**What to expect:** The AI presents the current state of the game and asks you to make a decision:

- **Accept** — you're happy with this tag; move on to finalising.
- **Reject (loop back)** — something is still wrong; the AI will return to `/gm-fixgap` and try again.
- **Stop** — you want to leave the session here and come back later.

**What lands on disk:** An acceptance record in `.godotmaker/stage.jsonl`.

**When you know it's done:** You've made your choice and told the AI.

---

## Step 9 — `/gm-finalize`

**What you type:**

```
/gm-finalize
```

**What to expect:** The AI tidies everything up — checks the working docs against the final code, archives them into `docs/tags/<Tag>/`, writes a per-tag changelog, runs `git tag <Tag>` locally, and resets per-tag runtime state so the next `/gm-gdd` starts clean. This is a short, automatic step.

**What lands on disk:** `docs/tags/<Tag>/` archive, `.godotmaker/final_report.json`, a local git tag.

**When you know it's done:** The AI confirms the tag is sealed and the project is ready to open in Godot.

---

## You now have a playable game

Open the project in the Godot editor:

```bash
godot --editor --path /path/to/my-game
```

Or run it directly:

```bash
godot --path /path/to/my-game
```

To add a new feature later, start a fresh Claude Code session in the same folder and begin again at `/gm-gdd`. The AI reads `MEMORY.md` to understand what already exists before planning the next change. `/gm-scaffold` is a one-time step and does not need to be repeated.

For a tour of what everything in the project folder means, see [Project layout](project-layout.md).
