# 模板库

一个模板 = 几个维度取值的打包。维度是字段（[DIMENSIONS.md](../DIMENSIONS.md)），模板是零件，风格是一套搭好的组合（[styles/](../styles)）。

- **模板只定结构**：每块（素材、人像、字幕、标题）放哪、什么形状、怎么进场。
- **皮肤由风格填**：颜色、字体、字号写成 `accent`、`title`、`subtitle` 这样的引用，从 `styles/<风格>.json` 取。同一个模板放进不同风格，颜色和字体跟着风格变。
- **模板和风格多对多**：一个模板标明适用画幅（`aspect`），风格在 `templates` 一节里列出自己开放哪些、状态是 ✓ 还是 △。
- **取值按层覆盖**：风格默认 → 模板 → 系列 → 本集 → 单个镜头。风格禁用（✗）的值哪一层都不能用。

渲染器是 [`shared/templates/engine.py`](../shared/templates/engine.py)，`bash shared/sync.sh` 会把它和整个模板库复制进开放了模板的风格技能。

## 现有模板

### 镜头模板（`shots/`）

一个镜头里的排版。来源：2026-11-11 du 给的「六种口播排版」录屏，拆出 7 种，加一个全屏人像当形变的起点和终点。

| 线框 | id | 名字 | 版式类 | 要什么 | 状态 |
| --- | --- | --- | --- | --- | --- |
| <img src="shots/sticker-hook.jpg" width="90"> | `sticker-hook` | 描边贴纸人 | 全屏人像（抠像） | 人像、抠像 | △ |
| <img src="shots/card-pip.jpg" width="90"> | `card-pip` | 卡片圆窗 | 内容 + 人像小窗 | 人像、素材 | △ |
| <img src="shots/sandwich.jpg" width="90"> | `sandwich` | 三明治竖排 | 内容 + 人像小窗 | 人像、素材 | △ |
| <img src="shots/slant-split.jpg" width="90"> | `slant-split` | 斜切分屏 | 分屏 | 人像、素材 | △ |
| <img src="shots/blur-pip.jpg" width="90"> | `blur-pip` | 虚化圆窗 | 内容 + 人像小窗 | 人像（素材可选） | △ |
| <img src="shots/cinema-band.jpg" width="90"> | `cinema-band` | 宽银幕框 | 全屏内容 + 抠像 | 人像、素材、抠像 | △ |
| <img src="shots/dashed-cutout.jpg" width="90"> | `dashed-cutout` | 虚线抠像 | 全屏内容 + 抠像 | 人像、素材、抠像 | △ |
| <img src="shots/full-portrait.jpg" width="90"> | `full-portrait` | 全屏人像 | 全屏人像 | 人像 | ✓ |

ins 感 vlog（`styles/vlog.json`，技能是 `vlog-beat-edit`）的镜头模板。来源：2026-11-11 du 给的 vlog 开头示例（日本街拍快切、VLOG / Thailand 衬线标题）。

| 线框 | id | 名字 | 版式类 | 要什么 | 状态 |
| --- | --- | --- | --- | --- | --- |
| <img src="shots/vlog-full-tags.jpg" width="90"> | `vlog-full-tags` | 全屏素材 + 角标 | 全屏内容 | 素材 | △ |
| <img src="shots/vlog-title.jpg" width="90"> | `vlog-title` | 衬线大标题 | 全屏内容 | 素材 | △ |
| <img src="shots/vlog-title-behind.jpg" width="90"> | `vlog-title-behind` | 字在人后 | 全屏内容 + 抠像 | 素材（画面里要有人）、抠像 | △ |
| <img src="shots/vlog-inset.jpg" width="90"> | `vlog-inset` | 画中画弹窗 | 全屏内容 + 小窗 | 素材 | △ |

### 片段模板（`sequences/`）

几个镜头模板按字幕句数（口播）或配乐拍数（vlog）串起来，加转场。现在都是开头。

| id | 名字 | 镜头顺序 | 要什么 |
| --- | --- | --- | --- |
| `opening-sticker` | 贴纸钩子开场 | 描边贴纸人（2 句）→ 卡片圆窗（2 句）→ 虚化圆窗 + 素材铺满 | 标题 `hook`、`topic`；1–2 段素材 |
| `opening-slant` | 斜切开场 | 斜切分屏（2 句）→ 宽银幕框（2 句）→ 虚线抠像 | 标题 `hook`；1–3 段素材 |
| `opening-pullback` | 全屏收圆窗开场 | 全屏人像（2 句）→ 虚化圆窗（1 句）→ 换素材铺满（1 句）→ 三明治竖排 | 标题 `hook`；1–2 段素材 |
| `opening-vlog-beat` | ins 感卡点开场 | 钩子（4 拍，配乐前奏）→ 落点进鼓，每半拍硬切（8 拍）→ 衬线大标题压住、底下继续每半拍换（8 拍）→ 结尾重音落在收尾镜头（4 拍） | 配乐 + 节拍表；`tag_l` `tag_r` `title` `note` `sub`；钩子 1 段 + 快切 8–16 段 + 收尾 1 段 |
| `opening-vlog-behind` | 字在人后开场 | 钩子（4 拍）→ 落点上超大衬线字压在人身后（4 拍）→ 每半拍快切（8 拍）→ 衬线标题每拍换（4 拍）→ 收尾（4 拍） | 同上，加 `big`；第 2 段素材要有人站在画面中间 |

元件模板（字幕样式、花字样式、标题样式）现在放在风格文件的 `text` 一节里，模板按名字引用；以后多了再拆出来。

## 文件格式

### 镜头模板

```jsonc
{
  "id": "card-pip", "name": "卡片圆窗", "kind": "shot", "status": "△",
  "aspect": ["9:16"],                 // 适用画幅，风格画幅对不上就不能用
  "layout_class": "内容 + 人像小窗",   // 维度 1 的版式类，✓ ✗ 规则管在这一层
  "needs": ["portrait", "content"],   // 还可能有 matting（要抠像）
  "dims": { "1 排版与布局": "…", "10 人像": "…" },   // 这个模板在各维度上取的值，给人看
  "background": { "type": "paper" },  // paper / content / portrait_blur / color，可加 blur、dim、lower_dim
  "layers": [                         // 从下往上画
    { "slot": "content",  "shape": "roundrect", "box": [0.06, 0.13, 0.88, 0.40], "radius": 0.05, "shadow": true },
    { "slot": "portrait", "shape": "circle", "box": [0.53, 0.43, 0.40, null], "face_width": 0.55,
      "ring": { "color": "white", "width": 0.008 }, "enter": "pop" },
    { "slot": "title",    "anchor": [0.5, 0.075], "text_style": "title_accent", "enter": "pop" },
    { "slot": "subtitle", "anchor": [0.5, 0.79],  "text_style": "subtitle" }
  ]
}
```

- 坐标都是画布的比例，`box` 是 `[x, y, 宽, 高]`；圆的高写 `null`，按宽算成正圆。
- `shape`：`rect`、`roundrect`、`circle`（这三种之间能形变）、`polygon`（给 `points`）、`cutout`（抠像，可加 `stroke` 实线或虚线描边、`bust` 把肩膀收圆、`align` 靠左右）。
- `slot`：`content`、`portrait`、`title`、`subtitle`，还有装饰用的 `panel`（色块）和 `lines`（横线）。
- 人像取景：`face_width` 是脸占框宽的比例，`face_y` 是脸在框里的高度（默认 0.42）。
- `enter` 进场：`pop` 弹出、`fade` 淡入、`rise` 上浮、`wipe` 刷出、`type` 逐字打出（字幕）、`draw` 画线、`slide_left` 从左滑入、`slide_down` 从上扫入（斜切）。
- 颜色和 `text_style` 都是风格文件里的名字，不写死色值。

### 片段模板

```jsonc
{
  "id": "opening-sticker", "kind": "sequence",
  "transition": { "type": "morph", "duration": 0.4 },   // morph 形变 / fade 叠化 / cut 硬切
  "shots": [
    { "template": "sticker-hook", "cues": 2, "title": "hook" },          // 占 2 句字幕，标题用任务里的 titles.hook
    { "template": "card-pip", "cues": 2, "title": "topic", "content": 0 }, // 用第 0 段素材
    { "template": "blur-pip", "cues": "rest", "content": 1,
      "background": { "type": "content", "dim": 0.3, "blur": 0.012 } }   // 镜头里可以覆盖模板的背景
  ]
}
```

按拍排（vlog）：镜头写 `beats`（占几拍）代替 `cues`；`cut_every` 是几拍换一段素材（0.5 = 半拍），素材从 `content` 那段开始往后轮，跨镜头接着轮；`on_drop: true` 的镜头正好从配乐落点开始，前面的镜头落在前奏里。图层可以写 `at_beat`（镜头开始后第几拍才出现）、`until_beat`（第几拍收掉）、`key`（用 `titles` 里的哪一条文字，一个镜头可以有好几行字）、`behind_subject`（字在人后：把背景画面里的人抠出来盖回字上）、`content`（这一块固定用第几段素材，-1 是最后一段）。

形变转场：前后两个镜头里同一个 `slot`、都是 `rect / roundrect / circle` 的块，位置、大小、圆角一起插值，看起来是同一个画面在变；其他块淡入淡出。

### 任务文件（每集一份）

```jsonc
{
  "style": "koubo",
  "sequence": "opening-sticker",            // 或者直接写 "shots": [...] 自己排
  "portrait": { "src": "~/Downloads/11158.MP4", "start": 4.52 },   // 口播原片和开头在原片里的起点
  "cues": [[0.0, 1.73, "分享一个至今让我觉得"], …],                  // 字幕，时间从 start 起算
  "duration": 16.7,
  "content": [{ "src": "broll_1.mp4", "focus": [0.3, 0.4] }, { "src": "card.png", "push": 1.06 }],  // 素材：视频或图片（图片会缓推）；focus 是铺满时的取景中心；视频比镜头短就停在最后一帧
  "split": [2, 3, 99],                       // 可选：按这一集的句子长短，改片段模板里每个镜头占几句
  "titles": { "hook": "这一刀\n差点白挨", "topic": "病程线" }
}
```

vlog 卡点开头的任务文件不用口播原片，换成配乐：

```jsonc
{
  "style": "vlog",
  "sequence": "opening-vlog-beat",
  "music": { "src": "house.wav", "beats": "house.beats.json", "start": "auto" },  // auto：按落点对齐；也可以写歌里的秒数
  "content": [{ "src": "hook.mp4" }, { "src": "c01.mp4", "start": 1.2 }, …, { "src": "selfie.mp4", "crop": [0, 0, 1, 0.75] }],
  "titles": { "tag_l": "atmosphere.daily", "tag_r": "in shanghai", "title": "Thailand", "note": "*july 2026 Record\nby du", "sub": "laid-back vibe" },
  "look": { "grain": 0.04 }      // 可选：覆盖风格的调色
}
```

有口播（`portrait`）又有配乐时，人声一响配乐自动让开；成片统一到 -14 LUFS。配乐和节拍表：

```bash
python beatgen.py house house.wav            # 合成一段配乐 + house.beats.json（house / lofi / pop）
python beats.py 曲库的歌.mp3 --start 32 --dur 15   # 现成的歌：测出节拍表
```

```bash
python engine.py list                              # 列出模板
python engine.py still  job.json 3.5 frame.jpg     # 先看一帧
python engine.py render job.json opening.mp4       # 出片，音频从原片同一段取
python engine.py wire   card-pip card-pip.jpg      # 出线框图
```

### 审片台

模板出的片都能进审片台改（口播开头、vlog 卡点开头都一样）。工作目录里有 `job.json` 或 `opening.json` 就认得出；目录里同时有别的工程（比如口播的 config.json）时加 `--style template`。

```bash
python shared/review/review.py serve <工作目录> --style template --video <这一版>.mp4
python shared/review/review.py apply <工作目录>    # 把修改单写回任务文件，再 render，再 done
```

在 Claude 对话里（有 Artifact 工具）不用起本地服务：`review.py export <工作目录> <输出目录> --style template --video <这一版>.mp4`，把输出目录发布成 Artifact（带 `db` 能力），审片台就在对话里打开，提交的修改单存在页面的 db 里，Agent 读回来 `review.py import` 再 apply。

审片台调 `engine.py plan` 拿时间轴，画出镜头、转场、快切、拍点、标题、字幕几条轨。镜头能换版式（只列这个风格开放的镜头模板，△ 标「待试」，✗ 灰掉）、改占几句或几拍、换素材、调取景；转场选形变、叠化、硬切；标题和字幕直接改字。本集设置里填「存为模板」，apply 时把这一版的镜头顺序存成 `templates/sequences/my-<时间>.json`，挂到风格里，状态 △。

第一次用到抠像时，会把两个 MediaPipe 模型（人像分割、人脸位置，共约 16MB）下载到 `~/.cache/edit-skills/models`。

## 加一个新模板

1. 拿到参考视频，抽帧，把每种排版拆成维度取值。
2. 用到维度表里没有的值，先加进 [DIMENSIONS.md](../DIMENSIONS.md)，标 △。
3. 在 `shots/` 或 `sequences/` 写一份 json，跑 `wire` 出线框图放在旁边，在上面两张表里加一行。
4. 挂到要用它的风格：`styles/<风格>.json` 的 `templates` 里加上，状态先写 △。
5. 用真实素材出一段小样给 du 看，看过转 ✓。
6. `bash shared/sync.sh`。
