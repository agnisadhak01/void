# Launch extracted Cursor reference client with isolated user data.
# Usage: .\scripts\cursor-dev\launch-cursor-ref.ps1 [-Version 3.7.21]

param(
    [string]$Version = "",
    [string[]]$ExtraArgs = @()
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "Get-CursorRefPaths.ps1")

if (-not $Version) {
    $Version = Get-DefaultCursorVersion -RepoRoot $RepoRoot
}

$paths = Get-CursorRefPaths -Version $Version -RepoRoot $RepoRoot

if (-not (Test-Path $paths.CursorExe)) {
    throw "Cursor reference exe not found at $($paths.CursorExe). Run setup-cursor-ref.ps1 and extract first."
}

New-Item -ItemType Directory -Force -Path $paths.UserDataDir, $paths.ExtensionsDir | Out-Null

$launchArgs = @(
    "--user-data-dir", $paths.UserDataDir,
    "--extensions-dir", $paths.ExtensionsDir
) + $ExtraArgs

Write-Host "Launching Cursor reference $Version" -ForegroundColor Cyan
Write-Host "  Exe: $($paths.CursorExe)"
Write-Host "  User data: $($paths.UserDataDir)"

& $paths.CursorExe @launchArgs
exit $LASTEXITCODE
