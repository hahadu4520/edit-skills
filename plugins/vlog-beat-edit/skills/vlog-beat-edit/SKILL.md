---
name: vlog-beat-edit
description: 「vlog 卡点剪辑」两个模板。模板一按配乐拍子剪 ins 感 vlog 开头：钩子镜头停在前奏，落点进鼓后素材每半拍硬切，细衬线英文大标题（可压在人身后）收住，保留原片色调。配乐可以现场合成（免版权）或用现成的歌测节拍。模板二「城市电影感」：按素材之间的关系（虚实、母题接力、远到近、细节先于人、首尾呼应）排一座城市的风景人文，镜头跟乐句不逐拍硬切，配乐没有鼓。当用户说“vlog 卡点”“城市 vlog”“电影感 vlog”“城市宣传片那种”“vlog 开头”“ins 感快剪”“卡点剪辑”“按音乐节奏剪”“给素材配卡点音乐”，或给出一组旅行、日常的手机素材要剪开头时使用。
---

# vlog 卡点剪辑

两个模板：**模板一 ins 感卡点开头**（下面第 1–5 步）和**模板二城市电影感**（见「模板二」一节）。用户没说就看素材：一堆手持生活小物、要快剪开头 → 模板一；一座城市的地标、街景、人文，要有电影感 → 模板二。拿不准就问一句。

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
5. 画面左右各一行很细的角标（地点、账号）；不调色、不加颗粒，保留原片色调。

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
# 法式（116 BPM，手风琴旋律 + 吉他 la pompe + 低音提琴 + 鼓刷）：--mood nostalgic 小调怀旧 / bright 大调明亮，换 --seed 换一句旋律
python <SKILL>/scripts/templates/beatgen.py french <workdir>/music.wav --mood nostalgic --seed 3
# 现成的歌（剪映曲库、买的版权音乐）：测出节拍表，只取开头要用的那一段
python <SKILL>/scripts/templates/beats.py <歌.mp3> --start <从哪秒开始> --dur 15 --out <workdir>/music.beats.json
```

- **先填配乐简报**：看素材关键帧，按维度表「14 配乐与卡点」里的律动、调式与和声、配器、旋律、质感、人声各选一个值，跟用户确认一句（比如「巴黎秋天、偏怀旧 → french nostalgic」），再生成或挑歌。
- 合成的配乐音色比较基础，要跟用户说清楚；正片建议用曲库的歌。旋律不满意就换 `--seed`，一次出 2–3 个给用户挑。
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
- `look`（可选，默认不写）：模板默认不调色、不加颗粒。只有用户明确要调色时才写，比如 `{"warm": 0.03}`。

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
- 用户提交后，`python <SKILL>/scripts/review/review.py changes <workdir>` 读修改单。vlog 开头所有能改的东西都在 `opening.json` 里：换某一刀的素材就调 `content` 的顺序或换 `src`；切得太碎就改片段里的 `cut_every`（写进任务的 `shots`）；改字改 `titles`；用户要调色才加 `look`；换歌重测节拍表。改完重出片，再 `review.py done <workdir>`，下一版版本号自动 +1。
- 时间轴（`engine.py plan` 的输出）是所有模板任务共用的格式，口播开头也一样，审片台按它画镜头轨、切点和拍点。


## 模板二：城市电影感（city-cinematic）

来源：2026-11-11 du 给的北京 vlog（只取结构，不用它的画面）。和模板一正好相反：**不逐拍硬切**，镜头跟着乐句和画面里的动作走；配乐没有鼓，每两拍一下低音。适合一座城市、一次旅行的整段风景人文，20–40 秒。

### 规则写的是「素材之间的关系」，不是某座城市

每座城市的素材不一样，有的有倒影、有的没有猫，所以模板不写死「第几刀放什么」，只写角色和关系，`arrange.py` 按规则现排，缺哪种素材就跳过那一步：

| 段落 | 角色 | 挑什么样的素材 | 拍数（78 BPM 下约 0.77 秒一拍） |
| --- | --- | --- | --- |
| 开场 | 意象 + 竖排城市名 | 倒影、虚焦、剪影、局部；最好和主地标同地点或同母题 | 1.5 |
| | 局部（城市名跨过这一刀淡出） | 建筑或地标的近景、特写；和意象是「虚 → 实」或同母题 | 1.5 |
| | 建立 | 主地标远景 | 2 |
| | 快闪 × 2（配乐的「呼」） | 有运动的素材：飞鸟、车、行人，不同地点 | 0.33 + 0.67 |
| | 落点（正片开始） | 主地标更近的另一个角度；没有就换一个地标 | 3 |
| 正片 | 地标章 | 同地点按 远 → 中 → 近 → 细节 | 每刀 2–3 |
| | 市井章（全片最密） | 街景开头；细节先出、人后出（象棋 → 下棋的人）；人接人越往后越快 | 每刀 0.5–2.5 |
| | 安静章 | 物件、屋顶、动物，动物压后 | 每刀 2 |
| 收尾 | 呼应 | 和开场同地点或同母题的地标 | 3–4 |

镜头之间的关系（`arrange.py` 给每一对相邻镜头打分，审片台里每个镜头的 `why` 就是它）：
- **虚 → 实**：倒影、虚焦接同一母题的实物。
- **母题接力**：上下两刀共享形状、颜色、物种，换章时优先用它（石狮 → 兽首门环、屋顶 → 屋檐上的猫）。
- **景别递进**：同一章里由远到近；市井章里细节先于人（先让人好奇，再交代是谁）。
- **插入**：主地标远景和近景之间插两下快闪。
- **遮挡**：有前景划过的素材放章末，遮挡划过时切到下一章。
- **动作**：素材里有关键动作（落子、回头）的，动作落在这一刀的后四分之三，切在动作之后。
- **呼应**：结尾回到开场的地点或母题。
- **避免**：同一主体同景别连着放；离开一个地点又回来（除了结尾）。
- **章节换在低音上**：每章总拍数补到偶数，换章正好落在每两拍那一下低音上；章内的刀不硬卡拍。

### 做法

1. **收素材、打标签**：素材文件夹里每段抽中间帧拼一张图看（`ffmpeg -ss <中间秒> -i x.mp4 -frames:v 1`），按下面的标签写素材表 `<workdir>/clips.json`。样板在 `<SKILL>/examples/clips.example.json`（21 段，北京的例子）。标签都很抽象，看一眼就能填，不用懂这座城市：

   ```json
   {"city": "北京", "city_en": "BEIJING",
    "clips": [
     {"src": "~/素材/beihai_1.mp4", "place": "北海", "scale": "wide", "subject": "landmark", "hero": true, "motifs": ["塔"]},
     {"src": "~/素材/water.mp4", "place": "故宫", "scale": "medium", "subject": "building", "image": true, "motifs": ["红色", "屋顶"]},
     {"src": "~/素材/chess.mp4", "place": "胡同", "scale": "detail", "subject": "object", "motifs": ["棋"], "action_at": 1.2}
    ]}
   ```
   - `place` 地点（同地点排成一章）、`scale` 景别（wide / medium / close / detail）、`subject` 主体（landmark / building / nature / street / people / object / animal / vehicle / sky）
   - `motion`（still / inner 主体在动 / cross 有东西横穿）、`dir` 运动方向（l2r / r2l）、`motifs` 母题（形状、颜色、物种，能跨地点接力的东西）
   - `hero` 主地标（1–3 段）、`image` 意象镜头（倒影、虚焦）、`occluder` 有前景遮挡、`action_at` 关键动作在第几秒、`start` / `len` 用哪一段
   - 素材有烧进去的字幕水印用 `crop`，取景中心用 `focus`，和模板一一样。

   标签写完先跟用户对一下哪几段是主地标、城市名怎么写（中文竖排 + 英文小字）。

2. **排镜头 + 配乐**：

   ```bash
   python <SKILL>/scripts/templates/arrange.py <workdir>/clips.json <workdir>/city.json
   ```
   打印出排好的镜头表（每刀的时间、拍数、角色、为什么这样接），同时按总拍数合成一段 `beatgen cinematic` 配乐（弦乐铺底 + 钢琴 + 每两拍一下低音，没有鼓，前奏最后两拍一个「呼」）。用现成的歌就加 `--music <歌.wav>`（同目录要有 `beats.py` 测出的 `.beats.json`；没有鼓的歌测得不准，测的时候知道 BPM 就给 `beats.py` 加 `--bpm`）。

3. **先出几帧、再出片、上审片台**：和模板一的第 3–5 步一样，任务文件换成 `city.json`。先给用户看开场城市名那一帧（约 0.8 秒）和落点那一帧。审片台的时间轴里每个镜头带 `role`、`chapter`、`why`；用户说「这两刀接得不顺」「这章太长」，就改素材表的标签（比如补一个母题、改景别、去掉一段）重新 `arrange.py`，或者直接改 `city.json` 里那一刀的 `beats` / `content`。

## 规则（违反就改，不出片）

- 两个模板都只用硬切，不加闪白、旋转、翻页这类转场（维度 5 ✗）。
- 模板一切点密度：每半拍或每拍；不要每 1/4 拍（太碎）。模板二不硬卡拍，但换章落在低音上。
- 钩子只停在前奏里，不切。
- 标题是英文细衬线，不描边、不加粗；中文字幕开头不出。
- 不用别人的视频素材和人像。

## 模板和代码在哪

这个技能的模板、风格和渲染器是仓库公共模板库的复制品，正本在仓库根目录：
- `templates/shots/vlog-*.json`、`templates/sequences/opening-vlog-*.json`、`templates/sequences/city-cinematic.json`：镜头模板和片段模板
- `styles/vlog.json`：皮肤（字体、文字样式、配乐默认值）和开放的模板
- `shared/templates/engine.py`（渲染器）、`shared/music/`（配乐生成和测节拍）、`shared/vlog/arrange.py`（城市电影感编排）

改正本，再在仓库里跑 `bash shared/sync.sh` 复制进来，不要只改复制品。新模板的加法见 `templates/README.md`。这些模板现在都是 △，用户看过真实素材的样片后再转 ✓。
