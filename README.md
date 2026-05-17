# GodotMaker

[![License: BUSL 1.1](https://img.shields.io/badge/License-BUSL_1.1-orange.svg)](LICENSE)
[![Godot 4.x](https://img.shields.io/badge/Godot-4.x-blue?logo=godotengine)](https://godotengine.org)
[![CI](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml/badge.svg)](https://github.com/RandallLiuXin/GodotMaker/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-online-teal)](https://RandallLiuXin.github.io/GodotMaker/)

**English** | [中文](README.zh-CN.md)

> **Describe your game. Play it. Own it.** — Source-available, local-first, and yours to build on.

GodotMaker turns plain-language descriptions into real, playable Godot games. Type *"a Vampire Survivors-style game with three weapon types and a level-up system"* — wait a few minutes — open Godot and play it. No engine experience required, no subscription, no platform lock-in. The project lives on your disk and is yours to keep, edit, and ship.

## What you get

- **A real Godot project** on your computer. Open it in the Godot editor any time and change anything you want.
- **Free** to use. Runs locally with the AI tools you already have. No platform fees, no usage caps.
- **Source-available under BUSL 1.1.** No black box, no closed-platform resale.
- **The full Godot ecosystem** is at your fingertips — addons, exporters, the editor itself. Your game can grow as far as you can take it.

## Who is this for?

- You have an idea for a game but you've never learned a game engine.
- You're a designer, hobbyist, student, or creator who wants to see your idea actually run.
- You want a working prototype fast — and you want to keep building on it long after the AI is done.

GodotMaker is for the gap between *"I have an idea"* and *"I have a playable thing."* And from there, the whole Godot ecosystem is yours — keep iterating in the editor, plug in community addons, learn as you go, and grow your prototype into the game you actually want to ship.

## How it works (in 30 seconds)

1. You install GodotMaker into an empty folder. One command.
2. You open Claude Code in that folder and type `/gm-scaffold`. The AI sets up the Godot project, addons, and folder layout. Then `/gm-gdd` interviews you about the game you want.
3. You run the remaining seven commands one at a time. Between each, the AI does the work — writes the code, generates the art, builds the project, plays the game, takes screenshots, scores the result.
4. When you're happy, you accept and finalise. Open the project in Godot and play.

A small game typically takes about 30 minutes of *your* attention spread across the session — the AI runs in the background between commands.

[Full walkthrough →](https://RandallLiuXin.github.io/GodotMaker/wiki/01-getting-started/first-game/)

## Quick start

```bash
# 1. Clone this repository
git clone https://github.com/RandallLiuXin/GodotMaker.git
cd GodotMaker

# 2. Install dependencies and check your environment
pip install -r tools/requirements.txt
python tools/check_env.py

# 3. Deploy GodotMaker into a new folder for your game.
# Choose the agent you want to use for this project.

# Claude Code
python tools/publish.py /path/to/my-game
cd /path/to/my-game
claude

# Codex
python tools/publish.py --agent codex /path/to/my-game
cd /path/to/my-game
codex
```

Inside [Claude Code](https://claude.ai/code) or
[Codex](https://openai.com/codex/), run the nine GodotMaker commands in order,
starting with `/gm-scaffold` for Claude Code or `$gm-scaffold` for Codex.
See [Your first game](https://RandallLiuXin.github.io/GodotMaker/wiki/01-getting-started/first-game/) for a full walk-through.

## What you'll need

| Tool | Why |
|---|---|
| [Godot 4.5+](https://godotengine.org) (recommended; 4.3/4.4 still supported) | The game engine your project runs in |
| [Claude Code](https://claude.ai/code) or [Codex](https://openai.com/codex/) | The coding agent you talk to |
| Python 3.10+ | Runs the helper scripts |
| `GOOGLE_API_KEY` | Free tier; used to generate art for your game |

Optional: .NET SDK 8.0+ if you want a C# game project instead of GDScript.

## Documentation

- [**Get started in 30 minutes**](https://RandallLiuXin.github.io/GodotMaker/wiki/01-getting-started/first-game/) — your first game, step by step
- [How it works](https://RandallLiuXin.github.io/GodotMaker/wiki/02-concepts/how-it-works/) — what each command does and why
- [Common problems](https://RandallLiuXin.github.io/GodotMaker/wiki/04-troubleshooting/common-problems/) — when something goes wrong
- [Full wiki](https://RandallLiuXin.github.io/GodotMaker/) — every page

## Roadmap

What's coming next:

- **More high-quality plugin skills** — first-class support for popular Godot community addons (Phantom Camera, Dialogic, Beehave, GodotSteam, …).
- **Richer asset generation workflows** — more pipelines for sprites, animations, tilesets, audio, and 3D models.
- **Multi-platform publishing** — one-click export to Steam, iOS, Google Play, and Web.
- **Graphical UI** — a visual front-end so you don't have to use the command line.

Full backlog and shipped items: [`ROADMAP.md`](ROADMAP.md).

## Contributing

Contributions are welcome — bug fixes, new reviewer skills, addon integrations, translations, anything. Start with the [Development Setup](https://RandallLiuXin.github.io/GodotMaker/wiki/07-contributing/development-setup/) and the [Contributing Guide](CONTRIBUTING.md).

## License

Business Source License 1.1. See [LICENSE](LICENSE). Each released version converts to Apache License 2.0 four years after that version is first publicly distributed. **The games you build with GodotMaker are not GodotMaker and are entirely yours**, subject to any third-party engine, asset, model-provider, runtime, or dependency terms that may apply.
