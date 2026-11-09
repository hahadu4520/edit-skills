#!/bin/bash
# 横版课程剪辑技能一键安装（macOS / Linux）：bash install.sh
# Windows 请用 install.ps1
set -e
cd "$(dirname "$0")"
SRC="$(pwd)"
NAME="course-landscape-edit"

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
  cp -R SKILL.md AGENTS.md README.md install.sh install.ps1 check.sh check.ps1 new_project.sh package.json scripts fonts examples "$DEST/"
fi

echo "③ 创建独立的 Python 环境，安装 numpy、pillow、opencv …"
python3 -m venv "$DEST/venv"
PIP="$DEST/venv/bin/pip"
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
PKGS="numpy pillow opencv-python-headless"
$PIP install -q --timeout 30 $PKGS || $PIP install -q --timeout 60 -i "$MIRROR" $PKGS

echo "④ 安装 Playwright（渲染课件和动效）和 MiSans 字体 …"
(cd "$DEST" && npm install --silent && npx playwright install chromium) \
  || (cd "$DEST" && npm install --silent --registry=https://registry.npmmirror.com && npx playwright install chromium)

echo "⑤ 让 Claude Code、Codex 和其他 Agent 都能找到这个技能 …"
case "$DEST" in */.claude/plugins/*) LINKS="$HOME/.codex/skills $HOME/.agents/skills" ;; *) LINKS="$HOME/.claude/skills $HOME/.codex/skills $HOME/.agents/skills" ;; esac
for dir in $LINKS; do
  mkdir -p "$dir"
  if [ "$dir/$NAME" != "$DEST" ] && [ ! -e "$dir/$NAME" ]; then ln -s "$DEST" "$dir/$NAME" && echo "   已链接 $dir/$NAME"; fi
done

echo "⑥ 自检 …"
bash "$DEST/check.sh" && echo "✅ 安装完成。打开 Claude Code 或 Codex，说「用横版课程风格剪 <你的原片路径>」就可以开始了。"
