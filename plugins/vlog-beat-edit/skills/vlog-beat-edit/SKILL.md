---
name: vlog-beat-edit
description: 「vlog 卡点剪辑」按配乐拍子剪 ins 感 vlog 开头：钩子镜头停在前奏，落点进鼓后素材每半拍硬切，细衬线英文大标题（可压在人身后）收住，暖调加胶片颗粒。配乐可以现场合成（免版权）或用现成的歌测节拍。当用户说“vlog 卡点”“vlog 开头”“ins 感快剪”“卡点剪辑”“按音乐节奏剪”“给素材配卡点音乐”，或给出一组旅行、日常的手机素材要剪开头时使用。
---

# vlog 卡点剪辑

> **维度表**：这个风格是[剪辑维度配置表](https://github.com/hahadu4520/edit-skills/blob/main/DIMENSIONS.md)里「ins 感 vlog」那一列，核心是维度 14「配乐与卡点」。改风格、加新手法前，先在表里找到对应的维度和属性，按 ✓ 允许 / △ 待试 / ✗ 禁用 处理；表和本文件要保持一致。

下面的 `<SKILL>` 指这个 SKILL.md 所在的目录。

## 第 0 步：先自检依赖（每次开始前都做）

运行 `bash <SKILL>/check.sh`（Windows：`powershell -ExecutionPolicy Bypass -File <SKILL>\check.ps1`）。
- 输出 OK：直接开始。
- 缺东西：**不要让用户自己去装**。直接运行 `bash <SKILL>/install.sh`（Windows：`install.ps1`），装完再跑一次 check。安装约 3–5 分钟，开始前跟用户说一声。
- 安装本身失败：把报错原文和用户要做的那一件事告诉用户，别的都替用户做掉。

所有命令都用技能自带的 Python：`<SKILL>/venv/bin/python`（Windows：`<SKILL>\venv\Scripts\python.exe`），下文简写为 `python`。

## 这个风格长什么样

来源：2026-11-11 du 给的 vlog 开头示例（日本街拍快切、VLOG / Thailand 衬线标题）。

1. **钩子停 4 拍**（约 2 秒，配乐前奏）：一个有情绪的镜头，人回头、张嘴、反差大的画面。只有这个镜头停得久。
2. **落点进鼓，每半拍硬切**（约 0.25 秒一个镜头，8 拍 16 个）：第一人称手持、生活小物、局部特写。不加任何转场特效，全是硬切，切点压在拍上。
3. **衬线大标题压住**：白色细衬线英文（地名或主题），右上一行斜体小注（日期、by 谁），左下一行小写副标。标题不动，底下继续每半拍换素材。
4. **结尾重音**：最后一个镜头（人物自拍或回头）落在配乐的结尾重音上，停 4 拍。
5. 画面左右各一行很细的角标（地点、账号）；整体暖调、黑位提一点、胶片颗粒。

## 第 1 步：问清楚、收素材

先问用户三件事，能一次问完就一次问完：
- **素材在哪**：一个文件夹。需要：1 段钩子 + 8–16 段快切素材 + 1 段收尾（人物自拍或回头）；做「字在人后」还要 1 段人站在画面中间的镜头。每段 1 秒以上就够。**只用用户自己拍的素材**，不要用别人的视频，也不要拿用户以前别的片子里的人像凑数。
- **文字**：标题（一个英文词，比如地名）、小注（比如 `*july 2026 Record` / `by 名字`）、副标、两个角标。用户没想好就按素材内容给 2–3 组建议让他挑。
- **配乐**：有指定的歌就用歌；没有就合成一段（见第 2 步）。

素材按时长、画面先过一遍：抽每段的中间帧拼一张图看，挑出适合做钩子、收尾、字在人后的那几段，其余按「远 → 近 → 手 → 物」大致交替排进快切。素材里有烧进去的字幕、水印，用 `crop` 裁掉。

## 第 2 步：配乐和节拍表（维度 14）

两种来源，后面的用法完全一样，都会得到一份节拍表 `*.beats.json`（BPM、每一拍的秒数、落点）：

```bash
# 合成一段免版权配乐：house（ins 快节奏卡点，默认 122 BPM）/ lofi（日常慢 vlog，86）/ pop（明亮旅行，128）
python <SKILL>/scripts/templates/beatgen.py house <workdir>/music.wav
# 现成的歌（剪映曲库、买的版权音乐）：测出节拍表，只取开头要用的那一段
python <SKILL>/scripts/templates/beats.py <歌.mp3> --start <从哪秒开始> --dur 15 --out <workdir>/music.beats.json
```

- 合成的配乐音色比较基础，要跟用户说清楚；正片建议用曲库的歌。
- 测出来的 BPM 和落点，先抽查：落点那一拍是不是鼓真正进来的地方。不对就用 `--drop <秒>` 指定，知道 BPM 就用 `--bpm` 指定。
- 用别人的歌要提醒用户确认版权。

## 第 3 步：写任务文件，先出几帧

两个片段模板，不确定就两个都出给用户挑：

| 片段模板 | 结构 | 要什么 |
| --- | --- | --- |
| `opening-vlog-beat` | 钩子 4 拍 → 落点每半拍快切 8 拍 → 衬线标题 + 每半拍快切 8 拍 → 收尾 4 拍 | 钩子 + 快切 + 收尾 |
| `opening-vlog-behind` | 钩子 4 拍 → 落点上超大衬线字压在人身后 4 拍 → 每半拍快切 8 拍 → 标题每拍换 4 拍 → 收尾 4 拍 | 再加 1 段人站在画面中间的镜头 |

样板在 `<SKILL>/examples/opening.example.json`，复制到 `<workdir>/opening.json` 改：

- `music.src` / `music.beats`：第 2 步的配乐和节拍表；`start: "auto"` 让快切第一刀正好落在鼓进来那一拍。
- `content`：第 0 段钩子，`opening-vlog-behind` 的第 1 段是人站在中间的镜头，后面是快切素材，最后一段是收尾。每段可以写 `start`（从素材第几秒开始用）、`crop`（裁掉字幕水印）、`focus`（铺满时取景中心）。素材不够快切用，会在快切那几段里循环，不会轮回钩子。
- `titles`：`title` 标题、`note` 斜体小注（可换行 `\n`）、`sub` 副标、`tag_l` `tag_r` 角标、`big` 字在人后的大字（通常是 `VLOG`）。
- `look`（可选）：覆盖调色，比如 `{"grain": 0.04, "warm": 0.03}`。

```bash
python <SKILL>/scripts/templates/engine.py still  <workdir>/opening.json 1.0 <workdir>/f_hook.jpg     # 钩子
python <SKILL>/scripts/templates/engine.py still  <workdir>/opening.json 3.0 <workdir>/f_cut.jpg      # 快切
python <SKILL>/scripts/templates/engine.py still  <workdir>/opening.json 7.0 <workdir>/f_title.jpg    # 标题
```

**先把这几帧给用户看**，确认标题文字、字体位置、画面选得对，再出片。字在人后那一帧要特别看：人是不是挡住了字的一部分、字还认不认得出。

## 第 4 步：出片

```bash
python <SKILL>/scripts/templates/engine.py render <workdir>/opening.json <workdir>/vlog_开头.mp4
```

- 成片带配乐，统一到 -14 LUFS；有口播原片（`portrait`）时人声一响配乐自动让开。
- 出完自查切点：`ffmpeg -i <成片> -vf "select='gt(scene,0.15)',showinfo" -f null -` 抽出切点时间，和节拍表比，误差应在 1 帧（0.033 秒）以内。
- 接正片：用 ffmpeg concat 接在正片前面；正片自己的音乐从开头结尾重音之后接上。

## 第 5 步：审片台改（每出一版都走）

很难一次出对，每出一版都用审片台让用户看片、定点改：

```bash
python <SKILL>/scripts/templates/engine.py plan <workdir>/opening.json <workdir>/opening.plan.json   # 时间轴：镜头、切点、用了哪段素材、文字、拍点
python <SKILL>/scripts/review/review.py serve <workdir> --video <workdir>/vlog_开头.mp4 --no-open
```

- 在后台运行 serve，按你所在的 Agent 在侧边栏打开它打印的地址，地址同时发给用户。
- 用户提交后，`python <SKILL>/scripts/review/review.py changes <workdir>` 读修改单。vlog 开头所有能改的东西都在 `opening.json` 里：换某一刀的素材就调 `content` 的顺序或换 `src`；切得太碎就改片段里的 `cut_every`（写进任务的 `shots`）；改字改 `titles`；调色改 `look`；换歌重测节拍表。改完重出片，再 `review.py done <workdir>`，下一版版本号自动 +1。
- 时间轴（`engine.py plan` 的输出）是所有模板任务共用的格式，口播开头也一样，审片台按它画镜头轨、切点和拍点。

## 规则（违反就改，不出片）

- 卡点全部硬切，不加闪白、旋转、翻页这类转场（维度 5 ✗）。
- 切点密度：每半拍或每拍；不要每 1/4 拍（太碎）。
- 钩子只停在前奏里，不切。
- 标题是英文细衬线，不描边、不加粗；中文字幕开头不出。
- 不用别人的视频素材和人像。

## 模板和代码在哪

这个技能的模板、风格和渲染器是仓库公共模板库的复制品，正本在仓库根目录：
- `templates/shots/vlog-*.json`、`templates/sequences/opening-vlog-*.json`：镜头模板和片段模板
- `styles/vlog.json`：皮肤（字体、文字样式、调色、配乐默认值）和开放的模板
- `shared/templates/engine.py`（渲染器）、`shared/music/`（配乐生成和测节拍）

改正本，再在仓库里跑 `bash shared/sync.sh` 复制进来，不要只改复制品。新模板的加法见 `templates/README.md`。这些模板现在都是 △，用户看过真实素材的样片后再转 ✓。
