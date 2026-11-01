# 把 skills\* 安装到本机 Agent 的技能目录。
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File install.ps1
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Dest "$env:USERPROFILE\.claude\skills"
#
# 默认目标：%USERPROFILE%\.workbuddy\skills
# 已存在的同名技能会先备份成 <名字>.bak-<时间戳>，不会直接覆盖。

param(
    [string]$Dest = "$env:USERPROFILE\.workbuddy\skills"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root "skills"

if (-not (Test-Path $src)) {
    Write-Error "找不到 skills 目录：$src"
}
if (-not (Test-Path $Dest)) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    Write-Host "已创建目标目录：$Dest"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Get-ChildItem -Path $src -Directory | ForEach-Object {
    $name = $_.Name
    $target = Join-Path $Dest $name

    if (Test-Path $target) {
        $backup = "$target.bak-$stamp"
        Move-Item -Path $target -Destination $backup
        Write-Host "已备份旧版本 -> $backup"
    }

    Copy-Item -Path $_.FullName -Destination $target -Recurse
    $files = (Get-ChildItem -Path $target -Recurse -File).Count
    Write-Host ("已安装 {0} -> {1}（{2} 个文件）" -f $name, $target, $files)
}

Write-Host ""
Write-Host "完成。重启 Agent 客户端后，说一句「在某个微信群发条消息」即可触发。" -ForegroundColor Green
Write-Host "提示：脚本只依赖 Python 标准库；模板匹配（cvfind.py）额外需要 opencv-python-headless numpy。"
