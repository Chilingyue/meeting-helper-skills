# Install both skills into an Agent skills directory.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install.ps1
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Dest "$env:USERPROFILE\.claude\skills"
#
# Default target: %USERPROFILE%\.workbuddy\skills
# An existing skill with the same name is renamed to <name>.bak-<timestamp> first,
# so nothing is silently overwritten.
#
# This file is intentionally ASCII-only: Windows PowerShell 5.1 reads .ps1 files
# using the system ANSI codepage, so non-ASCII text would show up garbled unless
# the file carries a UTF-8 BOM.

param(
    [string]$Dest = "$env:USERPROFILE\.workbuddy\skills"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root "skills"

if (-not (Test-Path $src)) {
    throw "skills directory not found: $src"
}
if (-not (Test-Path $Dest)) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    Write-Host "created target directory: $Dest"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$installed = 0

Get-ChildItem -Path $src -Directory | ForEach-Object {
    $name = $_.Name
    $target = Join-Path $Dest $name

    if (Test-Path $target) {
        $backup = "$target.bak-$stamp"
        Move-Item -Path $target -Destination $backup
        Write-Host "backed up previous version -> $backup"
    }

    Copy-Item -Path $_.FullName -Destination $target -Recurse
    $count = (Get-ChildItem -Path $target -Recurse -File).Count
    Write-Host "installed $name -> $target ($count files)"
    $installed++
}

Write-Host ""
Write-Host "done: $installed skill(s) installed." -ForegroundColor Green
Write-Host "Restart your Agent client, then ask it to send a WeChat message or join a meeting."
Write-Host "Note: scripts only need the Python standard library; cvfind.py additionally needs opencv-python-headless + numpy."
