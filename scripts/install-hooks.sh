#!/usr/bin/env bash
# Install git hooks for GodotMaker development
# Usage: bash scripts/install-hooks.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."

# Install pre-commit hook (gitleaks)
PRECOMMIT_SRC="$REPO_ROOT/scripts/pre-commit"
PRECOMMIT_DST="$HOOKS_DIR/pre-commit"

if [ -f "$PRECOMMIT_DST" ] && [ ! -L "$PRECOMMIT_DST" ]; then
    echo "  Backing up existing pre-commit hook to pre-commit.bak"
    cp "$PRECOMMIT_DST" "$PRECOMMIT_DST.bak"
fi

ln -sf ../../scripts/pre-commit "$PRECOMMIT_DST"
echo "  Installed pre-commit hook as symlink (gitleaks secret scanning)"

# Verify gitleaks
if command -v gitleaks &> /dev/null; then
    echo "  gitleaks found: $(gitleaks version)"
else
    echo "  WARNING: gitleaks not installed. Hook will skip scanning."
    echo "  Install: https://github.com/gitleaks-io/gitleaks#installing"
fi

echo "Done. Git hooks installed successfully."
