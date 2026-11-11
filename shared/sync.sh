#!/usr/bin/env bash
# 把 shared/ 里的正本复制到各风格技能目录（装插件时只会装到插件自己的目录，所以要各放一份）。
# 改了 shared/ 或模板库（templates/、styles/）之后运行：bash shared/sync.sh
set -e
cd "$(dirname "$0")/.."
for s in course-landscape-edit koubo-edit pixel-edit; do
  d="plugins/$s/skills/$s/scripts/review"
  mkdir -p "$d"
  cp shared/review/review.py shared/review/page.html "$d/"
  echo "已同步 → $d"
done
# 版式模板：渲染器 + 模板库。只同步给开放了模板的风格（styles/<风格>.json 里有 templates 一节）
for s in koubo-edit; do
  d="plugins/$s/skills/$s/scripts/templates"
  rm -rf "$d/library"; mkdir -p "$d/library/templates"
  cp shared/templates/engine.py "$d/"
  cp -R templates/shots templates/sequences "$d/library/templates/"
  cp -R styles "$d/library/"
  echo "已同步 → $d"
done
