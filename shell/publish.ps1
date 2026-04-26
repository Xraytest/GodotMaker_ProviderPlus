# Publish GodotMaker skills into a target Godot project directory.
# Usage: .\shell\publish.ps1 [-Force|--force] <target_godot_project_dir>
#
# On upgrade, compares VERSION against the target's .godotmaker/version:
#   PATCH  -> auto-proceed
#   MINOR  -> show changelog, prompt for confirmation
#   MAJOR  -> strong warning, prompt for confirmation
# Use -Force (or --force) to skip confirmation prompts and allow downgrades.
#
# Thin wrapper - all logic is in tools/publish.py.
# KEEP IN SYNC with publish.sh (Linux/macOS equivalent)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Script = Join-Path $RepoRoot "tools\publish.py"

# Parse args manually to accept both -Force and --force
$ForceFlag = $false
$Target = $null

foreach ($a in $args) {
    if ($a -eq "-Force" -or $a -eq "--force") {
        $ForceFlag = $true
    } elseif (-not $Target) {
        $Target = $a
    }
}

if (-not $Target) {
    Write-Host "Usage: .\shell\publish.ps1 [-Force|--force] <target_godot_project_dir>"
    exit 1
}

$pyArgs = @($Script)
if ($ForceFlag) { $pyArgs += "--force" }
$pyArgs += $Target

& python @pyArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
