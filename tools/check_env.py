#!/usr/bin/env python3
"""Check that the GodotMaker development environment is correctly set up.

Verifies: Git, Python, Node.js, Godot, Claude Code, API keys, pip packages.

Usage:
    python tools/check_env.py
"""
import os
import re
import shutil
import subprocess
import sys


class EnvCheck:
    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.warnings: list[str] = []

    def ok(self, msg: str):
        self.passed.append(msg)
        print(f"  [PASS] {msg}")

    def fail(self, msg: str):
        self.failed.append(msg)
        print(f"  [FAIL] {msg}")

    def warn(self, msg: str):
        self.warnings.append(msg)
        print(f"  [WARN] {msg}")


def get_version(cmd: str, pattern: str = r"(\d+(?:\.\d+)+)") -> str | None:
    """Run `cmd --version` and extract version number."""
    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout + result.stderr
        match = re.search(pattern, output)
        return match.group(1) if match else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def parse_version(v: str) -> tuple[int, ...]:
    """Parse '4.4.1' to (4, 4, 1)."""
    return tuple(int(x) for x in v.split(".")[:3])


# ── Individual checks ──────────────────────────────────────────


def check_git(r: EnvCheck):
    print("\n--- Git ---")
    version = get_version("git")
    if not version:
        r.fail("Git not found. Install: https://git-scm.com/downloads")
        return

    if parse_version(version) >= (2, 30):
        r.ok(f"Git {version} (>= 2.30)")
    else:
        r.fail(f"Git {version} too old (>= 2.30 required)")

    # Check identity config
    for key, label in [("user.name", "user.name"), ("user.email", "user.email")]:
        try:
            res = subprocess.run(
                ["git", "config", key],
                capture_output=True, text=True, timeout=5,
            )
            val = res.stdout.strip()
            if val:
                r.ok(f"Git {label}: {val}")
            else:
                r.warn(f"Git {label} not set. Run: git config --global {key} \"...\"")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


def check_python(r: EnvCheck):
    print("\n--- Python ---")
    v = sys.version_info
    version = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 9):
        r.ok(f"Python {version} (>= 3.9)")
    else:
        r.fail(f"Python {version} too old (>= 3.9 required)")

    # Check key packages
    packages = {
        "google-genai": "google.genai",
        "requests": "requests",
        "pillow": "PIL",
        "numpy": "numpy",
    }
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
            r.ok(f"Package '{pkg_name}' installed")
        except ImportError:
            r.fail(f"Package '{pkg_name}' missing. Run: pip install {pkg_name}")


def check_node(r: EnvCheck):
    print("\n--- Node.js ---")
    version = get_version("node")
    if not version:
        r.fail("Node.js not found. Install: https://nodejs.org")
        return

    if int(version.split(".")[0]) >= 18:
        r.ok(f"Node.js {version} (>= 18)")
    else:
        r.fail(f"Node.js {version} too old (>= 18 required)")

    if shutil.which("npx"):
        r.ok("npx available")
    else:
        r.fail("npx not found (should come with Node.js)")


def check_godot(r: EnvCheck):
    print("\n--- Godot ---")
    for cmd in ("godot", "godot4"):
        version = get_version(cmd)
        if version and parse_version(version)[:2] >= (4, 4):
            r.ok(f"Godot {version} (>= 4.4), command: {cmd}")
            return
        elif version:
            r.fail(f"Godot {version} too old (>= 4.4 required)")
            return

    r.warn(
        "Godot not found on PATH. Provide the full path when running publish, "
        "or add it to PATH."
    )


def check_claude(r: EnvCheck):
    print("\n--- Claude Code ---")
    cmd = (
        shutil.which("claude")
        or shutil.which("claude.cmd")
        or shutil.which("claude.exe")
    )
    if cmd:
        r.ok(f"Claude Code found: {cmd}")
    else:
        r.fail("Claude Code not found. Install: npm install -g @anthropic-ai/claude-code")


def check_api_keys(r: EnvCheck):
    print("\n--- API Keys ---")
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if google_key:
        masked = google_key[:8] + "..." + google_key[-4:] if len(google_key) > 12 else "***"
        r.ok(f"GOOGLE_API_KEY set ({masked})")

        # Quick connectivity test
        try:
            from google import genai  # noqa: F401
            r.ok("google-genai import OK")
        except Exception as e:
            r.warn(f"google-genai import failed: {e}")
    else:
        r.fail(
            "GOOGLE_API_KEY not set (required for image gen + VQA). "
            "Get one: https://aistudio.google.com/apikey"
        )

    # Optional keys
    if os.environ.get("XAI_API_KEY"):
        r.ok("XAI_API_KEY set (optional)")
    else:
        r.warn("XAI_API_KEY not set (optional, cheaper image generation)")

    if os.environ.get("TRIPO3D_API_KEY"):
        r.ok("TRIPO3D_API_KEY set (optional)")
    else:
        r.warn("TRIPO3D_API_KEY not set (optional, 3D model generation)")


# ── Main ───────────────────────────────────────────────────────


def main():
    print("GodotMaker Environment Check")
    print("=" * 40)

    r = EnvCheck()

    check_git(r)
    check_python(r)
    check_node(r)
    check_godot(r)
    check_claude(r)
    check_api_keys(r)

    # Summary
    total = len(r.passed) + len(r.failed) + len(r.warnings)
    print(f"\n{'=' * 40}")
    print(f"Total: {total} checks")
    print(f"  PASS: {len(r.passed)}")
    print(f"  FAIL: {len(r.failed)}")
    print(f"  WARN: {len(r.warnings)}")

    if r.failed:
        print("\nFailed checks:")
        for f in r.failed:
            print(f"  - {f}")
        print("\nFix the above issues before using GodotMaker.")
        sys.exit(1)
    else:
        print("\nAll required checks passed! Ready to use GodotMaker.")
        sys.exit(0)


if __name__ == "__main__":
    main()
