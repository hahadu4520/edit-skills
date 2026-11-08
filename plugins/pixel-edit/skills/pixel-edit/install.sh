#!/bin/bash
# 像素风剪辑技能一键安装（macOS / Linux）：bash install.sh
# Windows 请用 install.ps1
set -e
cd "$(dirname "$0")"
SRC="$(pwd)"
NAME="pixel-edit"

case "$SRC" in
  */skills/$NAME) DEST="$SRC" ;;
  *) DEST="$HOME/.claude/skills/$NAME" ;;
esac

if [ "$(uname -s)" = "Darwin" ] && ! command -v brew >/dev/null 2>&1; then
  echo "❌ 没找到 Homebrew。先在终端运行下面这行装好，再重新运行本脚本："
  echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'; exit 1
fi

echo "① 检查 ffmpeg、Python 和 Node.js …"
for pair in "ffmpeg:ffmpeg" "python3:python" "node:node"; do
  cmd=${pair%%:*}; pkg=${pair##*:}
  if ! command -v $cmd >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then brew install $pkg
    else echo "❌ 请先安装 $pkg"; exit 1; fi
  fi
done

if [ "$SRC" != "$DEST" ]; then
  echo "② 复制技能到 $DEST …"
  mkdir -p "$DEST"
  cp -R SKILL.md AGENTS.md README.md install.sh install.ps1 check.sh check.ps1 scripts screenshots fonts examples "$DEST/"
fi

echo "③ 创建独立的 Python 环境，安装 numpy、pillow、sherpa-onnx …"
python3 -m venv "$DEST/venv"
PIP="$DEST/venv/bin/pip"
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
$PIP install -q --timeout 30 numpy pillow sherpa-onnx || $PIP install -q --timeout 60 -i "$MIRROR" numpy pillow sherpa-onnx

echo "④ 安装截图用的 Playwright（对话截图镜头要用）…"
(cd "$DEST/screenshots" && npm init -y >/dev/null 2>&1; npm install --silent playwright && npx playwright install chromium) \
  || echo "⚠️  Playwright 安装失败，不影响像素画面；用到对话截图时再装：cd $DEST/screenshots && npm install playwright && npx playwright install chromium"

echo "⑤ 让 Claude Code、Codex 和其他 Agent 都能找到这个技能 …"
case "$DEST" in */.claude/plugins/*) LINKS="$HOME/.codex/skills $HOME/.agents/skills" ;; *) LINKS="$HOME/.claude/skills $HOME/.codex/skills $HOME/.agents/skills" ;; esac
for dir in $LINKS; do
  mkdir -p "$dir"
  if [ "$dir/$NAME" != "$DEST" ] && [ ! -e "$dir/$NAME" ]; then ln -s "$DEST" "$dir/$NAME" && echo "   已链接 $dir/$NAME"; fi
done

echo "⑥ 自检 …"
"$DEST/venv/bin/python" -c "import numpy, PIL" && ffmpeg -version >/dev/null && echo "✅ 安装完成。打开 Claude Code 或 Codex，说「用像素风剪辑 <你的原片路径>」就可以开始了。"
