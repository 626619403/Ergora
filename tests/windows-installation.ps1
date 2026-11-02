#Requires -Version 5.1
# Real installer acceptance on a disposable Windows runner; no agent/model calls.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$root = Join-Path ([IO.Path]::GetTempPath()) ('ergora-install-' + [guid]::NewGuid().ToString('N'))
$installRoot = Join-Path $root ('application with spaces ' + [char]0x9879 + [char]0x76EE)
$binDir = Join-Path $root 'commands with spaces'
$python = (Get-Command python.exe).Source
$installer = Join-Path $projectRoot 'scripts\install.ps1'
$entry = Join-Path $binDir 'ergora.exe'
$shellProfile = $PROFILE
$data = Join-Path $root 'persistent data'
$invalidRoot = Join-Path $root 'invalid profile'
try {
    $refused = $false
    try { & $installer -Profile 'unknown-profile' -InstallRoot $invalidRoot }
    catch {
        if ($_.Exception.Message -notmatch 'Unknown installation profile') { throw }
        $refused = $true
    }
    if (-not $refused -or (Test-Path -LiteralPath $invalidRoot)) { throw 'Unknown profile created installation files' }
    [IO.Directory]::CreateDirectory($data) | Out-Null
    $sentinel = Join-Path $data 'keep.txt'
    [IO.File]::WriteAllText($sentinel, 'persistent project data')
    for ($iteration = 0; $iteration -lt 3; $iteration++) {
        $selectedProfile = @('control', 'research', 'research')[$iteration]
        & $installer -Python $python -InstallRoot $installRoot -BinDir $binDir -Profile $selectedProfile `
            -WithGepa:($iteration -eq 2) -WithTemporal:($iteration -eq 2)
        & $entry --version
        if ($LASTEXITCODE -ne 0) { throw 'Installed launcher failed' }
        & $entry reference verify
        if ($LASTEXITCODE -ne 0) { throw 'Frozen reference identity failed' }
        $uncreated = Join-Path $root 'unused home'
        $recipes = (& $entry --home $uncreated tools profiles | Out-String) | ConvertFrom-Json
        if ($LASTEXITCODE -ne 0 -or $recipes.default -ne 'control' -or (Test-Path -LiteralPath $uncreated)) { throw 'Profile discovery failed or created state' }
        if ($iteration -gt 0) {
            $venvPython = Join-Path $installRoot 'venv\Scripts\python.exe'
            & $venvPython -c 'import importlib.metadata as m,sys;print(m.version(sys.argv[1]));print(m.version(sys.argv[2]))' gepa temporalio
            if ($LASTEXITCODE -ne 0) { throw 'Research profile SDKs were not installed' }
        }
        if ($PROFILE -cne $shellProfile -or [IO.File]::ReadAllText($sentinel) -ne 'persistent project data') { throw 'Installer changed shell profile or project data' }
    }
    $foreign = "@echo foreign application`r`n"
    [IO.File]::WriteAllText($entry, $foreign)
    $refused = $false
    try { & $installer -Python $python -InstallRoot $installRoot -BinDir $binDir }
    catch {
        if ($_.Exception.Message -notmatch 'belongs to another installation') { throw }
        $refused = $true
    }
    if (-not $refused -or [IO.File]::ReadAllText($entry) -ne $foreign) { throw 'Foreign launcher was not preserved' }
    Write-Host 'Windows profiles, SDK upgrade, repeated install, spaces, data, and foreign-entry protection: PASS'
}
finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
