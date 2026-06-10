# Verify prerequisites for the Cursor reference workspace.
# Usage: .\scripts\cursor-dev\setup-cursor-ref.ps1 [-Version 3.7.21]

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
$minFreeGb = 2

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "Cursor reference environment setup (version $Version)"

$drive = (Split-Path $RepoRoot -Qualifier)
$freeGb = [math]::Round((Get-PSDrive ($drive.TrimEnd(':'))).Free / 1GB, 2)
Write-Host "Free disk on $drive $freeGb GB (need >= $minFreeGb GB)"
if ($freeGb -lt $minFreeGb) {
    Write-Warning "Low disk space. Extraction may fail."
}

$running = Get-Process -Name "Cursor" -ErrorAction SilentlyContinue
if ($running) {
    Write-Warning "Cursor is running ($($running.Count) processes). Close before installer-based extraction."
}
else {
    Write-Host "Cursor not running - OK for installer extraction" -ForegroundColor Green
}

if (Test-Path $paths.InstallerPath) {
    $sizeMb = [math]::Round((Get-Item $paths.InstallerPath).Length / 1MB, 2)
    Write-Host "Installer: $($paths.InstallerPath) ($sizeMb MB)" -ForegroundColor Green
}
else {
    Write-Warning "Installer not found: $($paths.InstallerPath)"
    Write-Host "Download from https://cursor.com/downloads or use -FromInstalled extraction."
}

if (Test-Path $paths.CursorExe) {
    Write-Host "Extracted client: $($paths.CursorExe)" -ForegroundColor Green
}
else {
    Write-Host "Extraction not present. Run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\cursor-merge\start-merge.ps1 -Version $Version -FromInstalled"
    Write-Host "  # or with installer (Cursor must be closed):"
    Write-Host "  .\scripts\cursor-merge\start-merge.ps1 -Version $Version -InstallerPath cursor\CursorSetup-x64-$Version.exe"
}

Write-Step "Next commands"
Write-Host "  .\scripts\cursor-dev\verify-extraction.ps1 -Version $Version"
Write-Host "  .\scripts\cursor-dev\launch-cursor-ref.ps1 -Version $Version"
