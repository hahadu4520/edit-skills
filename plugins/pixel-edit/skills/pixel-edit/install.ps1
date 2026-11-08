# 像素风剪辑技能一键安装（Windows 10/11）：powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
$Name = "pixel-edit"
if ($Src -like "*\skills\$Name") { $Dest = $Src } else { $Dest = Join-Path $HOME ".claude\skills\$Name" }

Write-Host "① 检查 ffmpeg、Python 和 Node.js …"
foreach ($p in @(@("ffmpeg","Gyan.FFmpeg"), @("python","Python.Python.3.12"), @("node","OpenJS.NodeJS.LTS"))) {
  if (-not (Get-Command $p[0] -ErrorAction SilentlyContinue)) {
    winget install -e --id $p[1] --accept-source-agreements --accept-package-agreements
  }
}
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

if ($Src -ne $Dest) {
  Write-Host "② 复制技能到 $Dest …"
  New-Item -ItemType Directory -Force -Path $Dest | Out-Null
  foreach ($f in @("SKILL.md","AGENTS.md","README.md","install.sh","install.ps1","check.sh","check.ps1","scripts","screenshots","fonts","examples")) { Copy-Item -Recurse -Force (Join-Path $Src $f) $Dest }
}

Write-Host "③ 创建独立的 Python 环境，安装 numpy、pillow、sherpa-onnx …"
python -m venv (Join-Path $Dest "venv")
$Pip = Join-Path $Dest "venv\Scripts\pip.exe"
& $Pip install -q --timeout 30 numpy pillow sherpa-onnx
if ($LASTEXITCODE -ne 0) { & $Pip install -q --timeout 60 -i https://pypi.tuna.tsinghua.edu.cn/simple numpy pillow sherpa-onnx }

Write-Host "④ 安装截图用的 Playwright …"
Push-Location (Join-Path $Dest "screenshots")
try { npm init -y | Out-Null; npm install --silent playwright; npx playwright install chromium } catch { Write-Host "⚠️  Playwright 安装失败，用到对话截图时再装。" }
Pop-Location

Write-Host "⑤ 让 Claude Code、Codex 和其他 Agent 都能找到这个技能 …"
$Dirs = @(".claude\skills", ".codex\skills", ".agents\skills")
if ($Dest -like "*\.claude\plugins\*") { $Dirs = $Dirs[1..2] }  # 通过插件市场安装时 Claude Code 已能找到
foreach ($d in $Dirs) {
  $dir = Join-Path $HOME $d; New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $link = Join-Path $dir $Name
  if (($link -ne $Dest) -and -not (Test-Path $link)) { New-Item -ItemType Junction -Path $link -Target $Dest | Out-Null; Write-Host "   已链接 $link" }
}
Write-Host "✅ 安装完成。打开 Claude Code 或 Codex，说「用像素风剪辑 <你的原片路径>」就可以开始了。"
