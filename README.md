# hahadu 剪辑技能合集（edit-skills）

让 Claude Code、Codex 等 AI Agent 按固定风格帮你剪视频。每种剪辑风格是一个独立的技能，想用哪个装哪个。装好后**重启一次 Claude Code**，然后直接给它视频开剪：第一次用时它会自己检查并装好 ffmpeg、Python 环境和模型（约 5–15 分钟），不用你手动装依赖。

## 包含哪些风格

| 风格 | 插件名 | 适合什么视频 | 出什么 |
|---|---|---|---|
| 朴素版口播 | `koubo-edit` | 真人口播，想快速出一条干净的成片 | 粗剪去停顿口误、整条字幕（可中英双语）、花字和编号清单、限流词哔声打码、3 版 3:4 封面 |
| 像素风剪辑 | `pixel-edit` | 讲概念的口播，想加有记忆点的画面 | 星露谷式像素 B-roll、像素 Agent 界面卡片、3:4 竖版 + 16:9 双语横版、各平台封面 |
| 横版课程剪辑 | `course-landscape-edit` | 讲课、教程，带操作录屏和提示词 | 16:9 课程视频：左课件/录屏/动效卡 + 右人像小窗、开场效果对比、顶部章节进度条、中英双语字幕 |

每个风格的样片截图和详细说明，见各自目录里的 README：[koubo-edit](plugins/koubo-edit/skills/koubo-edit/README.md) · [pixel-edit](plugins/pixel-edit/skills/pixel-edit/README.md) · [course-landscape-edit](plugins/course-landscape-edit/skills/course-landscape-edit/README.md)。

## 安装

### Claude Code

```
/plugin marketplace add hahadu4520/edit-skills
/plugin install course-landscape-edit@hahadu-edit-skills
```

把 `course-landscape-edit` 换成上表里的插件名，就是装别的风格；要几个就装几个。

更新：`/plugin marketplace update hahadu-edit-skills`。

### Codex、Cursor 等其他 Agent

macOS / Linux：

```bash
git clone https://github.com/hahadu4520/edit-skills.git ~/.edit-skills && bash ~/.edit-skills/install.sh koubo-edit
```

Windows（PowerShell，需要先装好 Git）：

```powershell
git clone https://github.com/hahadu4520/edit-skills.git "$HOME\.edit-skills"; powershell -ExecutionPolicy Bypass -File "$HOME\.edit-skills\install.ps1" koubo-edit
```

把最后的 `koubo-edit` 换成上表里的其他插件名（`pixel-edit`、`course-landscape-edit`）就是装对应风格；要几个就各跑一次。不带风格名运行 `install.sh` 会列出所有可装的风格。之前从 koubo-edit 旧仓库装过的不用重装，旧仓库照常能用和更新。

更新：`cd ~/.edit-skills && git pull`。

## 提示缺少依赖怎么办

对 Agent 说“运行技能目录里的 check.sh 检查依赖，缺什么就运行 install.sh 装好”。也可以自己在终端运行：

```bash
bash ~/.edit-skills/plugins/koubo-edit/skills/koubo-edit/check.sh     # 只检查，1 秒
bash ~/.edit-skills/plugins/koubo-edit/skills/koubo-edit/install.sh   # 安装缺的
```

（其他风格把路径里的两处 `koubo-edit` 换成对应插件名；Windows 用同目录的 `check.ps1` / `install.ps1`。）还是装不上，把 install 的报错截图发给作者。

## 仓库结构

```
.claude-plugin/marketplace.json        插件市场清单，每个风格在这里登记一行
plugins/
  koubo-edit/                          朴素版口播
  pixel-edit/                          像素风剪辑
  course-landscape-edit/               横版课程剪辑
    .claude-plugin/plugin.json         插件信息
    hooks/hooks.json                   每次打开 Claude Code 时自检依赖，缺了就提醒 Agent 先安装
    skills/course-landscape-edit/
      SKILL.md                         给 Agent 的操作手册（第 0 步是自检依赖）
      AGENTS.md / README.md            给其他 Agent 的入口 / 给人看的说明
      check.sh / install.sh            依赖自检 / 一键安装（Windows 是 .ps1）
      scripts/                         样板片的完整剪辑工程，新片照着改
      fonts/  examples/                字体 / 样板片的时间轴和截图
shared/                                各风格共用的代码和资源（待抽取）
install.sh / install.ps1               非 Claude Code 的安装脚本：install.sh <插件名>
```

三个风格的目录结构相同，都是 `plugins/<插件名>/skills/<插件名>/` 下放 SKILL.md、脚本和依赖脚本。

加新风格：复制一个 `plugins/<风格>/` 目录，改 SKILL.md、plugin.json 和 check.sh 里要检查的依赖，在 marketplace.json 里加一行，README 的「包含哪些风格」表格和仓库结构各加一行。**每个风格都必须带 check + install，SKILL.md 第 0 步先自检、缺了由 Agent 自己装**，不能把装依赖留给用户。

## 版权

代码 MIT。字体按各自的 SIL Open Font License。样板里的棕色小熊是 hahadu 的频道形象，请在你的视频里换成自己的。
