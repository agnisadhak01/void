# Build an inventory of extracted Cursor app resources (file listing only).
# Does NOT decide what to merge into Void — decisions belong in docs/merges/{version}/MERGE_REPORT.md.

param(
    [string]$AppRoot = "cursor\extracted\app-resources",
    [string]$OutputPath = "cursor\extracted\COMPONENT_MANIFEST.json"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRootPath = Join-Path $repoRoot $AppRoot
$outputFile = Join-Path $repoRoot $OutputPath

if (-not (Test-Path $appRootPath)) {
    throw "App root not found: $appRootPath"
}

function Get-FolderSizeBytes([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    return (Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
}

$package = Get-Content (Join-Path $appRootPath "package.json") -Raw | ConvertFrom-Json
$extensionsRoot = Join-Path $appRootPath "extensions"
$contribRoot = Join-Path $appRootPath "out\vs\workbench\contrib"

$cursorExtensions = @()
if (Test-Path $extensionsRoot) {
    $cursorExtensions = Get-ChildItem $extensionsRoot -Directory |
        Where-Object { $_.Name -match '^(cursor-|anysphere)' } |
        ForEach-Object {
            $pkgPath = Join-Path $_.FullName "package.json"
            $extPkg = if (Test-Path $pkgPath) { Get-Content $pkgPath -Raw | ConvertFrom-Json } else { $null }
            [ordered]@{
                name = $_.Name
                publisher = $extPkg.publisher
                version = $extPkg.version
                main = $extPkg.main
                sizeBytes = Get-FolderSizeBytes $_.FullName
                inventoryNotes = switch -Regex ($_.Name) {
                    'cursor-mcp' { 'MCP-related extension bundle' }
                    'cursor-retrieval' { 'Retrieval/indexing-related extension bundle' }
                    'cursor-agent-exec' { 'Agent execution extension bundle' }
                    'cursor-commits' { 'SCM/commits extension bundle' }
                    'cursor-always-local' { 'Local routing extension bundle' }
                    default { 'Cursor-specific extension; inspect package.json and dist/ if needed' }
                }
            }
        }
}

$workbenchContrib = @()
if (Test-Path $contribRoot) {
    $workbenchContrib = Get-ChildItem $contribRoot -Directory | ForEach-Object {
        [ordered]@{
            name = $_.Name
            sizeBytes = Get-FolderSizeBytes $_.FullName
            inventoryNotes = switch ($_.Name) {
                'composer' { 'Cursor AI workbench contribution (compiled)' }
                'onboarding' { 'Onboarding workbench contribution (compiled)' }
                default { 'Workbench contribution folder (compiled)' }
            }
        }
    }
}

$manifest = [ordered]@{
    purpose = "Inventory only. User decisions for merging live in docs/merges/{version}/MERGE_REPORT.md"
    generatedAt = (Get-Date).ToString("o")
    source = [ordered]@{
        appRoot = $AppRoot
        cursorVersion = $package.version
        vscodeCommit = $package.distro
        vscodeVersion = (Get-Content (Join-Path $appRootPath "product.json") -Raw | ConvertFrom-Json).vscodeVersion
    }
    voidCodeHints = [ordered]@{
        note = "Reference paths only; not merge recommendations"
        workbench = "src/vs/workbench/contrib/void"
        product = "product.json"
        extensions = "extensions"
    }
    components = [ordered]@{
        productJson = [ordered]@{
            path = "product.json"
            sizeBytes = (Get-Item (Join-Path $appRootPath "product.json")).Length
            inventoryNotes = "Product configuration file"
        }
        compiledWorkbench = [ordered]@{
            path = "out/vs/workbench"
            sizeBytes = Get-FolderSizeBytes (Join-Path $appRootPath "out\vs\workbench")
            inventoryNotes = "Minified JS; reference only, do not copy into Void sources"
        }
        cursorExtensions = $cursorExtensions
        workbenchContrib = $workbenchContrib
        cliBinaries = [ordered]@{
            path = "bin"
            sizeBytes = Get-FolderSizeBytes (Join-Path $appRootPath "bin")
            inventoryNotes = "CLI and tunnel binaries"
        }
    }
}

New-Item -ItemType Directory -Force -Path (Split-Path $outputFile) | Out-Null
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $outputFile -Encoding UTF8
Write-Host "Wrote $outputFile"
