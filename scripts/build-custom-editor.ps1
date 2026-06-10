# Build Pulse (custom editor) Windows x64 executable from source.
# Wraps buildreact -> compile -> gulp with product.json-aware output verification.
#
# Usage:
#   .\scripts\build-custom-editor.ps1
#   .\scripts\build-custom-editor.ps1 -CopyToCursorBuild

param(
    [switch]$CopyToCursorBuild,
    [string]$CursorVersion = "3.7.21"
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot 'lib\Get-ProductInfo.ps1')

$product = Get-ProductInfo -RepoRoot $RepoRoot

$nodeMajor = (node -p "process.versions.node.split('.')[0]")
if ([int]$nodeMajor -gt 22) {
    Write-Warning "Node $(node -v) detected. Recommend v20.18.2 (see .nvmrc)."
}

Write-Host ""
Write-Host "Building $($product.NameLong) ($($product.ApplicationName))" -ForegroundColor Green
Write-Host "Expected output: $($product.PackagedExePath)" -ForegroundColor DarkGray

if (-not (Test-Path '.\node_modules')) {
    Write-Host "Running npm install..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$env:NODE_OPTIONS = '--max-old-space-size=8192'

Write-Host "Building React UI..." -ForegroundColor Cyan
npm run buildreact
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Compiling editor (one-shot)..." -ForegroundColor Cyan
npm run compile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Packaging Windows x64..." -ForegroundColor Cyan
npm run gulp vscode-win32-x64
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $product.PackagedExePath)) {
    Write-Host "Build finished but exe not found at $($product.PackagedExePath)" -ForegroundColor Red
    $alt = Get-ChildItem $product.GulpOutputDir -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($alt) {
        Write-Host "Found alternate exe: $($alt.FullName)" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host ""
Write-Host "Build succeeded." -ForegroundColor Green
Write-Host "  Product: $($product.NameLong)"
Write-Host "  Launch:  $($product.PackagedExePath)"

if ($CopyToCursorBuild) {
    $dest = Join-Path $RepoRoot "cursor\build\custom\$CursorVersion"
    Write-Host "Copying gulp output to $dest ..." -ForegroundColor Cyan
    if (Test-Path $dest) {
        Remove-Item -Recurse -Force $dest
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    robocopy $product.GulpOutputDir $dest /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy to $dest failed"
    }
    Write-Host "  Side-by-side copy: $dest\$($product.ExeName)" -ForegroundColor Green
}
