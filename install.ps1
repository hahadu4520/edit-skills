# 不用 Claude Code 插件市场时的安装方式（Windows）：
#   powershell -ExecutionPolicy Bypass -File install.ps1 <风格名>
param([string]$Name)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Name) { Write-Host "可安装的剪辑风格："; Get-ChildItem (Join-Path $Root "plugins") -Name; Write-Host "用法：install.ps1 <风格名>"; exit 0 }
$D = Join-Path $Root "plugins\$Name\skills\$Name"
if (-not (Test-Path $D)) { Write-Host "❌ 没有这个风格：$Name"; exit 1 }
& powershell -ExecutionPolicy Bypass -File (Join-Path $D "install.ps1")
