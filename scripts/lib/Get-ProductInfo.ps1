# Shared product.json helpers for dev/build scripts.

function Get-ProductInfo {
    param(
        [string]$RepoRoot = (Get-Location).Path
    )

    $productJson = Join-Path $RepoRoot 'product.json'
    if (-not (Test-Path $productJson)) {
        throw "product.json not found at $productJson"
    }

    $product = Get-Content $productJson -Raw | ConvertFrom-Json
    $exeName = "$($product.nameShort).exe"

    return [ordered]@{
        NameShort       = $product.nameShort
        NameLong        = $product.nameLong
        ApplicationName = $product.applicationName
        DataFolderName  = $product.dataFolderName
        ExeName         = $exeName
        ElectronPath    = Join-Path $RepoRoot ".build/electron/$exeName"
        GulpOutputDir   = Join-Path (Split-Path $RepoRoot -Parent) "VSCode-win32-x64"
        PackagedExePath = Join-Path (Split-Path $RepoRoot -Parent) "VSCode-win32-x64/$exeName"
    }
}
