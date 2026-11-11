#!/bin/bash
# 依赖自检（1 秒内跑完，只检查不安装）：bash check.sh
# 全部就绪：输出 OK、退出码 0。缺东西：列出缺什么、退出码 1。
# --hook：给 Claude Code 插件的 SessionStart 钩子用，就绪时什么都不输出，永远返回 0。
D="$(cd "$(dirname "$0")" && pwd)"
MODS="PIL numpy cv2 mediapipe"
MISS=""
command -v ffmpeg >/dev/null 2>&1 || MISS="$MISS ffmpeg"
PY="$D/venv/bin/python"; [ -x "$PY" ] || PY="$D/venv/Scripts/python.exe"
if [ -x "$PY" ]; then
  for m in $MODS; do "$PY" -c "import $m" >/dev/null 2>&1 || MISS="$MISS python:$m"; done
else MISS="$MISS venv(技能自带的 Python 环境)"; fi
if [ -z "$MISS" ]; then [ "$1" = "--hook" ] || echo "OK：vlog 卡点剪辑的依赖都装好了"; exit 0; fi
if [ "$1" = "--hook" ]; then
  echo "[vlog 卡点剪辑] 依赖还没装好（缺：$MISS）。用户要剪 vlog 卡点开头时，先直接运行 bash \"$D/install.sh\"（Windows：powershell -ExecutionPolicy Bypass -File \"$D/install.ps1\"）装好，再开始；安装约 3–5 分钟，开始前告诉用户一声。"
  exit 0
fi
echo "缺少：$MISS"; echo "运行 bash \"$D/install.sh\" 安装（Windows：install.ps1）"; exit 1
