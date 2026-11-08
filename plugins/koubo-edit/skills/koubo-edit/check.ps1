# 依赖自检（Windows）：powershell -ExecutionPolicy Bypass -File check.ps1
$D = Split-Path -Parent $MyInvocation.MyCommand.Path
$Miss = @()
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { $Miss += "ffmpeg" }
$Py = Join-Path $D "venv\Scripts\python.exe"
$Mods = @("PIL", "jieba", "faster_whisper")
if (Test-Path $Py) { foreach ($m in $Mods) { & $Py -c "import $m" 2>$null; if ($LASTEXITCODE -ne 0) { $Miss += "python:$m" } } } else { $Miss += "venv" }
if ($Miss.Count -eq 0) { Write-Host "OK：朴素版口播的依赖都装好了"; exit 0 }
Write-Host ("缺少：" + ($Miss -join " ")); Write-Host "运行 powershell -ExecutionPolicy Bypass -File `"$D\install.ps1`" 安装"; exit 1
