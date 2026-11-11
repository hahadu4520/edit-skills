#!/usr/bin/env bash
# 把 shared/ 里的正本复制到各风格技能目录（装插件时只会装到插件自己的目录，所以要各放一份）。
# 改了 shared/ 或模板库（templates/、styles/）之后运行：bash shared/sync.sh
set -e
cd "$(dirname "$0")/.."
for s in course-landscape-edit koubo-edit pixel-edit vlog-beat-edit; do
  d="plugins/$s/skills/$s/scripts/review"
  mkdir -p "$d"
  cp shared/review/review.py shared/review/page.html "$d/"
  echo "已同步 → $d"
done
# 版式模板：渲染器 + 这个风格开放的模板。每个技能只带自己风格的风格文件和模板（styles/<风格>.json 的 templates 一节）
for pair in koubo-edit:koubo vlog-beat-edit:vlog; do
  s="${pair%%:*}"; style="${pair##*:}"
  d="plugins/$s/skills/$s/scripts/templates"
  rm -rf "$d/library"; mkdir -p "$d/library/templates/shots" "$d/library/templates/sequences" "$d/library/styles"
  cp shared/templates/engine.py "$d/"
  cp "styles/$style.json" "$d/library/styles/"
  python3 - "$style" "$d/library" <<'PY'
import json, shutil, sys, os
style, lib = sys.argv[1], sys.argv[2]
t = json.load(open(f"styles/{style}.json", encoding="utf-8"))["templates"]
for kind in ("shots", "sequences"):
    for tid in t.get(kind, {}):
        for ext in (".json", ".jpg"):
            p = f"templates/{kind}/{tid}{ext}"
            if os.path.exists(p):
                shutil.copy(p, f"{lib}/templates/{kind}/")
PY
  echo "已同步 → $d（风格 $style）"
done
# 配乐与卡点（维度 14）：只给 vlog 卡点剪辑
cp shared/music/*.py shared/vlog/*.py plugins/vlog-beat-edit/skills/vlog-beat-edit/scripts/templates/
rm -f plugins/koubo-edit/skills/koubo-edit/scripts/templates/beatgen.py plugins/koubo-edit/skills/koubo-edit/scripts/templates/beats.py
echo "已同步 → 配乐工具"
