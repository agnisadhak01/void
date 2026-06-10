# Sync patched app-resources into installed-client and optional build output folder.
# Usage: .\scripts\cursor-dev\repack-cursor-ref.ps1 -Version 3.7.21 [-CopyToBuild]

param(
    [string]$Version = "",
    [switch]$CopyToBuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "Get-CursorRefPaths.ps1")

if (-not $Version) {
    $Version = Get-DefaultCursorVersion -RepoRoot $RepoRoot
}

$paths = Get-CursorRefPaths -Version $Version -RepoRoot $RepoRoot
$sourceApp = $paths.AppResources
$targetApp = Join-Path $paths.InstalledClient "resources\app"

if (-not (Test-Path $paths.InstalledClient)) {
    throw "installed-client missing at $($paths.InstalledClient). Re-run extraction."
}

if (-not (Test-Path $sourceApp)) {
    throw "app-resources missing at $sourceApp"
}

Write-Host "==> Syncing app-resources to installed-client" -ForegroundColor Cyan
robocopy $sourceApp $targetApp /MIR /NFL /NDL /NJH /NJS /nc /ns /np /XD node_modules | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

Write-Host "Repack complete: $($paths.CursorExe)" -ForegroundColor Green

if ($CopyToBuild) {
    Write-Host "==> Copying to build output $($paths.BuildOutput)" -ForegroundColor Cyan
    if (Test-Path $paths.BuildOutput) {
        Remove-Item -Recurse -Force $paths.BuildOutput
    }
    New-Item -ItemType Directory -Force -Path $paths.BuildOutput | Out-Null
    robocopy $paths.InstalledClient $paths.BuildOutput /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy to build output failed with exit code $LASTEXITCODE"
    }
    Write-Host "Build copy: $($paths.BuildOutput)\Cursor.exe" -ForegroundColor Green
}

& (Join-Path $PSScriptRoot "verify-extraction.ps1") -Version $Version
