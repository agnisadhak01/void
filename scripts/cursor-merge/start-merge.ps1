# Extract Cursor client and build file inventory for a version.
# Does NOT select features to merge — record decisions in docs/merges/{version}/MERGE_REPORT.md.
# Usage:
#   .\scripts\cursor-merge\start-merge.ps1 -Version 3.7.21 -InstallerPath cursor\CursorSetup-x64-3.7.21.exe
#   .\scripts\cursor-merge\start-merge.ps1 -Version 3.7.21 -FromInstalled

param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [string]$InstallerPath = "",
    [switch]$FromInstalled
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

if (-not $InstallerPath) {
    $InstallerPath = "cursor\CursorSetup-x64-$Version.exe"
}

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "Cursor merge extraction for version $Version"
Write-Host "Branch target: Cursor-merge-$Version"
Write-Host "Output: cursor\extracted\$Version\"
Write-Host ""

$extractScript = Join-Path $repoRoot "scripts\extract-cursor-client.ps1"
$extractArgs = @{
    Version       = $Version
    InstallerPath = $InstallerPath
    OutputRoot    = "cursor\extracted\$Version"
}

if ($FromInstalled) {
    $extractArgs.FromInstalled = $true
}

& $extractScript @extractArgs

$mergeReportDir = Join-Path $repoRoot "docs\merges\$Version"
$mergeReport = Join-Path $mergeReportDir "MERGE_REPORT.md"
$template = Join-Path $repoRoot "docs\templates\MERGE_REPORT.template.md"

if (-not (Test-Path $mergeReport)) {
    Write-Step "Creating merge report from template"
    New-Item -ItemType Directory -Force -Path $mergeReportDir | Out-Null
    if (Test-Path $template) {
        (Get-Content $template -Raw) -replace '\{VERSION\}', $Version -replace '\{PREVIOUS_VERSION\}', 'PREVIOUS' |
            Set-Content -Path $mergeReport -Encoding UTF8
        Write-Host "Created $mergeReport"
    }
    else {
        Write-Warning "Template not found at $template"
    }
}
else {
    Write-Host "Merge report already exists: $mergeReport"
}

Write-Step "Next steps (human decisions required)"
Write-Host "1. Open docs\merges\$Version\MERGE_REPORT.md"
Write-Host "2. Fill User goals and paste changelog"
Write-Host "3. For each item, set Decision: implement | adapt | ignore | defer"
Write-Host "4. Optional inventory diff:"
Write-Host "   .\scripts\cursor-merge\diff-manifests.ps1 -Old cursor\extracted\OLD\COMPONENT_MANIFEST.json -New cursor\extracted\$Version\COMPONENT_MANIFEST.json -OutputPath docs\merges\$Version\manifest-diff.txt"
Write-Host "5. Implement only implement/adapt rows - see docs\CURSOR_MERGE_WORKFLOW.md"
