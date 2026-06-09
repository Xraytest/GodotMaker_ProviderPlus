#!/usr/bin/env bash
# Migrate from the original npm global installation to the current branch version.
# This script helps you:
# 1. Keep the original npm global installation intact
# 2. Set up the current branch version for use
# 3. Switch between versions easily using aliases
#
# Usage:
#   bash scripts/migrate_to_branch.sh [--alias-name gm-branch] [--dry-run]
#
# Options:
#   --alias-name <name>  Custom alias name (default: gm-branch)
#   --dry-run            Show what would be done without making changes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
ALIAS_NAME="gm-branch"
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --alias-name)
            ALIAS_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: bash scripts/migrate_to_branch.sh [--alias-name gm-branch] [--dry-run]"
            echo ""
            echo "Migrate from npm global installation to current branch version."
            echo ""
            echo "Options:"
            echo "  --alias-name <name>  Custom alias name (default: gm-branch)"
            echo "  --dry-run            Show what would be done without making changes"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "GodotMaker Branch Migration Helper"
echo "=========================================="
echo ""

# Check if original godotmaker is installed
info "Checking for original godotmaker-cli installation..."
if command -v godotmaker &>/dev/null; then
    ORIGINAL_PATH=$(command -v godotmaker)
    success "Original godotmaker found at: $ORIGINAL_PATH"
    
    # Try to get version
    if godotmaker --version &>/dev/null; then
        ORIGINAL_VERSION=$(godotmaker --version 2>&1 | head -1)
        info "Original version: $ORIGINAL_VERSION"
    fi
else
    warning "Original godotmaker-cli not found in PATH. You may not have it installed globally."
fi

# Check Node.js and npm
info "Checking Node.js and npm..."
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js: $NODE_VERSION"
else
    error "Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

if command -v npm &>/dev/null; then
    NPM_VERSION=$(npm --version)
    success "npm: $NPM_VERSION"
else
    error "npm not found. Please install npm first."
    exit 1
fi

# Check Python
info "Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    error "Python not found. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
success "Python: $PYTHON_VERSION"

# Determine shell config file
SHELL_CONFIG=""
if [[ -n "${BASH_VERSION:-}" ]] || [[ -n "${ZSH_VERSION:-}" ]]; then
    if [[ -n "${ZSH_VERSION:-}" ]] && [[ -f "$HOME/.zshrc" ]]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [[ -f "$HOME/.bash_profile" ]]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    else
        SHELL_CONFIG="$HOME/.bashrc"
    fi
fi

info "Shell config file: $SHELL_CONFIG"

echo ""
echo "=========================================="
echo "Migration Plan"
echo "=========================================="
echo ""
info "This script will:"
echo "  1. Keep your original 'godotmaker' command unchanged"
echo "  2. Create an alias '$ALIAS_NAME' for the current branch version"
echo "  3. Add the alias to your shell config ($SHELL_CONFIG)"
echo "  4. Verify the branch version works correctly"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    warning "DRY RUN MODE - No changes will be made"
    echo ""
    info "Would add the following to $SHELL_CONFIG:"
    echo "---"
    echo "# GodotMaker branch version alias (added by migrate_to_branch.sh)"
    echo "alias $ALIAS_NAME='cd $REPO_ROOT && $PYTHON tools/publish.py --agent claude-code'"
    echo "---"
    echo ""
    info "After sourcing your shell config, you can use:"
    echo "  godotmaker      # Original npm version"
    echo "  $ALIAS_NAME     # Current branch version"
    exit 0
fi

# Confirm before proceeding
echo -n "Proceed with migration? [y/N] "
read -r CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    info "Migration cancelled."
    exit 0
fi

echo ""
info "Setting up branch version alias..."

# Create the alias command
ALIAS_COMMAND="alias $ALIAS_NAME='cd $REPO_ROOT && $PYTHON tools/publish.py --agent claude-code'"
ALIAS_COMMENT="# GodotMaker branch version alias (added by migrate_to_branch.sh on $(date '+%Y-%m-%d %H:%M:%S'))"

# Check if alias already exists
if grep -q "alias $ALIAS_NAME=" "$SHELL_CONFIG" 2>/dev/null; then
    warning "Alias '$ALIAS_NAME' already exists in $SHELL_CONFIG"
    echo -n "Overwrite existing alias? [y/N] "
    read -r OVERWRITE
    if [[ "$OVERWRITE" =~ ^[Yy]$ ]]; then
        # Remove old alias
        sed -i.bak "/alias $ALIAS_NAME=/d" "$SHELL_CONFIG"
        success "Removed existing alias"
    else
        info "Keeping existing alias. Migration complete."
        exit 0
    fi
fi

# Add alias to shell config
{
    echo ""
    echo "$ALIAS_COMMENT"
    echo "$ALIAS_COMMAND"
} >> "$SHELL_CONFIG"

success "Added alias to $SHELL_CONFIG"

# Create a backup reminder
if [[ -f "${SHELL_CONFIG}.bak" ]]; then
    info "Backup of previous config: ${SHELL_CONFIG}.bak"
fi

echo ""
info "To activate the new alias, run:"
echo "  source $SHELL_CONFIG"
echo ""
info "Or restart your terminal."

echo ""
echo "=========================================="
echo "Testing the Setup"
echo "=========================================="
echo ""

# Test by running the alias command directly
info "Testing branch version publish script..."
cd "$REPO_ROOT"
if $PYTHON tools/publish.py --help &>/dev/null; then
    success "Branch version publish script works correctly"
else
    warning "Could not test publish script. Please verify manually."
fi

echo ""
echo "=========================================="
echo "Migration Complete!"
echo "=========================================="
echo ""
info "You can now use:"
echo "  godotmaker      # Original npm global version (unchanged)"
echo "  $ALIAS_NAME     # Current branch version"
echo ""
info "Example usage:"
echo "  cd my-game-project"
echo "  $ALIAS_NAME .    # Run branch version on current project"
echo ""
warning "Remember to run 'source $SHELL_CONFIG' or restart your terminal to use the new alias."
echo ""
