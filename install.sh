#!/bin/bash
# 不用 Claude Code 插件市场时的安装方式（Codex、Cursor 等）：
#   git clone https://github.com/hahadu4520/edit-skills.git ~/.edit-skills && bash ~/.edit-skills/install.sh pixel-edit
# 不带参数运行会列出所有可装的风格。
set -e
cd "$(dirname "$0")"
if [ -z "$1" ]; then echo "可安装的剪辑风格："; ls plugins; echo "用法：bash install.sh <风格名>"; exit 0; fi
D="plugins/$1/skills/$1"
[ -d "$D" ] || { echo "❌ 没有这个风格：$1"; ls plugins; exit 1; }
for dir in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills"; do
  mkdir -p "$dir"; [ -e "$dir/$1" ] || { ln -s "$(pwd)/$D" "$dir/$1"; echo "已链接 $dir/$1"; }
done
bash "$D/install.sh"
