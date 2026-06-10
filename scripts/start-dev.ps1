# Start Void Developer Mode: npm run watch + launch Void in one command.
#
# Usage (from repo root or scripts/):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\scripts\start-dev.ps1
#
# Options:
#   -SkipBuildReact     Skip npm run buildreact
#   -SkipNativeCheck    Skip native .node module verification
#   -WatchOnly          Start watch only; do not launch Void
#   -LaunchOnly         Launch Void only (watch must already be running with 0 errors)
#   -CompileTimeoutSec  Max wait for first clean compile (default 900)

[CmdletBinding()]
param(
    [switch]$SkipBuildReact,
    [switch]$SkipNativeCheck,
    [switch]$WatchOnly,
    [switch]$LaunchOnly,
    [int]$CompileTimeoutSec = 900
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot 'lib\Get-ProductInfo.ps1')
$Product = Get-ProductInfo -RepoRoot $RepoRoot

$UserDataDir = Join-Path $RepoRoot '.tmp/user-data'
$ExtensionsDir = Join-Path $RepoRoot '.tmp/extensions'
$WatchLogFile = Join-Path $env:TEMP 'void-dev-watch.log'
$ElectronExe = $Product.ElectronPath
$MainJs = Join-Path $RepoRoot 'out/main.js'
$script:WatchStartedAt = $null

$NativeModules = @(
    '@vscode/policy-watcher',
    '@vscode/windows-mutex',
    '@vscode/spdlog',
    '@vscode/sqlite3',
    '@vscode/windows-registry',
    'native-keymap',
    'native-watchdog',
    '@parcel/watcher',
    'node-pty'
)

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Initialize-VoidDevEnvironment {
    $requiredNode = (Get-Content (Join-Path $RepoRoot '.nvmrc') -Raw).Trim()
    $nvmHome = $env:NVM_HOME
    if (-not $nvmHome) {
        $nvmHome = Join-Path $env:LOCALAPPDATA 'nvm'
    }
    $nvmExe = Join-Path $nvmHome 'nvm.exe'

    if (Test-Path $nvmExe) {
        & $nvmExe use $requiredNode | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Step "Installing Node $requiredNode via nvm..."
            & $nvmExe install $requiredNode
            & $nvmExe use $requiredNode
        }
    }

    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $gitCmd = 'C:\Program Files\Git\cmd'
    $nvmSymlink = if ($env:NVM_SYMLINK) { $env:NVM_SYMLINK } else { 'C:\nvm4w\nodejs' }
    $env:Path = "$nvmSymlink;$nvmHome;$gitCmd;$machinePath"

    $nodeVersion = (node -v)
    Write-Host "Node: $nodeVersion (recommended: v$requiredNode)" -ForegroundColor DarkGray

    $env:NODE_OPTIONS = '--max-old-space-size=8192'
}

function Test-NativeModuleBuilt([string]$PackageName) {
    $modulePath = Join-Path $RepoRoot "node_modules/$PackageName"
    if (-not (Test-Path $modulePath)) { return $false }
    $nodes = Get-ChildItem -Path $modulePath -Recurse -Filter '*.node' -ErrorAction SilentlyContinue
    return ($null -ne $nodes -and $nodes.Count -gt 0)
}

function Ensure-NativeModules {
    $missing = @($NativeModules | Where-Object { -not (Test-NativeModuleBuilt $_) })
    if ($missing.Count -eq 0) {
        Write-Host 'Native modules: OK' -ForegroundColor DarkGray
        return
    }

    Write-Step "Missing native modules: $($missing -join ', ')"
    Write-Host 'Approving npm install scripts and rebuilding (npm 11 requirement)...' -ForegroundColor Yellow

    npm approve-scripts --all 2>&1 | Out-Null

    $vcvars = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path $vcvars)) {
        Write-Host "Cannot rebuild natives: VS Build Tools not found at $vcvars" -ForegroundColor Red
        Write-Host 'Run scripts/install-windows-build-prereqs.ps1 or see docs/BUILD.md' -ForegroundColor Yellow
        exit 1
    }

    $rebuildList = ($NativeModules -join ' ')
    $nvmSymlink = if ($env:NVM_SYMLINK) { $env:NVM_SYMLINK } else { 'C:\nvm4w\nodejs' }
    $nvmHomeLocal = if ($env:NVM_HOME) { $env:NVM_HOME } else { Join-Path $env:LOCALAPPDATA 'nvm' }
    $pathPrefix = "$nvmSymlink;$nvmHomeLocal;C:\Program Files\Git\cmd;"

    $cmd = "`"$vcvars`" && set `"PATH=$pathPrefix%PATH%`" && set `"WindowsSdkDir=C:\Program Files (x86)\Windows Kits\10\`" && set WindowsSDKVersion=10.0.22621.0\ && cd /d `"$RepoRoot`" && npm rebuild $rebuildList"
    cmd /c $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Native module rebuild failed. See docs/BUILD.md' -ForegroundColor Red
        exit $LASTEXITCODE
    }

    $stillMissing = @($NativeModules | Where-Object { -not (Test-NativeModuleBuilt $_) })
    if ($stillMissing.Count -gt 0) {
        Write-Host "Still missing after rebuild: $($stillMissing -join ', ')" -ForegroundColor Red
        exit 1
    }
    Write-Host 'Native modules rebuilt successfully.' -ForegroundColor Green
}

function Ensure-Electron {
    if (Test-Path $ElectronExe) {
        Write-Host "Electron dev binary: OK" -ForegroundColor DarkGray
        return
    }
    Write-Step 'Downloading dev Electron (npm run electron)...'
    npm run electron
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $ElectronExe)) {
        Write-Host "Failed to prepare $ElectronExe" -ForegroundColor Red
        exit 1
    }
}

function Start-WatchProcess {
    if (Test-Path $WatchLogFile) {
        Remove-Item $WatchLogFile -Force -ErrorAction SilentlyContinue
    }

    $watchCommand = @"
Set-Location '$RepoRoot'
`$Host.UI.RawUI.WindowTitle = 'Void Dev Watch'
`$env:NVM_HOME = '$($env:NVM_HOME -replace "'","''")'
`$env:NVM_SYMLINK = '$($env:NVM_SYMLINK -replace "'","''")'
`$env:Path = '$($env:Path -replace "'","''")'
`$env:NODE_OPTIONS = '--max-old-space-size=8192'
Write-Host 'Void watch - leave this window open. Close to stop the dev compiler.' -ForegroundColor Cyan
npm run watch 2>&1 | Tee-Object -FilePath '$WatchLogFile'
"@

    Write-Step 'Starting npm run watch in a new terminal...'
    $script:WatchStartedAt = Get-Date
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-Command', $watchCommand
    ) | Out-Null

    Start-Sleep -Seconds 2
}

function Remove-AnsiEscapeCodes([string]$Text) {
    if ([string]::IsNullOrEmpty($Text)) { return $Text }
    return [regex]::Replace($Text, '\x1b\[[0-9;]*m', '')
}

function Read-WatchLogTail([string]$Path, [int]$TailLines = 200) {
    if (-not (Test-Path $Path)) { return '' }
    try {
        # Tee-Object keeps the file open; shared read avoids empty reads on Windows.
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $reader = New-Object System.IO.StreamReader($stream)
            $lines = [System.Collections.Generic.List[string]]::new()
            while ($null -ne ($line = $reader.ReadLine())) {
                $lines.Add($line)
            }
            if ($lines.Count -eq 0) { return '' }
            $start = [Math]::Max(0, $lines.Count - $TailLines)
            return ($lines.GetRange($start, $lines.Count - $start) -join "`n")
        } finally {
            $reader.Dispose()
            $stream.Dispose()
        }
    } catch {
        return (Get-Content $Path -Tail $TailLines -ErrorAction SilentlyContinue) -join "`n"
    }
}

function Test-WatchExtensionsReady([string]$Log) {
    # Ignore the quick partial compile (~1s); full pass takes tens of seconds.
    return $Log -match '\[watch-extensions\s*\][^\r\n]*Finished compilation extensions with 0 errors after [0-9]{5,}'
}

function Test-WatchClientReady([string]$Log) {
    if ($script:WatchStartedAt -and (Test-Path $MainJs)) {
        $main = Get-Item $MainJs
        if ($main.LastWriteTime -ge $script:WatchStartedAt.AddSeconds(-15)) {
            return $true
        }
    }

    foreach ($match in [regex]::Matches($Log, '\[watch-client\s*\][^\r\n]*Finished compilation[^\r\n]*with 0 errors')) {
        if ($match.Value -notmatch 'api-proposal-names') {
            return $true
        }
    }
    return $false
}

function Wait-ForCleanCompile {
    Write-Step "Waiting for clean compile (timeout ${CompileTimeoutSec}s)..."
    Write-Host 'First watch-client compile usually takes about 2 minutes.' -ForegroundColor DarkGray

    $clientOk = $false
    $extensionsOk = $false
    $deadline = (Get-Date).AddSeconds($CompileTimeoutSec)
    $lastProgress = Get-Date

    while ((Get-Date) -lt $deadline) {
        $log = Remove-AnsiEscapeCodes (Read-WatchLogTail $WatchLogFile 400)

        if (-not $extensionsOk -and (Test-WatchExtensionsReady $log)) {
            $extensionsOk = $true
            Write-Host '  watch-extensions: 0 errors' -ForegroundColor Green
        }

        if (-not $clientOk -and (Test-WatchClientReady $log)) {
            $clientOk = $true
            if (Test-Path $MainJs) {
                Write-Host '  watch-client: 0 errors (out/main.js ready)' -ForegroundColor Green
            } else {
                Write-Host '  watch-client: 0 errors' -ForegroundColor Green
            }
        }

        if ($clientOk -and $extensionsOk) {
            return
        }

        if ($log -match 'Finished compilation[^\r\n]* with [1-9]\d* errors') {
            Write-Host 'Compilation reported errors - check the Void Dev Watch window.' -ForegroundColor Red
            exit 1
        }

        if (((Get-Date) - $lastProgress).TotalSeconds -ge 15) {
            if (-not $extensionsOk) {
                Write-Host '  still compiling extensions...' -ForegroundColor DarkGray
            } else {
                Write-Host '  extensions done; waiting for watch-client (~2 min first compile)...' -ForegroundColor DarkGray
            }
            $lastProgress = Get-Date
        }
        Start-Sleep -Seconds 2
    }

    Write-Host 'Timed out waiting for compile. Check Void Dev Watch window and log:' -ForegroundColor Red
    Write-Host "  $WatchLogFile" -ForegroundColor Yellow
    exit 1
}

function Start-VoidApp {
    Write-Step 'Launching Void Developer Mode...'
    New-Item -ItemType Directory -Force -Path $UserDataDir, $ExtensionsDir | Out-Null

    $codeBat = Join-Path $RepoRoot 'scripts/code.bat'
    $args = @(
        '--user-data-dir', $UserDataDir,
        '--extensions-dir', $ExtensionsDir
    )

    & $codeBat @args
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Void exited with code $LASTEXITCODE" -ForegroundColor Yellow
    }
}

# --- Main ---

Write-Host ''
Write-Host "$($Product.NameLong) Developer Mode launcher" -ForegroundColor Green
Write-Host "Repo: $RepoRoot" -ForegroundColor DarkGray

Initialize-VoidDevEnvironment

if (-not (Test-Path 'node_modules')) {
    Write-Step 'Running npm install (first time)...'
    npm install
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not $SkipNativeCheck) {
    Ensure-NativeModules
}

Ensure-Electron

if (-not $LaunchOnly) {
    if (-not $SkipBuildReact) {
        Write-Step 'Building Void React UI (npm run buildreact)...'
        npm run buildreact
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    Start-WatchProcess
    Wait-ForCleanCompile
}

if ($WatchOnly) {
    Write-Host "`nWatch is running. Launch Void later with:" -ForegroundColor Green
    Write-Host "  .\scripts\start-dev.ps1 -LaunchOnly" -ForegroundColor White
    exit 0
}

if ($LaunchOnly) {
    if (-not (Test-Path $MainJs)) {
        Write-Host "Missing $MainJs - run without -LaunchOnly first." -ForegroundColor Red
        exit 1
    }
}

Start-VoidApp

Write-Host ''
Write-Host 'Dev tips:' -ForegroundColor Green
Write-Host '  - Keep the Void Dev Watch terminal open while developing'
Write-Host '  - Press Ctrl+R inside Void to reload after code changes'
Write-Host '  - Log: ' -NoNewline; Write-Host $WatchLogFile -ForegroundColor DarkGray
Write-Host ''
