# Compare two Cursor COMPONENT_MANIFEST.json files (file/component deltas only).
# Does NOT recommend what to merge — user decides in docs/merges/{version}/MERGE_REPORT.md.
# Usage:
#   .\scripts\cursor-merge\diff-manifests.ps1 -Old cursor\extracted\3.7.19\COMPONENT_MANIFEST.json -New cursor\extracted\3.7.21\COMPONENT_MANIFEST.json
#   .\scripts\cursor-merge\diff-manifests.ps1 -Old ... -New ... -OutputPath docs\merges\3.7.21\manifest-diff.txt

param(
    [Parameter(Mandatory = $true)]
    [string]$Old,
    [Parameter(Mandatory = $true)]
    [string]$New,
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Resolve-ManifestPath([string]$Path) {
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return Join-Path $repoRoot $Path
}

function Get-ExtensionNames($manifest) {
    if (-not $manifest.components.cursorExtensions) { return @() }
    return @($manifest.components.cursorExtensions | ForEach-Object { $_.name })
}

function Get-ContribNames($manifest) {
    if (-not $manifest.components.workbenchContrib) { return @() }
    return @($manifest.components.workbenchContrib | ForEach-Object { $_.name })
}

$oldPath = Resolve-ManifestPath $Old
$newPath = Resolve-ManifestPath $New

if (-not (Test-Path $oldPath)) { throw "Old manifest not found: $oldPath" }
if (-not (Test-Path $newPath)) { throw "New manifest not found: $newPath" }

$oldManifest = Get-Content $oldPath -Raw | ConvertFrom-Json
$newManifest = Get-Content $newPath -Raw | ConvertFrom-Json

$oldExt = Get-ExtensionNames $oldManifest
$newExt = Get-ExtensionNames $newManifest
$addedExt = $newExt | Where-Object { $_ -notin $oldExt }
$removedExt = $oldExt | Where-Object { $_ -notin $newExt }

$oldContrib = Get-ContribNames $oldManifest
$newContrib = Get-ContribNames $newManifest
$addedContrib = $newContrib | Where-Object { $_ -notin $oldContrib }
$removedContrib = $oldContrib | Where-Object { $_ -notin $newContrib }

$lines = @(
    "Cursor manifest diff"
    "==================="
    ""
    "Old: $Old"
    "  Cursor $($oldManifest.source.cursorVersion) | VS Code $($oldManifest.source.vscodeVersion) | commit $($oldManifest.source.vscodeCommit)"
    ""
    "New: $New"
    "  Cursor $($newManifest.source.cursorVersion) | VS Code $($newManifest.source.vscodeVersion) | commit $($newManifest.source.vscodeCommit)"
    ""
    "New cursor-* extensions ($($addedExt.Count)):"
)
if ($addedExt.Count -eq 0) { $lines += "  (none)" } else { $lines += $addedExt | ForEach-Object { "  + $_" } }

$lines += ""
$lines += "Removed cursor-* extensions ($($removedExt.Count)):"
if ($removedExt.Count -eq 0) { $lines += "  (none)" } else { $lines += $removedExt | ForEach-Object { "  - $_" } }

$lines += ""
$lines += "New workbench contrib folders ($($addedContrib.Count)):"
if ($addedContrib.Count -eq 0) { $lines += "  (none)" } else { $lines += $addedContrib | ForEach-Object { "  + $_" } }

$lines += ""
$lines += "Removed workbench contrib folders ($($removedContrib.Count)):"
if ($removedContrib.Count -eq 0) { $lines += "  (none)" } else { $lines += $removedContrib | ForEach-Object { "  - $_" } }

# Extension version bumps
$lines += ""
$lines += "Extension version changes:"
$versionChanges = @()
foreach ($newItem in $newManifest.components.cursorExtensions) {
    $oldItem = $oldManifest.components.cursorExtensions | Where-Object { $_.name -eq $newItem.name } | Select-Object -First 1
    if ($oldItem -and $oldItem.version -ne $newItem.version) {
        $versionChanges += "  $($newItem.name): $($oldItem.version) -> $($newItem.version)"
    }
}
if ($versionChanges.Count -eq 0) { $lines += "  (none)" } else { $lines += $versionChanges }

$report = $lines -join "`n"
Write-Host $report

if ($OutputPath) {
    $outFile = if ([System.IO.Path]::IsPathRooted($OutputPath)) { $OutputPath } else { Join-Path $repoRoot $OutputPath }
    New-Item -ItemType Directory -Force -Path (Split-Path $outFile) | Out-Null
    $report | Set-Content -Path $outFile -Encoding UTF8
    Write-Host ""
    Write-Host "Wrote $outFile"
}
