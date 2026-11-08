#!/bin/bash
# 横版分段并行渲染：SRC=原片.mov bash render_parts.sh T0 T1 段数 输出目录
# 每段跑一个 r16.py，最后无损拼接成 输出目录/video.mp4（无音轨，之后混入竖版成片的音轨）
T0=$1; T1=$2; N=$3; OUT=$(cd "$(dirname "$4")" && pwd)/$(basename "$4"); mkdir -p "$OUT"
cd "$(dirname "$0")"
PY=python3; [ -x ../venv/bin/python ] && PY=../venv/bin/python
$PY - "$T0" "$T1" "$N" > "$OUT/ranges.txt" <<'PY'
import sys; a,b,n=float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3])
step=(b-a)/n
for i in range(n): print(f"{a+i*step:.4f} {a+(i+1)*step:.4f}")
PY
i=0; while read s e; do $PY r16.py "$OUT/p$i.mp4" $s $e > "$OUT/log$i.txt" 2>&1 & i=$((i+1)); done < "$OUT/ranges.txt"; wait
ls "$OUT"/p*.mp4 | sort -V | sed "s#^#file '#; s#\$#'#" > "$OUT/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$OUT/list.txt" -c copy "$OUT/video.mp4" && echo "完成：$OUT/video.mp4"
