# vlog 卡点剪辑技能一键安装（Windows）
# 用法：在 PowerShell 里运行
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Name = "vlog-beat-edit"
$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Src -like "*\skills\$Name") { $Dest = $Src } else { $Dest = Join-Path $HOME ".claude\skills\$Name" }

Write-Host "① 检查 ffmpeg 和 Python …"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    } else { Write-Host "❌ 请先安装 ffmpeg：https://www.gyan.dev/ffmpeg/builds/ ，并把 bin 目录加到 PATH"; exit 1 }
}
$Py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $Py -or (& python --version 2>&1) -notmatch "Python 3") {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    } else { Write-Host "❌ 请先安装 Python 3.10+：https://www.python.org/downloads/ （安装时勾选 Add to PATH）"; exit 1 }
}

if ($Src -ne $Dest) {
    Write-Host "② 复制技能到 $Dest …"
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    foreach ($f in "SKILL.md","AGENTS.md","README.md","install.sh","install.ps1","check.sh","check.ps1","scripts","fonts","examples") {
        Copy-Item -Recurse -Force (Join-Path $Src $f) $Dest
    }
}

Write-Host "③ 创建独立的 Python 环境，安装 pillow、numpy、opencv、mediapipe …"
python -m venv (Join-Path $Dest "venv")
$VPy = Join-Path $Dest "venv\Scripts\python.exe"
& $VPy -m pip install -q --timeout 30 pillow numpy opencv-python-headless mediapipe
if ($LASTEXITCODE -ne 0) {
    & $VPy -m pip install -q --timeout 60 -i https://pypi.tuna.tsinghua.edu.cn/simple pillow numpy opencv-python-headless mediapipe
}

Write-Host "④ 让 Claude Code、Codex 和其他 Agent 都能找到这个技能 …"
$Dirs = @((Join-Path $HOME ".claude\skills"), (Join-Path $HOME ".codex\skills"), (Join-Path $HOME ".agents\skills"))
if ($Dest -like "*\.claude\plugins\*") { $Dirs = $Dirs[1..2] }
foreach ($d in $Dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    $link = Join-Path $d $Name
    if ($link -ne $Dest -and -not (Test-Path $link)) {
        New-Item -ItemType Junction -Path $link -Target $Dest | Out-Null
        Write-Host "   已链接 $link"
    }
}

Write-Host "⑤ 自检 …"
& $VPy -c "import PIL, numpy, cv2, mediapipe"
if ($LASTEXITCODE -eq 0 -and (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "✅ 安装完成。打开 Claude Code 或 Codex，说“剪一个 vlog 卡点开头，素材在 C:\Users\你\Videos\xxx”就能开始。"
} else { Write-Host "❌ 自检没通过，请把上面的报错截图发给技能作者。" }
