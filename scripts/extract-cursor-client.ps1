# Extract Cursor Windows client components for local inventory (no merge decisions).
# Usage:
#   .\scripts\extract-cursor-client.ps1
#   .\scripts\extract-cursor-client.ps1 -InstallerPath "cursor\CursorSetup-x64-3.7.21.exe"
#   .\scripts\extract-cursor-client.ps1 -Version 3.7.21 -InstallerPath "cursor\CursorSetup-x64-3.7.21.exe"

param(
    [string]$Version = "",
    [string]$InstallerPath = "cursor\CursorSetup-x64-3.7.21.exe",
    [string]$OutputRoot = "",
    [switch]$FromInstalled,
    [string]$InstalledPath = "${env:ProgramFiles}\cursor",
    [switch]$SkipVersionCheck
)

if ($Version -and -not $OutputRoot) {
    $OutputRoot = "cursor\extracted\$Version"
}
elseif (-not $OutputRoot) {
    $OutputRoot = "cursor\extracted"
}

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$RequiredAppPaths = @(
    "package.json",
    "product.json",
    "out\main.js",
    "extensions\cursor-mcp"
)

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-ExtractedVersion([string]$AppRoot, [string]$ExpectedVersion) {
    if ($SkipVersionCheck -or -not $ExpectedVersion) {
        return
    }

    $packageJson = Join-Path $AppRoot "package.json"
    if (-not (Test-Path $packageJson)) {
        throw "Missing package.json at $AppRoot"
    }

    $pkg = Get-Content $packageJson -Raw | ConvertFrom-Json
    if ($pkg.version -ne $ExpectedVersion) {
        throw @"
Version mismatch: expected Cursor $ExpectedVersion but extracted $($pkg.version).
Close all Cursor windows and re-run extraction, or use -FromInstalled after updating the installed client.
"@
    }
    Write-Host "Version check passed: $($pkg.version)" -ForegroundColor Green
}

function Test-ExtractionLayout([string]$AppRoot, [string]$InstallDir) {
    Write-Step "Validating extraction layout"

    foreach ($relativePath in $RequiredAppPaths) {
        $fullPath = Join-Path $AppRoot $relativePath
        if (-not (Test-Path $fullPath)) {
            throw "Required path missing: $relativePath (expected at $fullPath)"
        }
    }

    if ($InstallDir) {
        $cursorExe = Join-Path $InstallDir "Cursor.exe"
        if (-not (Test-Path $cursorExe)) {
            throw "Full client shell missing: $cursorExe (installed-client was not preserved)"
        }
        Write-Host "Full client shell: $cursorExe" -ForegroundColor DarkGray
    }

    Write-Host "Layout validation passed." -ForegroundColor Green
}

function Copy-AppResources([string]$SourceApp, [string]$DestinationApp, [string]$Label) {
    if (-not (Test-Path $SourceApp)) {
        throw "App path not found: $SourceApp"
    }

    Write-Step "Copying app resources ($Label)"
    New-Item -ItemType Directory -Force -Path $DestinationApp | Out-Null
    robocopy $SourceApp $DestinationApp /E /NFL /NDL /NJH /NJS /nc /ns /np /XD node_modules | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }

    $packageJson = Join-Path $DestinationApp "package.json"
    if (Test-Path $packageJson) {
        $pkg = Get-Content $packageJson -Raw | ConvertFrom-Json
        Write-Host "Extracted Cursor app version: $($pkg.version)"
        Write-Host "VS Code commit (distro): $($pkg.distro)"
    }
}

function Install-FromExe([string]$ExePath, [string]$InstallDir) {
    if (-not (Test-Path $ExePath)) {
        throw "Installer not found: $ExePath"
    }

    $running = Get-Process -Name "Cursor" -ErrorAction SilentlyContinue
    if ($running) {
        throw @"
Cursor is currently running. Close all Cursor windows and retry.
The installer aborts silently when Cursor is open.
"@
    }

    Write-Step "Running silent installer to $InstallDir"
    $logPath = Join-Path $OutputRoot "install.log"
    New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

    if (Test-Path $InstallDir) {
        Write-Host "Removing previous installed-client at $InstallDir" -ForegroundColor DarkGray
        Remove-Item -Recurse -Force $InstallDir
    }

    $args = @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/CLOSEAPPLICATIONS",
        "/DIR=$InstallDir",
        "/LOG=$logPath"
    )

    $proc = Start-Process -FilePath (Resolve-Path $ExePath) -ArgumentList $args -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "Installer failed with exit code $($proc.ExitCode). See $logPath"
    }

    $appPath = Join-Path $InstallDir "resources\app"
    if (-not (Test-Path $appPath)) {
        throw "Installer completed but app resources missing at $appPath. Review $logPath"
    }

    return $appPath
}

Write-Step "Cursor client extraction"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$installDir = $null

if ($FromInstalled) {
    $localInstallDir = Join-Path $OutputRoot "installed-client"
    $sourceApp = Join-Path $InstalledPath "resources\app"

    if (-not (Test-Path (Join-Path $InstalledPath "Cursor.exe"))) {
        throw "Installed Cursor not found at $InstalledPath"
    }

    Write-Step "Copying full installed client to $localInstallDir"
    if (Test-Path $localInstallDir) {
        Remove-Item -Recurse -Force $localInstallDir
    }
    New-Item -ItemType Directory -Force -Path $localInstallDir | Out-Null
    robocopy $InstalledPath $localInstallDir /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed copying installed client with exit code $LASTEXITCODE"
    }

    $installDir = $localInstallDir
    $destApp = Join-Path $OutputRoot "app-resources"
    Copy-AppResources -SourceApp $sourceApp -DestinationApp $destApp -Label "installed copy"
}
else {
    $installDir = Join-Path $OutputRoot "installed-client"
    $sourceApp = Install-FromExe -ExePath $InstallerPath -InstallDir $installDir
    $destApp = Join-Path $OutputRoot "app-resources"
    Copy-AppResources -SourceApp $sourceApp -DestinationApp $destApp -Label "installer"
}

Test-ExtractedVersion -AppRoot $destApp -ExpectedVersion $Version
Test-ExtractionLayout -AppRoot $destApp -InstallDir $installDir

Write-Step "Generating component manifest"
& (Join-Path $PSScriptRoot "generate-cursor-manifest.ps1") -AppRoot $destApp -OutputPath (Join-Path $OutputRoot "COMPONENT_MANIFEST.json")

Write-Step "Done"
Write-Host "Installed client: $installDir"
Write-Host "App resources: $destApp"
Write-Host "Manifest: $(Join-Path $OutputRoot 'COMPONENT_MANIFEST.json')"
