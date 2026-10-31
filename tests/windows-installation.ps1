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
try {
    for ($iteration = 0; $iteration -lt 2; $iteration++) {
        & $installer -Python $python -InstallRoot $installRoot -BinDir $binDir
        & $entry --version
        if ($LASTEXITCODE -ne 0) { throw 'Installed launcher failed' }
        & $entry reference verify
        if ($LASTEXITCODE -ne 0) { throw 'Frozen reference identity failed' }
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
    Write-Host 'Windows install, idempotent upgrade, spaces, and foreign-entry protection: PASS'
}
finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
