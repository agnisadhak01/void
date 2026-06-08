# Installs Windows prerequisites for building Void from source.
# Requires: winget, Administrator PowerShell (Run as Administrator).
#
# Usage:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\scripts\install-windows-build-prereqs.ps1

$ErrorActionPreference = 'Stop'

Write-Host "=== Void Windows build prerequisites ===" -ForegroundColor Cyan

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Re-launching elevated (UAC prompt)..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', $MyInvocation.MyCommand.Path
    )
    exit
}

# Visual Studio 2022 Build Tools + C++ desktop + Node build tools + Spectre libs (per HOW_TO_CONTRIBUTE.md)
$vsOverride = @(
    '--wait', '--passive', '--norestart',
    '--add', 'Microsoft.VisualStudio.Workload.NativeDesktop',
    '--add', 'Microsoft.VisualStudio.Component.Node.jsBuild',
    '--add', 'Microsoft.VisualStudio.Component.VC.Runtimes.x86.x64.Spectre',
    '--add', 'Microsoft.VisualStudio.Component.VC.ATL.Spectre.x86.x64',
    '--add', 'Microsoft.VisualStudio.Component.VC.MFC.Spectre.x86.x64',
    '--includeRecommended'
) -join ' '

Write-Host "`n[1/2] Installing Visual Studio 2022 Build Tools (15-45 min)..." -ForegroundColor Green
winget install --id Microsoft.VisualStudio.2022.BuildTools `
    --accept-package-agreements --accept-source-agreements `
    --override $vsOverride

Write-Host "`n[2/2] Installing NVM for Windows (optional Node version manager)..." -ForegroundColor Green
winget install --id CoreyButler.NVMforWindows `
    --accept-package-agreements --accept-source-agreements

Write-Host @"

=== Next steps (new terminal after NVM install) ===

  cd X:\Void
  nvm install 20.18.2
  nvm use 20.18.2
  node -v    # should print v20.18.2

  npm install
  `$env:NODE_OPTIONS='--max-old-space-size=8192'; npm run buildreact
  npm run compile
  npm run gulp vscode-win32-x64

Output: X:\VSCode-win32-x64\Void.exe

"@ -ForegroundColor Cyan
