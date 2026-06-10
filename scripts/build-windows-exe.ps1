# Build a local Void Windows x64 executable.
# Full prerequisite graph and troubleshooting: docs/BUILD.md
# Ecosystem / CI releases: docs/ECOSYSTEM.md
#
# Usage (from repo root):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\scripts\build-windows-exe.ps1

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..

$nodeMajor = (node -p "process.versions.node.split('.')[0]")
if ([int]$nodeMajor -gt 22) {
    Write-Warning "Node $(node -v) detected. Void recommends v20.18.2 (see .nvmrc). Build may still work."
}

if (-not (Test-Path '.\node_modules')) {
    Write-Host "Running npm install..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Building Void React UI..." -ForegroundColor Cyan
$env:NODE_OPTIONS = '--max-old-space-size=8192'
npm run buildreact
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Compiling Void (one-shot; ~5-15 min)..." -ForegroundColor Cyan
npm run compile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Packaging Windows x64 executable (~25 min)..." -ForegroundColor Cyan
npm run gulp vscode-win32-x64
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

. (Join-Path $PSScriptRoot 'lib\Get-ProductInfo.ps1')
$product = Get-ProductInfo -RepoRoot (Get-Location).Path
Write-Host "`nDone. Launch:" -ForegroundColor Green
Write-Host "  $($product.PackagedExePath)"
