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
    [string]$InstalledPath = "${env:ProgramFiles}\cursor"
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

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
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

    Write-Step "Running silent installer"
    $logPath = Join-Path $OutputRoot "install.log"
    New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

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

    return Join-Path $InstallDir "resources\app"
}

Write-Step "Cursor client extraction"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

if ($FromInstalled) {
    $sourceApp = Join-Path $InstalledPath "resources\app"
    $destApp = Join-Path $OutputRoot "app-resources"
    Copy-AppResources -SourceApp $sourceApp -DestinationApp $destApp -Label "installed copy"
}
else {
    $installDir = Join-Path $OutputRoot "installed-client"
    $sourceApp = Install-FromExe -ExePath $InstallerPath -InstallDir $installDir
    $destApp = Join-Path $OutputRoot "app-resources"
    Copy-AppResources -SourceApp $sourceApp -DestinationApp $destApp -Label "installer"
}

Write-Step "Generating component manifest"
& (Join-Path $PSScriptRoot "generate-cursor-manifest.ps1") -AppRoot $destApp -OutputPath (Join-Path $OutputRoot "COMPONENT_MANIFEST.json")

Write-Step "Done"
Write-Host "App resources: $destApp"
Write-Host "Manifest: $(Join-Path $OutputRoot 'COMPONENT_MANIFEST.json')"
