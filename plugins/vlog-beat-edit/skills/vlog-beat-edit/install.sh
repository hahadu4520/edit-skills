#!/bin/bash
# vlog 卡点剪辑技能一键安装（macOS / Linux）：bash install.sh
# Windows 请用 install.ps1
set -e
cd "$(dirname "$0")"
SRC="$(pwd)"
NAME="vlog-beat-edit"

case "$SRC" in
  */skills/$NAME) DEST="$SRC" ;;
  *) DEST="$HOME/.claude/skills/$NAME" ;;
esac

if [ "$(uname -s)" = "Darwin" ] && ! command -v brew >/dev/null 2>&1; then
  echo "❌ 没找到 Homebrew。先在终端运行下面这行装好，再重新运行本脚本："
  echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'; exit 1
fi

echo "① 检查 ffmpeg 和 Python …"
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install ffmpeg
  else echo "❌ 请先安装 ffmpeg（例如 sudo apt install ffmpeg）"; exit 1; fi
fi
if ! command -v python3 >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install python
  else echo "❌ 请先安装 Python 3.10 或更新版本"; exit 1; fi
fi

if [ "$SRC" != "$DEST" ]; then
  echo "② 复制技能到 $DEST …"
  mkdir -p "$DEST"
  cp -R SKILL.md AGENTS.md README.md install.sh install.ps1 check.sh check.ps1 scripts fonts examples "$DEST/"
fi

echo "③ 创建独立的 Python 环境，安装 pillow、numpy、opencv、mediapipe …"
python3 -m venv "$DEST/venv"
PIP="$DEST/venv/bin/pip"
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
PKGS="pillow numpy opencv-python-headless mediapipe"
$PIP install -q --timeout 30 $PKGS || $PIP install -q --timeout 60 -i "$MIRROR" $PKGS

echo "④ 让 Claude Code、Codex 和其他 Agent 都能找到这个技能 …"
case "$DEST" in */.claude/plugins/*) LINKS="$HOME/.codex/skills $HOME/.agents/skills" ;; *) LINKS="$HOME/.claude/skills $HOME/.codex/skills $HOME/.agents/skills" ;; esac
for dir in $LINKS; do
  mkdir -p "$dir"
  if [ "$dir/$NAME" != "$DEST" ] && [ ! -e "$dir/$NAME" ]; then ln -s "$DEST" "$dir/$NAME" && echo "   已链接 $dir/$NAME"; fi
done

echo "⑤ 自检 …"
"$DEST/venv/bin/python" -c "import PIL, numpy, cv2, mediapipe" && ffmpeg -version >/dev/null && \
  echo "✅ 安装完成。打开 Claude Code 或 Codex，说“剪一个 vlog 卡点开头，素材在 ~/Movies/xxx”就能开始。"
