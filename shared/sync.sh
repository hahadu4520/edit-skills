#!/usr/bin/env bash
# 把 shared/ 里的正本复制到各风格技能目录（装插件时只会装到插件自己的目录，所以要各放一份）。
# 改了 shared/review/ 之后运行：bash shared/sync.sh
set -e
cd "$(dirname "$0")/.."
for s in course-landscape-edit koubo-edit pixel-edit; do
  d="plugins/$s/skills/$s/scripts/review"
  mkdir -p "$d"
  cp shared/review/review.py shared/review/page.html "$d/"
  echo "已同步 → $d"
done
