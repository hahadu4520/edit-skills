#!/bin/bash
# 新建一期剪辑工程：bash new_project.sh <工作目录>
# 会生成 <工作目录>/ed/（剪辑工程，脚本都在里面跑），原片放 <工作目录>/src.mp4，素材放 <工作目录>/素材/
set -e
D="$(cd "$(dirname "$0")" && pwd)"
[ -n "$1" ] || { echo "用法：bash new_project.sh <工作目录>"; exit 1; }
W="$(mkdir -p "$1" && cd "$1" && pwd)"; E="$W/ed"
[ -e "$E" ] && { echo "❌ $E 已存在，不覆盖"; exit 1; }
mkdir -p "$E" "$W/素材" "$W/rec"
cp -R "$D/scripts/." "$E/"
mkdir -p "$E/fonts" "$E/slides/out" "$E/cmp" "$E/rec" "$E/kf"
cp "$D/fonts/SmileySans-Oblique.ttf" "$E/fonts/"
cp "$D"/fonts/*.woff2 "$E/"
ln -s "$D/node_modules" "$E/node_modules"
ln -s "$D/venv" "$E/venv"
echo "✅ 工程已建好：$E"
echo "   原片放到 $W/src.mp4；Python 用 $E/venv/bin/python"
