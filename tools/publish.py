#!/usr/bin/env python3
"""Publish GodotMaker skills into a target Godot project directory.

Flattens skills/core/* and skills/reviewer/* into .claude/skills/,
copies tools, config, hooks, templates, and sets up godot-mcp.

Supports versioned upgrades: compares source VERSION against the
target's .godotmaker/version and prompts accordingly.

Usage:
    python tools/publish.py <target_godot_project_dir>
    python tools/publish.py --force <target_godot_project_dir>
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from _version import SemVer, parse_version
from migrate import (
    LegacyTargetWithMigrationsError,
    TrackerCorruptionError,
    baseline_applied,
    run_migrations,
)


class VersionCheckResult(NamedTuple):
    proceed: bool
    level: str  # "FRESH" | "SAME" | "PATCH" | "MINOR" | "MAJOR" | "DOWNGRADE"
    target_ver: SemVer | None
    source_ver: SemVer | None

EXCLUDE_DIRS = {"__pycache__", "doc_source", ".workspace"}

DEFAULT_CONFIG_TEMPLATE = Path(__file__).resolve().parent.parent / "config" / "config.yaml.default"


def read_source_version(repo_root: Path) -> SemVer | None:
    """Read VERSION file from GodotMaker repo root."""
    version_file = repo_root / "VERSION"
    if not version_file.exists():
        return None
    return parse_version(version_file.read_text(encoding="utf-8"))


def read_target_version(target: Path) -> SemVer | None:
    """Read deployed version from target project's .godotmaker/version."""
    version_file = target / ".godotmaker" / "version"
    if not version_file.exists():
        return None
    return parse_version(version_file.read_text(encoding="utf-8"))


def write_target_version(target: Path, version: SemVer):
    """Stamp the deployed version into the target project."""
    version_dir = target / ".godotmaker"
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "version").write_text(str(version) + "\n", encoding="utf-8")


def read_changelog_section(repo_root: Path, version: SemVer) -> str | None:
    """Extract the CHANGELOG.md section for a specific version."""
    changelog = repo_root / "CHANGELOG.md"
    if not changelog.exists():
        return None
    content = changelog.read_text(encoding="utf-8")
    # Match from "## [version]" to next "## [" or end
    pattern = rf"(## \[{re.escape(str(version))}\].*?)(?=\n## \[|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else None


def check_version_upgrade(repo_root: Path, target: Path, force: bool
                          ) -> VersionCheckResult:
    """Compare source and target versions, prompt user if needed.

    Returns a VersionCheckResult with fields:
      - proceed: True if publish should continue
      - level: "FRESH" | "SAME" | "PATCH" | "MINOR" | "MAJOR" | "DOWNGRADE"
      - target_ver: version currently in the target project (None if fresh)
      - source_ver: version in the GodotMaker repo (None if no VERSION file)
    """
    source_ver = read_source_version(repo_root)
    if not source_ver:
        return VersionCheckResult(True, "FRESH", None, None)

    target_ver = read_target_version(target)

    # Fresh install — no existing version
    if not target_ver:
        print(f"\n  GodotMaker v{source_ver} (fresh install)")
        return VersionCheckResult(True, "FRESH", None, source_ver)

    # Same version
    if source_ver == target_ver:
        print(f"\n  GodotMaker v{source_ver} (same version, re-publishing)")
        return VersionCheckResult(True, "SAME", target_ver, source_ver)

    # Downgrade
    if source_ver < target_ver:
        print(f"\n  WARNING: Downgrade detected: v{target_ver} -> v{source_ver}")
        if not force:
            print("  Use --force to downgrade.")
            return VersionCheckResult(False, "DOWNGRADE", target_ver, source_ver)
        return VersionCheckResult(True, "DOWNGRADE", target_ver, source_ver)

    # Upgrade — determine severity
    if source_ver.major != target_ver.major:
        level = "MAJOR"
        color = "!!! "
        msg = "Breaking changes — backup your project first!"
    elif source_ver.minor != target_ver.minor:
        level = "MINOR"
        color = ">>  "
        msg = "Backward-compatible new features / behavior changes. Review changelog below."
    else:
        level = "PATCH"
        color = "    "
        msg = "Backward-compatible bug fixes."

    print(f"\n  {color}Upgrade: v{target_ver} -> v{source_ver} ({level})")
    print(f"  {color}{msg}")

    # Show changelog for the new version
    changelog = read_changelog_section(repo_root, source_ver)
    if changelog:
        print()
        for line in changelog.splitlines():
            print(f"  {line}")
        print()

    # MAJOR upgrade — block incremental, require --force for clean re-init
    if level == "MAJOR" and not force:
        print("  MAJOR upgrades require --force (clean re-initialization).")
        print("  This will wipe .claude/skills/ and .godotmaker/hooks/ and re-deploy.")
        try:
            answer = input("  Proceed with MAJOR upgrade? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer not in ("y", "yes"):
            print("  Upgrade cancelled.")
            return VersionCheckResult(False, level, target_ver, source_ver)

    # MINOR upgrades require confirmation (unless --force)
    elif level == "MINOR" and not force:
        try:
            answer = input(f"  Proceed with {level} upgrade? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer not in ("y", "yes"):
            print("  Upgrade cancelled.")
            return VersionCheckResult(False, level, target_ver, source_ver)

    return VersionCheckResult(True, level, target_ver, source_ver)


def select_migration_action(level: str, force: bool) -> str:
    """Decide whether publish should baseline or run migrations.

    Returns "baseline" or "run".

    - FRESH (no `.godotmaker/version`) and MAJOR `--force` (cleanup wiped
      state) start at the latest format and have nothing to migrate from
      → "baseline" (mark every current migration as applied without
      executing it).
    - All other resolved upgrade levels — SAME, PATCH, MINOR, DOWNGRADE
      with `--force` — already have a tracked state → "run" (apply
      pending migrations). A legacy target lacking the tracker file is
      handled inside `run_migrations()`: empty `migrations/` →
      bootstrap an empty tracker; non-empty → raise
      `LegacyTargetWithMigrationsError` and force the user to choose a
      recovery path.

    MAJOR without `--force` is filtered out by check_version_upgrade()
    before this function is called, so the (level="MAJOR", force=False)
    case is unreachable in practice; if it does arrive (defensive),
    treating it as "run" is harmless because publish would have aborted.
    """
    if level == "FRESH" or (level == "MAJOR" and force):
        return "baseline"
    return "run"


def copy_tree(src: Path, dst: Path):
    """Copy directory tree, overwriting destination. Excludes __pycache__ etc."""
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE_DIRS))


# ── Publish steps ──────────────────────────────────────────────


def publish_skills(repo_root: Path, skills_target: Path) -> int:
    """Flatten-copy skills/core/* and skills/reviewer/* to target.

    Directory names starting with `_` (e.g. _shared/) are excluded — they hold
    cross-skill source material rather than self-contained skills, and are
    distributed by publish_shared_refs() instead.
    """
    count = 0
    for layer in ("core", "reviewer"):
        layer_dir = repo_root / "skills" / layer
        if not layer_dir.exists():
            continue
        for skill_dir in sorted(layer_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            if skill_dir.name.startswith("_"):
                continue
            dst = skills_target / skill_dir.name
            copy_tree(skill_dir, dst)
            count += 1

    # Copy _read_config.sh helper
    helper = repo_root / "shell" / "_read_config.sh"
    if helper.exists():
        shutil.copy2(helper, skills_target / "_read_config.sh")

    print(f"Published skills: {count}")
    return count


SHARED_HEADER_TEMPLATE = (
    "<!-- AUTO-GENERATED from skills/core/_shared/{filename}. "
    "Do NOT edit this deployed copy — it is overwritten on every publish. "
    "Edit the source under skills/core/_shared/ instead. -->\n\n"
)


def publish_shared_refs(repo_root: Path, skills_target: Path) -> int:
    """Distribute shared reference docs into each consumer skill's references/.

    The single source of truth is `skills/core/_shared/`. `_shared/manifest.json`
    maps each shared filename to the skills that consume it. For every entry,
    `<file>` is written into `<skill>/references/<file>` (with an
    AUTO-GENERATED header prepended) so deployed skills are self-contained —
    no `.claude/skills/_shared/` directory exists at runtime, and editors
    opening a deployed copy see an explicit warning at the top.
    """
    shared_dir = repo_root / "skills" / "core" / "_shared"
    manifest_path = shared_dir / "manifest.json"
    if not manifest_path.exists():
        return 0

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in {manifest_path}: {e.msg} "
            f"(line {e.lineno}, col {e.colno})"
        ) from e
    files = manifest.get("files", {})
    distributions = 0
    for filename, target_skills in files.items():
        src = shared_dir / filename
        if not src.exists():
            raise FileNotFoundError(
                f"_shared/manifest.json references {filename}, but source "
                f"file does not exist at {src}."
            )
        deployed_content = (
            SHARED_HEADER_TEMPLATE.format(filename=filename)
            + src.read_text(encoding="utf-8")
        )
        for skill_name in target_skills:
            skill_root = skills_target / skill_name
            if not skill_root.exists():
                raise FileNotFoundError(
                    f"_shared/manifest.json maps {filename} -> {skill_name}, "
                    f"but skill directory {skill_root} does not exist (was "
                    f"publish_skills() called first?)."
                )
            references = skill_root / "references"
            references.mkdir(parents=True, exist_ok=True)
            (references / filename).write_text(deployed_content,
                                               encoding="utf-8")
            distributions += 1

    print(f"Distributed shared refs: {distributions} copies "
          f"({len(files)} source file(s))")
    return distributions


def publish_directory(src: Path, dst: Path, label: str, count_pattern: str = "*.py"):
    """Copy a directory from repo to target, printing file count."""
    if not src.exists():
        return
    copy_tree(src, dst)
    count = len(list(dst.glob(count_pattern)))
    print(f"Published {label} ({count} files)")


def deploy_settings(repo_root: Path, config_dir: Path, force: bool):
    """Deploy settings.json (hooks configuration) — only if not exists."""
    src = repo_root / "config" / "settings.json"
    dst = config_dir / "settings.json"
    if not src.exists():
        return
    if not dst.exists() or force:
        shutil.copy2(src, dst)
        print("Created settings.json (hooks enabled)")
    else:
        print("settings.json already exists, skipping (use --force to overwrite)")


def deploy_claude_md(repo_root: Path, target: Path):
    """Deploy CLAUDE.md from template if not exists."""
    dst = target / "CLAUDE.md"
    if dst.exists():
        return
    template = repo_root / "templates" / "game-claude.md"
    if template.exists():
        shutil.copy2(template, dst)
        print("Created CLAUDE.md")


def create_godotmaker_yaml(config_file: Path):
    """Interactive godotmaker.yaml generation on first run."""
    if config_file.exists():
        print("godotmaker.yaml already exists, skipping")
        return

    print()
    print("No godotmaker.yaml found. Let's create one.")
    print("Enter the full path to your Godot executable")
    print("  (e.g. C:/path/to/Godot_v4.4-stable_win64.exe)")

    try:
        godot_path = input("godot_path: ").strip()
    except (EOFError, KeyboardInterrupt):
        godot_path = ""

    if not godot_path:
        print("Warning: no path provided, defaulting to 'godot' (must be on PATH)")
        godot_path = "godot"

    config_file.write_text(
        f'# Host-specific tool paths — not committed to git\n'
        f'godot_path: "{godot_path}"\n',
        encoding="utf-8",
    )
    print(f"Created {config_file}")


def create_project_config(target: Path):
    """Create .godotmaker/config.yaml with default settings."""
    config_dir = target / ".godotmaker"
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        print(".godotmaker/config.yaml already exists, skipping")
        return

    config_dir.mkdir(parents=True, exist_ok=True)
    if DEFAULT_CONFIG_TEMPLATE.exists():
        shutil.copy2(DEFAULT_CONFIG_TEMPLATE, config_file)
    else:
        config_file.write_text("# GodotMaker config — template not found\n", encoding="utf-8")
    print("Created .godotmaker/config.yaml")


def deploy_stage_schemas(repo_root: Path, target: Path):
    """Deploy stage_schemas.json to .godotmaker/ directory."""
    src = repo_root / "config" / "stage_schemas.json"
    dst = target / ".godotmaker" / "stage_schemas.json"
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print("Deployed stage_schemas.json")


def create_project_dirs(target: Path):
    """Create standard game project directories."""
    dirs = [
        "assets/sprites", "assets/audio", "assets/fonts", "assets/ui",
        "references",
    ]
    created = 0
    for d in dirs:
        p = target / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created += 1
    if created:
        print(f"Created {created} project directories")


def read_godot_path(config_file: Path) -> str:
    """Read godot_path from godotmaker.yaml."""
    if not config_file.exists():
        return "godot"
    for line in config_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("godot_path:"):
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
            if val:
                return val
    return "godot"


def register_mcp(target: Path, godot_path: str):
    """Register godot-mcp MCP server."""
    # Remove existing registration first
    claude_cmd = (
        shutil.which("claude")
        or shutil.which("claude.cmd")
        or shutil.which("claude.exe")
    )
    if not claude_cmd:
        print("WARNING: claude CLI not found. Skipping godot-mcp registration.")
        print("  Install Claude Code, then run manually:")
        print(f'  claude mcp add godot -e GODOT_PATH="{godot_path}" -- npx @coding-solo/godot-mcp')
        return

    if not shutil.which("npx"):
        print("WARNING: npx not found. Skipping godot-mcp registration.")
        print("  Install Node.js, then run manually:")
        print(f'  claude mcp add godot -e GODOT_PATH="{godot_path}" -- npx @coding-solo/godot-mcp')
        return

    try:
        subprocess.run(
            [claude_cmd, "mcp", "remove", "godot"],
            cwd=str(target), capture_output=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass

    print("Registering godot-mcp MCP server...")
    cmd = [claude_cmd, "mcp", "add", "godot",
           "-e", f"GODOT_PATH={godot_path}", "--"]

    if sys.platform == "win32":
        cmd.extend(["cmd", "/c", "npx", "@coding-solo/godot-mcp"])
    else:
        cmd.extend(["npx", "@coding-solo/godot-mcp"])

    try:
        result = subprocess.run(cmd, cwd=str(target), timeout=60)
        if result.returncode == 0:
            print("godot-mcp registered")
        else:
            print("WARNING: godot-mcp registration failed. Register manually if needed.")
    except (subprocess.TimeoutExpired, OSError):
        print("WARNING: godot-mcp registration failed. Register manually if needed.")


def ensure_git_repo(target: Path):
    """Initialize git repo with initial commit if needed.

    Worktree isolation (used by parallel workers) requires at least one commit.
    Without it: 'fatal: not a valid object name: HEAD'.
    """
    git_dir = target / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(["git", "init"], cwd=str(target),
                           capture_output=True, timeout=15)
            print("Initialized git repository")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("WARNING: git not found. Initialize manually: git init && git commit --allow-empty -m 'init'")
            return

    # Check if there are any commits
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(target), capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            return  # Already has commits
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return

    # No commits yet — create initial empty commit
    try:
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial commit (GodotMaker publish)"],
            cwd=str(target), capture_output=True, timeout=15,
        )
        print("Created initial git commit (required for worktree isolation)")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("WARNING: could not create initial commit. Run manually: git commit --allow-empty -m 'init'")


def ensure_gitignore(target: Path):
    """Ensure .gitignore covers .claude/ and .godotmaker/ runtime state.

    .claude/ is fully ignored (Claude Code config, not project code).
    .godotmaker/ is selectively ignored: hooks and config are tracked,
    runtime state (metrics, session state) is ignored. This allows
    git worktrees to inherit hooks automatically.
    """
    gitignore = target / ".gitignore"

    # Lines that must be present
    entries_needed = [
        ".claude/",
        ".godotmaker/state.json",
        ".godotmaker/metrics.jsonl",
        ".godotmaker/metrics_current.jsonl",
        ".godotmaker/traces/",
        ".godotmaker/applied_migrations.json",
    ]

    # If upgrading from old blanket ignore, remove it
    old_blanket = ".godotmaker/"

    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        line_set = set(line.strip() for line in lines)

        # Remove old blanket .godotmaker/ ignore
        updated = False
        if old_blanket in line_set:
            lines = [line for line in lines if line.strip() != old_blanket]
            line_set = set(line.strip() for line in lines)
            updated = True

        # Add missing entries
        missing = [e for e in entries_needed if e not in line_set]
        if missing:
            for entry in missing:
                lines.append(entry)
            updated = True

        if updated:
            gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print("Updated .gitignore (selective .godotmaker/ ignore for worktree support)")
    else:
        gitignore.write_text("\n".join(entries_needed) + "\n", encoding="utf-8")
        print("Created .gitignore")


# ── Main ───────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Publish GodotMaker skills into a target Godot project directory"
    )
    parser.add_argument("target", help="Path to the target Godot project directory")
    parser.add_argument("--force", action="store_true",
                        help="Clean existing .claude/skills/ before publishing; "
                             "skip upgrade confirmation prompts")
    args = parser.parse_args()

    # Resolve paths
    repo_root = Path(__file__).resolve().parent.parent
    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)

    # Version check — may abort on MAJOR/MINOR without --force
    proceed, level, target_ver, source_ver = check_version_upgrade(
        repo_root, target, args.force
    )
    if not proceed:
        sys.exit(1)

    config_dir = target / ".claude"
    skills_target = config_dir / "skills"
    config_file = config_dir / "godotmaker.yaml"

    # MAJOR upgrade with --force: clean all framework-managed content
    if level == "MAJOR" and args.force:
        # Directories to wipe and recreate
        for d in [
            skills_target,                      # .claude/skills/
            config_dir / "agents",              # .claude/agents/
            config_dir / "config",              # .claude/config/
            config_dir / "templates",           # .claude/templates/
            target / ".godotmaker" / "hooks",   # .godotmaker/hooks/
            target / "tools",                   # tools/
        ]:
            if d.exists():
                print(f"  Cleaning {d}")
                shutil.rmtree(d)
        # State files to remove
        for f in [
            target / ".godotmaker" / "state.json",
            target / ".godotmaker" / "metrics.jsonl",
            target / ".godotmaker" / "metrics_current.jsonl",
            target / ".godotmaker" / "stage_schemas.json",
            target / ".godotmaker" / "applied_migrations.json",
        ]:
            if f.exists():
                f.unlink()
                print(f"  Removed {f.name}")
        print("  Full rebuild: framework content cleaned.")
        print("  Preserved: CLAUDE.md, godotmaker.yaml, config.yaml")
    elif args.force and skills_target.exists():
        print(f"Force: cleaning {skills_target}")
        shutil.rmtree(skills_target)

    print(f"Publishing to: {target}")
    skills_target.mkdir(parents=True, exist_ok=True)

    # Publish all components
    publish_skills(repo_root, skills_target)
    publish_shared_refs(repo_root, skills_target)
    publish_directory(repo_root / "agents", config_dir / "agents", "agents/", "*.md")
    publish_directory(repo_root / "tools", target / "tools", "tools/")
    publish_directory(repo_root / "config", config_dir / "config", "config/", "*")
    godotmaker_dir = target / ".godotmaker"
    godotmaker_dir.mkdir(parents=True, exist_ok=True)
    publish_directory(repo_root / "hooks", godotmaker_dir / "hooks", "hooks/")
    deploy_settings(repo_root, config_dir, args.force)
    publish_directory(repo_root / "templates", config_dir / "templates", "templates/", "*.md")
    deploy_claude_md(repo_root, target)

    # Interactive config generation
    create_godotmaker_yaml(config_file)
    create_project_config(target)
    deploy_stage_schemas(repo_root, target)
    create_project_dirs(target)

    # Register MCP server
    godot_path = read_godot_path(config_file)
    register_mcp(target, godot_path)

    # Ensure .gitignore
    ensure_gitignore(target)

    # Initialize git repo with initial commit (required for worktree isolation)
    ensure_git_repo(target)

    # Migration handling — per-target applied tracking
    # (.godotmaker/applied_migrations.json), decoupled from the bump level.
    # select_migration_action() decides between two paths:
    #   "baseline" — skip execution, mark all current migrations as applied
    #     (FRESH / MAJOR --force: target starts at the latest format and
    #     has nothing to migrate from).
    #   "run" — apply any pending migrations
    #     (SAME / PATCH / MINOR / DOWNGRADE: target has tracked state.
    #     Legacy targets without applied_migrations.json are bootstrapped
    #     to an empty tracker if migrations/ is empty, or rejected with
    #     LegacyTargetWithMigrationsError if it isn't — handled inside
    #     run_migrations() itself.)
    action = select_migration_action(level, args.force)
    if action == "baseline":
        n = baseline_applied(target)
        if n:
            scope = "fresh install" if level == "FRESH" else "MAJOR re-init"
            print(f"Baselined {n} migration(s) for {scope}.")
    else:
        try:
            ok = run_migrations(target)
        except TrackerCorruptionError as e:
            print(f"\nERROR: applied-migrations tracker is corrupt:\n  {e}",
                  file=sys.stderr)
            sys.exit(2)
        except LegacyTargetWithMigrationsError as e:
            print(f"\nERROR: legacy target needs explicit handling:\n  {e}",
                  file=sys.stderr)
            sys.exit(3)
        if not ok:
            print("\nMigration failed. Published files are updated but migrations incomplete.")
            print("Fix the issue and re-run publish, or use --force for clean install.")
            sys.exit(1)

    # Stamp deployed version
    if source_ver:
        write_target_version(target, source_ver)

    print(f"\nDone (v{source_ver or '?'}). Run 'python tools/check_env.py' in the target project to verify setup.")


if __name__ == "__main__":
    main()
