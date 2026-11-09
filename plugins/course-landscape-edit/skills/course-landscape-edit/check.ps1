# 依赖自检（Windows）：powershell -ExecutionPolicy Bypass -File check.ps1
$D = Split-Path -Parent $MyInvocation.MyCommand.Path
$Miss = @()
foreach ($c in @("ffmpeg","node")) { if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { $Miss += $c } }
$Py = Join-Path $D "venv\Scripts\python.exe"
$Mods = @("numpy", "PIL", "cv2")
if (Test-Path $Py) { foreach ($m in $Mods) { & $Py -c "import $m" 2>$null; if ($LASTEXITCODE -ne 0) { $Miss += "python:$m" } } } else { $Miss += "venv" }
if (-not (Test-Path (Join-Path $D "node_modules\playwright"))) { $Miss += "playwright" }
if (-not (Test-Path (Join-Path $D "node_modules\misans"))) { $Miss += "misans字体" }
if ($Miss.Count -eq 0) { Write-Host "OK：横版课程剪辑的依赖都装好了"; exit 0 }
Write-Host ("缺少：" + ($Miss -join " ")); Write-Host "运行 powershell -ExecutionPolicy Bypass -File `"$D\install.ps1`" 安装"; exit 1
