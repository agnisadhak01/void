# Apply JSON-only configuration patches to cursor app-resources (reference copy).
# Does not modify minified out/ bundles.
#
# Usage:
#   .\scripts\cursor-dev\apply-config-mods.ps1 -Version 3.7.21
#   .\scripts\cursor-dev\apply-config-mods.ps1 -Version 3.7.21 -PatchFile cursor\mods\3.7.21\product-tweaks.json

param(
    [string]$Version = "",
    [string]$PatchFile = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "Get-CursorRefPaths.ps1")

if (-not $Version) {
    $Version = Get-DefaultCursorVersion -RepoRoot $RepoRoot
}

$paths = Get-CursorRefPaths -Version $Version -RepoRoot $RepoRoot
$appRoot = $paths.AppResources

if (-not (Test-Path $appRoot)) {
    throw "App resources not found at $appRoot"
}

function Merge-JsonFile {
    param(
        [string]$TargetPath,
        [hashtable]$Patches
    )

    if (-not (Test-Path $TargetPath)) {
        throw "Target JSON not found: $TargetPath"
    }

    $json = Get-Content $TargetPath -Raw | ConvertFrom-Json
    foreach ($key in $Patches.Keys) {
        $json | Add-Member -NotePropertyName $key -NotePropertyValue $Patches[$key] -Force
    }
    $json | ConvertTo-Json -Depth 100 | Set-Content -Path $TargetPath -Encoding UTF8
    Write-Host "Patched $TargetPath" -ForegroundColor Green
}

if ($PatchFile) {
    if (-not (Test-Path $PatchFile)) {
        throw "Patch file not found: $PatchFile"
    }

    $patch = Get-Content $PatchFile -Raw | ConvertFrom-Json
    foreach ($entry in $patch.files) {
        $target = Join-Path $appRoot $entry.relativePath
        $hashtable = @{}
        foreach ($prop in $entry.properties.PSObject.Properties) {
            $hashtable[$prop.Name] = $prop.Value
        }
        Merge-JsonFile -TargetPath $target -Patches $hashtable
    }
}
else {
    $defaultPatch = Join-Path $RepoRoot "cursor\mods\$Version\product-tweaks.json"
    if (Test-Path $defaultPatch) {
        & $PSCommandPath -Version $Version -PatchFile $defaultPatch
    }
    else {
        Write-Host "No patch file specified and no default at $defaultPatch" -ForegroundColor Yellow
        Write-Host "Create a patch file or pass -PatchFile with JSON:"
        Write-Host @'
{
  "files": [
    {
      "relativePath": "product.json",
      "properties": { "someKey": "someValue" }
    }
  ]
}
'@
    }
}
