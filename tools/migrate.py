#!/usr/bin/env python3
"""Version migration runner for GodotMaker publish upgrades.

Discovers and executes migration scripts between version ranges.
Each migration directory covers one MINOR version bump (e.g., 0.3_to_0.4/).
Scripts within are executed in sorted order.

Migration chain example: from=0.2.0, to=0.4.0
  → runs 0.2_to_0.3/*.py, then 0.3_to_0.4/*.py

Usage (standalone):
    python tools/migrate.py <target_project> --from 0.3.0 --to 0.4.0

Typically called from publish.py, not directly.
"""
import importlib.util
import sys
from pathlib import Path

from _version import SemVer, parse_version

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def find_migration_chain(from_ver: SemVer, to_ver: SemVer) -> list[Path]:
    """Find ordered list of migration directories for the version range.

    Only MINOR boundaries have migrations. For example, 0.2.1 → 0.4.0
    needs: 0.2_to_0.3/, 0.3_to_0.4/.

    Returns empty list if no migrations needed (same minor, or PATCH-only).
    """
    if from_ver.major != to_ver.major:
        # MAJOR upgrade — no incremental migration
        return []

    if from_ver.minor >= to_ver.minor:
        # Same minor or downgrade — no migration
        return []

    chain = []
    for minor in range(from_ver.minor, to_ver.minor):
        dir_name = f"{from_ver.major}.{minor}_to_{from_ver.major}.{minor + 1}"
        migration_dir = MIGRATIONS_DIR / dir_name
        if migration_dir.is_dir():
            chain.append(migration_dir)

    return chain


def collect_scripts(migration_dir: Path) -> list[Path]:
    """Collect .py migration scripts in sorted order."""
    scripts = sorted(migration_dir.glob("*.py"))
    return [s for s in scripts if s.name != "__init__.py"]


def run_migration_script(script_path: Path, target: Path) -> bool:
    """Load and execute a single migration script.

    Returns True on success, False on failure.
    """
    migrations_root = str(MIGRATIONS_DIR)
    if migrations_root not in sys.path:
        sys.path.insert(0, migrations_root)

    try:
        spec = importlib.util.spec_from_file_location(
            f"migration_{script_path.stem}", str(script_path)
        )
        if spec is None or spec.loader is None:
            print(f"  [error] Cannot load {script_path.name}")
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "migrate"):
            print(f"  [error] {script_path.name} has no migrate() function")
            return False

        module.migrate(target)
        return True

    except Exception as e:
        print(f"  [error] {script_path.name} failed: {e}")
        return False


def run_migrations(target: Path, from_ver: SemVer, to_ver: SemVer) -> bool:
    """Execute all migrations in the version chain.

    Returns True if all migrations succeeded (or none needed).
    Returns False if any migration failed (chain aborted).
    """
    if from_ver.major != to_ver.major:
        print(f"\n  MAJOR upgrade ({from_ver} -> {to_ver}): incremental migration not supported.")
        print("  Use --force for a clean re-initialization.")
        return False

    chain = find_migration_chain(from_ver, to_ver)

    if not chain:
        return True  # No migrations needed

    print(f"\n  Running migrations: {from_ver} -> {to_ver}")
    print(f"  Migration steps: {len(chain)}")

    for migration_dir in chain:
        step_name = migration_dir.name
        scripts = collect_scripts(migration_dir)

        if not scripts:
            print(f"\n  [{step_name}] (no scripts)")
            continue

        print(f"\n  [{step_name}]")

        for script in scripts:
            print(f"    {script.name}:")
            if not run_migration_script(script, target):
                print(f"\n  Migration aborted at {step_name}/{script.name}")
                print("  Target project may be in a partially migrated state.")
                print("  Fix the issue and re-run publish, or use --force for clean install.")
                return False

    print("\n  All migrations completed successfully.")
    return True


def main():
    """CLI entry point for standalone testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Run GodotMaker version migrations")
    parser.add_argument("target", help="Path to target game project")
    parser.add_argument("--from", dest="from_ver", required=True, help="Source version (e.g., 0.3.0)")
    parser.add_argument("--to", dest="to_ver", required=True, help="Target version (e.g., 0.4.0)")
    args = parser.parse_args()

    from_v = parse_version(args.from_ver)
    to_v = parse_version(args.to_ver)
    if not from_v or not to_v:
        print("Error: invalid version format. Use MAJOR.MINOR.PATCH")
        sys.exit(1)

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: {target} is not a directory")
        sys.exit(1)

    success = run_migrations(target, from_v, to_v)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
