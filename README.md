# hahadu 剪辑技能合集（edit-skills）

让 Claude Code、Codex 等 AI Agent 按固定风格帮你剪视频。每种剪辑风格是一个独立的技能，想用哪个装哪个。装好后**重启一次 Claude Code**，然后直接给它视频开剪：第一次用时它会自己检查并装好 ffmpeg、Python 环境和模型（约 5–15 分钟），不用你手动装依赖。

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

## 提示缺少依赖怎么办

对 Agent 说“运行技能目录里的 check.sh 检查依赖，缺什么就运行 install.sh 装好”。也可以自己在终端运行：

```bash
bash ~/.edit-skills/plugins/koubo-edit/skills/koubo-edit/check.sh     # 只检查，1 秒
bash ~/.edit-skills/plugins/koubo-edit/skills/koubo-edit/install.sh   # 安装缺的
```

（像素风剪辑把路径里的 `koubo-edit` 换成 `pixel-edit`；Windows 用同目录的 `check.ps1` / `install.ps1`。）还是装不上，把 install 的报错截图发给作者。

## 仓库结构

```
.claude-plugin/marketplace.json   插件市场清单，新风格在这里登记
plugins/<风格>/                    一个风格一个插件
  .claude-plugin/plugin.json
  hooks/hooks.json                 每次打开 Claude Code 时自检依赖，缺了就提醒 Agent 先安装
  skills/<风格>/SKILL.md           给 Agent 的操作手册（第 0 步是自检依赖），脚本、字体、示例都在这个目录
  skills/<风格>/check.sh / install.sh   依赖自检 / 一键安装（Windows 是 .ps1）
shared/                           各风格共用的代码和资源（待抽取）
install.sh / install.ps1           非 Claude Code 的安装脚本
```

加新风格：复制一个 `plugins/<风格>/` 目录，改 SKILL.md、plugin.json 和 check.sh 里要检查的依赖，在 marketplace.json 里加一行，README 表格加一行。**每个风格都必须带 check + install，SKILL.md 第 0 步先自检、缺了由 Agent 自己装**，不能把装依赖留给用户。

## 版权

代码 MIT。字体按各自的 SIL Open Font License。样板里的棕色小熊是 hahadu 的频道形象，请在你的视频里换成自己的。
