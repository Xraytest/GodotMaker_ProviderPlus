# Migration Guide: From npm Global to Branch Version

This guide helps you migrate from the original npm global installation to the current branch version **without uninstalling the original**.

## Quick Migration

Run the migration helper script:

```bash
bash scripts/migrate_to_branch.sh
```

This will:
1. Keep your original `godotmaker` command (npm global version) unchanged
2. Create a new alias `gm-branch` for the current branch version
3. Add the alias to your shell configuration file

After running the script and sourcing your shell config:

```bash
source ~/.bashrc  # or ~/.zshrc, depending on your shell
```

You can now use both versions:

```bash
godotmaker      # Original npm global version
gm-branch       # Current branch version
```

## Manual Setup

If you prefer manual setup, add this alias to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
alias gm-branch='cd /path/to/GodotMaker && python3 tools/publish.py --agent claude-code'
```

Replace `/path/to/GodotMaker` with the actual path to your GodotMaker repository.

## Usage Examples

### Using the branch version on a project:

```bash
cd my-game-project
gm-branch .
```

### Using the original npm version:

```bash
cd my-game-project
godotmaker
```

### Switching between versions for different projects:

```bash
# Project A uses the branch version
cd project-a
gm-branch .

# Project B uses the stable npm version
cd ../project-b
godotmaker
```

## Advanced Options

The migration script supports several options:

```bash
# Custom alias name
bash scripts/migrate_to_branch.sh --alias-name gm-dev

# Dry run (see what would be done without making changes)
bash scripts/migrate_to_branch.sh --dry-run

# Show help
bash scripts/migrate_to_branch.sh --help
```

## Why Use This Approach?

- **No conflicts**: Keep the stable npm version while testing branch features
- **Easy switching**: Use aliases to switch between versions instantly
- **Safe testing**: Test new features without affecting production projects
- **Quick rollback**: If something breaks, just use the original `godotmaker` command

## Removing the Alias

To remove the branch alias:

1. Open your shell config file (`~/.bashrc`, `~/.zshrc`, etc.)
2. Remove the lines added by the migration script (look for the comment `# GodotMaker branch version alias`)
3. Run `source ~/.bashrc` (or restart your terminal)

Or simply run the migration script again with a different alias name to replace it.

## Troubleshooting

### "command not found: gm-branch"

Make sure you've sourced your shell configuration after running the migration:

```bash
source ~/.bashrc  # or ~/.zshrc
```

### Alias points to wrong path

Check that the path in your alias matches your GodotMaker repository location:

```bash
grep "gm-branch" ~/.bashrc
```

Update the path if needed and source your shell config again.

### Python not found

Ensure Python 3.10+ is installed and available as `python3` or `python`:

```bash
python3 --version
```

If Python is installed but not found, update the alias to use the correct Python path:

```bash
alias gm-branch='cd /path/to/GodotMaker && /usr/bin/python3 tools/publish.py --agent claude-code'
```
