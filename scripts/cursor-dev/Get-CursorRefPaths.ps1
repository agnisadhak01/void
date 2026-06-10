# Cursor reference dev environment — shared path helpers.

function Get-CursorRefPaths {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version,
        [string]$RepoRoot = (Get-Location).Path
    )

    $extractRoot = Join-Path $RepoRoot "cursor\extracted\$Version"
    return [ordered]@{
        Version         = $Version
        RepoRoot        = $RepoRoot
        ExtractRoot     = $extractRoot
        InstalledClient = Join-Path $extractRoot "installed-client"
        AppResources    = Join-Path $extractRoot "app-resources"
        Manifest        = Join-Path $extractRoot "COMPONENT_MANIFEST.json"
        InstallLog      = Join-Path $extractRoot "install.log"
        CursorExe       = Join-Path $extractRoot "installed-client\Cursor.exe"
        BuildOutput     = Join-Path $RepoRoot "cursor\build\$Version"
        UserDataDir     = Join-Path $RepoRoot ".tmp\cursor-ref-user-data"
        ExtensionsDir   = Join-Path $RepoRoot ".tmp\cursor-ref-extensions"
        InstallerPath   = Join-Path $RepoRoot "cursor\CursorSetup-x64-$Version.exe"
    }
}

function Get-DefaultCursorVersion {
    param([string]$RepoRoot = (Get-Location).Path)

    $patchesRoot = Join-Path $RepoRoot "cursor\patches"
    if (Test-Path $patchesRoot) {
        $versions = Get-ChildItem $patchesRoot -Directory | Sort-Object Name -Descending
        if ($versions.Count -gt 0) {
            return $versions[0].Name
        }
    }

    return "3.7.21"
}
