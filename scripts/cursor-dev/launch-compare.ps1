# Launch Cursor reference and Pulse dev side-by-side for merge QA.
# Usage: .\scripts\cursor-dev\launch-compare.ps1 [-Version 3.7.21] [-SkipBuildReact]

param(
    [string]$Version = "",
    [switch]$SkipBuildReact,
    [switch]$CursorOnly,
    [switch]$EditorOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "Get-CursorRefPaths.ps1")

if (-not $Version) {
    $Version = Get-DefaultCursorVersion -RepoRoot $RepoRoot
}

$launchCursor = Join-Path $PSScriptRoot "launch-cursor-ref.ps1"
$startDev = Join-Path $RepoRoot "scripts\start-dev.ps1"

if (-not $EditorOnly) {
    Write-Host "Starting Cursor reference ($Version)..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", $launchCursor,
        "-Version", $Version
    ) | Out-Null
    Start-Sleep -Seconds 2
}

if (-not $CursorOnly) {
    Write-Host "Starting Pulse dev environment..." -ForegroundColor Cyan
    $devArgs = @("-ExecutionPolicy", "Bypass", "-File", $startDev)
    if ($SkipBuildReact) {
        $devArgs += "-SkipBuildReact"
    }
    Start-Process powershell -ArgumentList $devArgs -WorkingDirectory $RepoRoot | Out-Null
}

Write-Host "Compare mode started. Use isolated user-data dirs for both apps." -ForegroundColor Green
