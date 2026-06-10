# Validate versioned Cursor extraction layout and manifest.
# Usage: .\scripts\cursor-dev\verify-extraction.ps1 [-Version 3.7.21]

param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "Get-CursorRefPaths.ps1")

if (-not $Version) {
    $Version = Get-DefaultCursorVersion -RepoRoot $RepoRoot
}

$paths = Get-CursorRefPaths -Version $Version -RepoRoot $RepoRoot
$required = @(
    $paths.CursorExe,
    (Join-Path $paths.AppResources "package.json"),
    (Join-Path $paths.AppResources "product.json"),
    (Join-Path $paths.AppResources "out\main.js"),
    (Join-Path $paths.AppResources "extensions\cursor-mcp"),
    $paths.Manifest
)

$failures = @()
foreach ($item in $required) {
    if (-not (Test-Path $item)) {
        $failures += $item
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Extraction verification FAILED for version $Version" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host "  missing: $f" -ForegroundColor Red
    }
    exit 1
}

$pkg = Get-Content (Join-Path $paths.AppResources "package.json") -Raw | ConvertFrom-Json
if ($pkg.version -ne $Version) {
    Write-Host "Version mismatch: folder expects $Version but package.json is $($pkg.version)" -ForegroundColor Red
    exit 1
}

$manifest = Get-Content $paths.Manifest -Raw | ConvertFrom-Json
Write-Host "Extraction verification PASSED" -ForegroundColor Green
Write-Host "  Cursor version: $($pkg.version)"
Write-Host "  VS Code distro: $($pkg.distro)"
Write-Host "  Manifest extensions: $($manifest.cursorExtensions.Count)"
Write-Host "  Workbench contrib folders: $($manifest.workbenchContrib.Count)"
Write-Host "  Installed client: $($paths.CursorExe)"
