# The 9 roles

Each role is a slash command you type in Claude Code. Run them in order — you will be told if you skipped a prerequisite.

The commands form two kinds of sequence. `/gm-scaffold` runs once, at the very start of a project. `/gm-gdd` through `/gm-finalize` form one "milestone" — a round of design, build, and ship. After `/gm-finalize` closes a milestone, you can start the next one with another `/gm-gdd`.

---

## `/gm-scaffold`

**What it does:** Creates an empty Godot project with the right folder structure, installs the required addons (`gecs` for ECS support, `gdUnit4` for testing), and makes the first git commit.

**When to run it:** Once, before anything else. The project directory must exist but be empty (or have only a `.git` folder).

**What happens behind the scenes:**
- Writes `project.godot`, `addons/`, `src/`, `scenes/`, `assets/`, `e2e/`, `tests/`
- Installs and configures `gecs` and `gdUnit4`
- Creates `e2e/conftest.py` (the test harness entry point)

**What you get:** A clean, runnable Godot project with no game logic yet.

**Things to know:** This command runs only once per project. Running it a second time in the same project stops early with an explanation.

---

## `/gm-gdd`

**What it does:** Interviews you to understand what game you want, then writes the planning documents that everything else reads from.

**When to run it:** After `/gm-scaffold` (first milestone), or after `/gm-finalize` (each subsequent milestone).

**What happens behind the scenes:**
- Asks you questions about genre, mechanics, art style, scope, and platform
- Writes `GDD.md` (the design contract), `PLAN.md` (task list), `STRUCTURE.md` (folder and architecture plan), `SCENES.md` (scene-by-scene description), `ASSETS.md` (art and audio needed), and `TOC.md` (table of contents)

**What you get:** A complete document set that the build, evaluate, and review steps will hold the game accountable to.

**Things to know:** The quality of this step determines the quality of the result. Be specific — "a top-down zombie shooter with wave-based spawning and a high-score screen" is much more useful than "a zombie game". You can edit the documents before running `/gm-asset`.

---

## `/gm-asset`

**What it does:** Makes sure every art and audio file listed in `ASSETS.md` actually exists, and generates one visual reference image per scene described in `SCENES.md`, before the build starts.

**When to run it:** After `/gm-gdd`, before `/gm-build`.

**What happens behind the scenes:**
- Reads `ASSETS.md` to find every asset the game needs
- For assets you have already provided: dispatches an Analyst helper to inspect your image files and record what they contain
- For assets that are missing: generates them via an image generation API (Gemini or xAI, depending on your configuration)
- For each entry in `SCENES.md`: generates a target reference image at `references/scene_<name>.png` from the scene description, art direction, and your provided art style
- Updates `ASSETS.md` with the actual file paths

**What you get:** Art files in `assets/`, scene reference images in `references/`, and a fully resolved `ASSETS.md` ready for the build step. The scene references become the visual contract that `/gm-evaluate` later compares running screenshots against.

**Things to know:** You can re-run `/gm-asset` at any milestone if you add new assets to `ASSETS.md` or replace image files. It will only process what has changed.

---

## `/gm-build`

**What it does:** Implements the game — all the GDScript code, scenes, and unit tests — by coordinating a team of specialised helpers.

**When to run it:** After `/gm-asset`. Requires a completed `/gm-gdd` in the current milestone.

**What happens behind the scenes:**
- Reads `PLAN.md` to find pending tasks, starting with the riskiest ones
- Dispatches Workers (up to 3 in parallel) — each Worker implements one game system and its unit tests, then reports back
- After every 5 or so workers, dispatches a Verifier — a helper that compiles the project headlessly and runs the unit tests
- After the Verifier passes, dispatches a Reviewer — a helper with domain knowledge about Godot pitfalls (physics, UI, animation, etc.) that checks for common mistakes
- If the Reviewer finds problems, new tasks are added to `PLAN.md` and the cycle continues
- The build ends only when every task in `PLAN.md` is marked `verified` and the last review round found nothing new

**What you get:** Game code in `src/`, scenes in `scenes/`, unit tests in `tests/`.

**Things to know:** You cannot write game code yourself while in this step — the permission system blocks it. The main agent coordinates; Workers do the actual writing. If the same task fails three times, the build stops and asks you what to do.

---

## `/gm-verify`

**What it does:** Runs a fast mechanical check of the whole project — compile, unit tests, and file structure.

**When to run it:** After `/gm-build`, and again after each `/gm-fixgap`.

**What happens behind the scenes:**
- Runs the Godot headless build to check for compile errors
- Runs all unit tests in `tests/` via `gdUnit4`
- Checks that every file listed in `stage_schemas.json` for the current milestone exists

**What you get:** A printed verification report with a pass/fail verdict per check and the full output of any failures. On success, `/gm-verify` appends a `verify` event to `.godotmaker/stage.jsonl`.

**Things to know:** `/gm-verify` is a prerequisite for `/gm-evaluate`. If it fails, the build still has problems that need fixing — go back to `/gm-build` or file an issue description for `/gm-fixgap`.

---

## `/gm-evaluate`

**What it does:** Independently assesses whether the game matches what the GDD promised, using end-to-end tests and screenshots.

**When to run it:** After `/gm-verify` passes.

**What happens behind the scenes:**
- Reads `GDD.md`, `SCENES.md`, and `PLAN.md` fresh — with no memory of the build process
- Writes end-to-end tests in `e2e/` that exercise every described feature through simulated player input
- Runs those tests and records which pass and which fail
- Takes screenshots of each scene and compares them against reference images using a visual quality check
- Produces a final verdict: approve or reject, with a list of specific problems if rejected

**What you get:** `.godotmaker/evaluation.json` (the full verdict) and screenshots in `e2e/screenshots/`.

**Things to know:** The evaluator cannot write game code or touch `src/` — it is strictly read-only on game files. A rejection is not a failure; it is information. The problem list feeds directly into `/gm-fixgap`.

---

## `/gm-fixgap`

**What it does:** Reads the evaluation's problem list and dispatches workers to fix each issue.

**When to run it:** After `/gm-evaluate` rejects the build.

**What happens behind the scenes:**
- Reads `.godotmaker/evaluation.json` and `GAP.md` (a prioritised list of issues)
- Dispatches Workers to address each critical and major issue, with the same Worker → Verifier → Reviewer cycle as `/gm-build`
- Archives the current `GAP.md` to `.godotmaker/gaps/<n>/` so every iteration is preserved

**What you get:** Updated game code, with `GAP.md` moved to the archive.

**Things to know:** After `/gm-fixgap` finishes, run `/gm-verify` and then `/gm-evaluate` again. The loop continues until `/gm-evaluate` approves or you decide to stop.

---

## `/gm-accept`

**What it does:** Presents the approved build to you and records your decision.

**When to run it:** After `/gm-evaluate` approves.

**What happens behind the scenes:**
- Shows you the final evaluation summary and screenshots
- Asks: accept, reject (go back to `/gm-fixgap`), or stop
- Records your answer in `.godotmaker/stage.jsonl`

**What you get:** A recorded acceptance event, or a clear instruction to loop back.

**Things to know:** Rejecting here is valid — if you see something in the screenshots you do not like, you can send it back for another round. Your decision is always the final word.

---

## `/gm-finalize`

**What it does:** Closes out the milestone cleanly — archives records, writes a summary, and stamps it as done.

**When to run it:** After `/gm-accept` records an acceptance.

**What happens behind the scenes:**
- Writes `.godotmaker/final_report.json` summarising what was built, what tasks were completed, and the evaluation result
- Archives milestone documents (`GDD.md`, `PLAN.md`, etc.) so they are not overwritten by the next milestone

**What you get:** A clean project ready for the next milestone, with the current milestone's records preserved.

**Things to know:** After `/gm-finalize`, the next step is another `/gm-gdd` if you want to add more features. `/gm-scaffold` does not run again — the project already exists.

---

## What is a milestone?

One milestone = one round of `/gm-gdd` → `/gm-asset` → `/gm-build` → `/gm-verify` → `/gm-evaluate` → (fixgap loop) → `/gm-accept` → `/gm-finalize`.

The first milestone builds the core game. Each subsequent milestone adds a new feature set or major revision. This lets you grow the game incrementally without starting from scratch, and it keeps each `/gm-build` session small enough to be reliable.

For a bird's-eye view of how the phases connect, see [how-it-works.md](how-it-works.md).
