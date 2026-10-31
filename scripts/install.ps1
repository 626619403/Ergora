#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Python = $env:ERGORA_PYTHON,
    [string]$InstallRoot = $env:ERGORA_INSTALL_ROOT,
    [string]$BinDir = $env:ERGORA_BIN_DIR,
    [switch]$WithGepa,
    [switch]$WithTemporal,
    [switch]$InstallPrerequisites,
    [switch]$AddToPath
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Use scripts/install.sh on Linux.' }

function Invoke-Checked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
}

function Find-Python {
    if ($Python) { return @{ executable = $Python; arguments = @() } }
    foreach ($candidate in @(@{ name = 'py.exe'; arguments = @('-3') }, @{ name = 'python.exe'; arguments = @() })) {
        $command = Get-Command $candidate.name -ErrorAction SilentlyContinue
        if ($command) {
            & $command.Source @($candidate.arguments) -c 'import sys;sys.exit(0 if sys.version_info >= (3,11) else 1)'
            if ($LASTEXITCODE -eq 0) { return @{ executable = $command.Source; arguments = $candidate.arguments } }
        }
    }
    return $null
}

$pythonSpec = Find-Python
if ($InstallPrerequisites) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Install App Installer (winget), or install Python 3.11+ and Git manually; see docs/WINDOWS.md.' }
    if (-not $pythonSpec) { Invoke-Checked $winget.Source @('install', '--exact', '--id', 'Python.Python.3.12', '--scope', 'user', '--accept-source-agreements', '--accept-package-agreements') }
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { Invoke-Checked $winget.Source @('install', '--exact', '--id', 'Git.Git', '--scope', 'user', '--accept-source-agreements', '--accept-package-agreements') }
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
    $pythonSpec = Find-Python
}

if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git is required. Install Git for Windows, then open a new terminal.' }
if (-not $pythonSpec) { throw 'Python 3.11+ is required. Use -InstallPrerequisites or install Python, then open a new terminal.' }
$Python = $pythonSpec.executable
$pythonArguments = @($pythonSpec.arguments)
& $Python @pythonArguments -c 'import sys;sys.exit(0 if sys.version_info >= (3,11) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
if (-not $InstallRoot) { $InstallRoot = Join-Path $env:LOCALAPPDATA 'Ergora\app' }
if (-not $BinDir) { $BinDir = Join-Path $env:LOCALAPPDATA 'Ergora\bin' }
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$BinDir = [IO.Path]::GetFullPath($BinDir)
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venv = Join-Path $InstallRoot 'venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
$entry = Join-Path $BinDir 'ergora.exe'
$ownerFile = Join-Path $BinDir 'ergora-install.json'
$nativeEntry = Join-Path $venv 'Scripts\ergora.exe'
if (Test-Path -LiteralPath $entry) {
    if (-not (Test-Path -LiteralPath $ownerFile)) { throw "Existing $entry belongs to another installation. Choose -BinDir." }
    $owner = [IO.File]::ReadAllText($ownerFile) | ConvertFrom-Json
    $entryHash = (Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash
    if ($owner.kind -ne 'ergora-windows-launcher-v1' -or $owner.python -ne $venvPython -or $owner.sha256 -ne $entryHash) {
        throw "Existing $entry belongs to another installation or was edited. Choose -BinDir."
    }
}
elseif (Test-Path -LiteralPath $ownerFile) { throw "An orphaned $ownerFile exists. Preserve it and choose -BinDir." }
foreach ($name in @('ergora.cmd', 'ergora.ps1', 'ergora.bat')) {
    if (Test-Path -LiteralPath (Join-Path $BinDir $name)) { throw "Existing $name would shadow the launcher. Choose -BinDir." }
}

[IO.Directory]::CreateDirectory($InstallRoot) | Out-Null
[IO.Directory]::CreateDirectory($BinDir) | Out-Null
Invoke-Checked $Python ($pythonArguments + @('-m', 'venv', $venv))
$extras = @('web')
if ($WithGepa) { $extras += 'gepa' }
if ($WithTemporal) { $extras += 'temporal' }
$requirement = $sourceRoot + '[' + ($extras -join ',') + ']'
Invoke-Checked $venvPython @('-X', 'utf8', '-m', 'pip', 'install', $requirement)
Invoke-Checked $venvPython @('-X', 'utf8', '-m', 'ergora', 'reference', 'verify')
Copy-Item -LiteralPath $nativeEntry -Destination $entry -Force
$owner = @{ kind = 'ergora-windows-launcher-v1'; python = $venvPython; sha256 = (Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash }
[IO.File]::WriteAllText($ownerFile, ($owner | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))

if ($AddToPath) {
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (-not $userPath) { $userPath = '' }
    if (($userPath -split ';') -notcontains $BinDir) {
        [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';') + ';' + $BinDir).TrimStart(';')), 'User')
    }
}
$env:Path = $BinDir + ';' + $env:Path
Write-Host "Installed: $entry"
Write-Host "Start console: & '$entry' serve"
Write-Host 'Open http://127.0.0.1:8977. No agents, services, or GPU jobs were started.'
