# hahadu 剪辑技能合集（edit-skills）

让 Claude Code、Codex 等 AI Agent 按固定风格帮你剪视频。每种剪辑风格是一个独立的技能，想用哪个装哪个。

| 风格 | 一句话 | 说明 |
|---|---|---|
| 口播剪辑 `koubo-edit` | 竖屏口播粗剪（去停顿、口误、重复）、字幕和中英双语、花字和清单、限流词哔声打码、3:4 封面 | [README](plugins/koubo-edit/skills/koubo-edit/README.md) |
| 像素风剪辑 `pixel-edit` | 真人口播 + 星露谷式像素 B-roll、像素 Agent 界面；竖版、双语横版、各平台封面 | [README](plugins/pixel-edit/skills/pixel-edit/README.md) |

两个可以连着用：先用口播剪辑粗剪、出字幕，再用像素风剪辑加像素画面。

## 安装

### Claude Code（推荐）

在 Claude Code 里输入：

```
/plugin marketplace add hahadu4520/edit-skills
/plugin install koubo-edit@hahadu-edit-skills
/plugin install pixel-edit@hahadu-edit-skills
```

想用哪个装哪个。第一次用时对它说“帮我安装口播剪辑（或像素风剪辑）的依赖”，它会运行技能目录里的 `install.sh`（Windows 是 `install.ps1`），准备 ffmpeg、Python 环境和模型。

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

把最后的 `koubo-edit` 换成 `pixel-edit` 就是装像素风剪辑；两个都要就各跑一次。之前从 koubo-edit 旧仓库装过的不用重装，旧仓库照常能用和更新。

更新：`cd ~/.edit-skills && git pull`。

## 仓库结构

```
.claude-plugin/marketplace.json   插件市场清单，新风格在这里登记
plugins/<风格>/                    一个风格一个插件
  .claude-plugin/plugin.json
  skills/<风格>/SKILL.md           给 Agent 的操作手册，脚本、字体、示例都在这个目录
shared/                           各风格共用的代码和资源（待抽取）
install.sh / install.ps1           非 Claude Code 的安装脚本
```

加新风格：复制一个 `plugins/<风格>/` 目录，改 SKILL.md 和 plugin.json，在 marketplace.json 里加一行，README 表格加一行。

## 版权

代码 MIT。字体按各自的 SIL Open Font License。样板里的棕色小熊是 hahadu 的频道形象，请在你的视频里换成自己的。
