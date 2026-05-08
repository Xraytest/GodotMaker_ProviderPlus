# How it works

GodotMaker turns a description into a game by running 9 small steps in order. Each step is a slash command you type. Each step does one job and stops.

```mermaid
flowchart TD
    A[/gm-scaffold] --> B[/gm-gdd]
    B --> C[/gm-asset]
    C --> D[/gm-build]
    D --> E[/gm-verify]
    E --> F[/gm-evaluate]
    F --> G{approve?}
    G -- yes --> H[/gm-accept]
    G -- no --> I[/gm-fixgap]
    H --> J[/gm-finalize]
    I --> E
```

You are in control at every transition. Nothing runs while you aren't looking — you type the next command when you are ready to move on.

---

## The four phases

### Setup — `/gm-scaffold`, `/gm-gdd`, `/gm-asset`

These three commands prepare everything the game needs before a single line of gameplay code is written.

`/gm-scaffold` creates the empty Godot project: the right folder layout, the required addons, and a first git commit. You run it once per project, at the very beginning.

`/gm-gdd` interviews you about the game you want. It asks questions, then writes a Game Design Document (`GDD.md`), a task plan (`PLAN.md`), a folder layout (`STRUCTURE.md`), a scene list (`SCENES.md`), and an asset list (`ASSETS.md`). This document set is the contract everything else works from.

`/gm-asset` takes that asset list and either generates art files or analyses images you have already provided. The build step needs real art to work with — this command makes sure it exists.

### Make — `/gm-build`

`/gm-build` reads `PLAN.md` and implements the game. It does not write code itself. Instead, it hands each task to a specialised "Worker" — a focused helper that writes one system at a time and includes unit tests. Every few workers, a "Verifier" runs the headless Godot build and checks that the tests pass. Then a "Reviewer" checks the output against Godot-specific pitfalls (physics gotchas, UI layout rules, animation traps, etc.). If the reviewer finds issues, new tasks are added and the cycle continues until everything is clean.

### Check — `/gm-verify`, `/gm-evaluate`

`/gm-verify` does a fast mechanical check: does the project compile, do the unit tests pass, are there missing files?

`/gm-evaluate` is a completely fresh perspective. It has not seen the build process at all. It runs the game, takes screenshots, writes end-to-end tests, and scores the result against what `GDD.md` promised. If anything does not match — a feature missing, a scene looking wrong, the game crashing — it produces a rejection with a list of specific problems.

### Ship — `/gm-accept`, `/gm-fixgap`, `/gm-finalize`

If `/gm-evaluate` approves, you run `/gm-accept`. GodotMaker shows you the result and asks you to confirm. Your answer is recorded.

If `/gm-evaluate` rejects, you run `/gm-fixgap` instead. It reads the evaluation's problem list, generates a fix plan, dispatches workers to address each issue, and then loops back to `/gm-verify` and `/gm-evaluate`. This loop repeats until you get an approval.

Once you accept, `/gm-finalize` tidies up: it archives the tag's working docs into `docs/tags/<Tag>/`, writes a per-tag changelog, runs `git tag <Tag>` locally, and resets the per-tag runtime state. At that point you can start the next tag with another `/gm-gdd`, or stop here.

---

## What makes this not just a fancy chatbot

### File-lock permissions

When you run a role command, GodotMaker writes that role's name to a file called `.godotmaker/current_role`. A small Python script runs on every file write and refuses anything that role is not allowed to touch. For example: in `/gm-evaluate`, the evaluator can only write into `e2e/` and `.godotmaker/` — it cannot touch game code. In `/gm-build`, the main agent cannot write `.gd` or `.tscn` files directly; it must go through a Worker. This prevents the AI from taking shortcuts or breaking things while in the wrong role.

### The worker-verifier-reviewer loop

Inside `/gm-build` and `/gm-fixgap`, quality checks are not optional. A "completion check" hook runs when the session tries to end. If workers ran but verifier and reviewer did not, the session is blocked from finishing. The AI cannot declare build complete and skip the checks.

### The independent evaluator pass

`/gm-evaluate` starts fresh — it reads the GDD and the game files as if seeing them for the first time. It is not allowed to reuse conclusions from the build phase. This gives you an honest second opinion: not "did we write all the code?" but "does the game actually work as described?"

---

For a command-by-command breakdown, see [the-9-roles.md](the-9-roles.md).
