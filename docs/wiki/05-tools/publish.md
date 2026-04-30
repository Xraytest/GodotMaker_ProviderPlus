# Publish

`publish.py` installs the GodotMaker framework into a target Godot project folder. You'll run it once to create a project, and again whenever you upgrade GodotMaker.

## Fresh install

Point `publish.py` at an empty folder (or an existing Godot project folder). It will create everything it needs:

```bash
python tools/publish.py /path/to/my-game
```

On Windows:

```powershell
python tools\publish.py C:\Games\my-game
```

The first time you run this, the script will ask you for the full path to your Godot executable. Enter it when prompted — you only need to do this once per project.

**What gets created:**

| Location | What it is |
|----------|------------|
| `.claude/skills/` | All GodotMaker slash commands (the `/gm-*` commands and supporting skills) |
| `.claude/agents/` | Definitions for the worker, verifier, reviewer, and analyst helpers |
| `.claude/settings.json` | Tells Claude Code which hook scripts to run and when |
| `.claude/godotmaker.yaml` | Your Godot executable path (specific to this machine) |
| `.godotmaker/hooks/` | The enforcement scripts that keep the AI on track |
| `.godotmaker/config.yaml` | Per-project settings (model choice, asset generation provider, etc.) |
| `.godotmaker/version` | Records which GodotMaker version is installed here |
| `tools/` | Utility scripts (`check_env.py`, `check_project.py`, `asset_gen.py`, etc.) |
| `.claude/templates/` | Document templates used by `/gm-gdd` and other commands |
| `CLAUDE.md` | Per-project instructions that Claude Code reads at the start of every session |
| `assets/sprites`, `assets/audio`, `assets/fonts`, `assets/ui`, `references/` | Standard asset folders |

The script also registers the `godot-mcp` server (which lets Claude Code talk to the Godot editor), initializes a git repository if one doesn't exist, and creates a `.gitignore` with the right entries.

## Upgrading an existing project

Run the same command again inside an already-published project. GodotMaker compares its own version number against the version recorded in `.godotmaker/version` and decides what to do:

| Upgrade type | What happens |
|--------------|--------------|
| **Patch** (e.g. 0.3.0 to 0.3.1) | Proceeds automatically — backward-compatible bug fixes. Applies any pending migrations |
| **Minor** (e.g. 0.3.0 to 0.4.0) | Shows the changelog, asks you to confirm. Applies any pending migrations |
| **Major** (e.g. 0.x to 1.x) | Requires `--force` — breaking changes that need a clean re-initialization. Skips migrations and re-baselines after re-deploy |
| **Same version** | Always proceeds — useful when you've made local changes to the framework. Also applies any pending migrations you added locally without bumping `VERSION` |
| **Downgrade** | Blocked by default; requires `--force` to override. Migrations are not rolled back (no down-migrations); restore from VCS if needed |

> Migrations and bump levels are independent. Each migration is a
> timestamped script under `migrations/`; targets record what they've
> applied in `.godotmaker/applied_migrations.json`. PATCH and MINOR both
> apply any pending scripts. See [`../../versioning.md`](../../versioning.md)
> for the full policy.

For the full upgrade policy and migration script details, see [`../../versioning.md`](../../versioning.md). For what changed in each release, see the [changelog](../08-reference/changelog.md).

## Options

```bash
python tools/publish.py --force /path/to/my-game
```

`--force` does four things at once:

1. Clears `.claude/skills/` before re-deploying, removing any skills left over from a previous version.
2. Overwrites `.claude/settings.json` even if you've already customized it.
3. Skips the confirmation prompts for minor and major upgrades.
4. Allows downgrades.

For **major** upgrades with `--force`, the clean-up is more thorough: `.claude/skills/`, `.claude/agents/`, `.claude/config/`, `.claude/templates/`, `.godotmaker/hooks/`, `tools/`, and the runtime state files are all wiped and rebuilt from scratch.

## What is preserved on upgrade

These files are never overwritten by a normal publish (only `--force` can change `settings.json`):

| File | Why it is kept |
|------|---------------|
| `CLAUDE.md` | You may have added project-specific instructions |
| `.claude/settings.json` | You may have adjusted hook behavior |
| `.claude/godotmaker.yaml` | Contains your machine-specific Godot path |
| `.godotmaker/config.yaml` | Contains your project-specific preferences |

Your game code, scenes, assets, and planning documents (`GDD.md`, `PLAN.md`, etc.) are not touched by publish — it only manages the framework layer.
