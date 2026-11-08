# 口播剪辑技能（koubo-edit）

让 Claude Code、Codex 等 AI Agent 帮你剪竖屏口播视频：

- 粗剪：去掉停顿、口误和重复。
- 字幕：生成整条字幕，可以加英文做成中英双语。
- 花字和清单：在关键词上加花字，在要点处加编号清单。
- 限流词：说到敏感词时放“哔”声，字幕里打码。
- 封面：出 3 版 3:4 封面供你挑。

每一步做完都会先给你看，再往下走。

## 电脑要求

- **系统**：macOS 或 Windows 10/11 都可以。
  - Apple 芯片（M1 到 M4）的 Mac 转写最快。
  - Windows 和 Intel Mac 会自动换用 faster-whisper；有 NVIDIA 显卡会快很多，只用 CPU 也能跑，就是慢一些。
- **Agent**：装好 [Claude Code](https://claude.com/claude-code) 或 [Codex](https://github.com/openai/codex) 中的任意一个，Cursor、Gemini CLI 等其他 Agent 也能读懂（见 AGENTS.md）。
- **硬盘**：留出约 3GB 空间，用来放转写模型和 Python 环境。

## 安装（只需一次，约 5 到 15 分钟）

见仓库首页 [README](../../../../README.md)：Claude Code 用插件市场一键装；其他 Agent 运行 `bash install.sh koubo-edit`（Windows：`install.ps1 koubo-edit`）。装好后会自动运行本目录的 `install.sh` / `install.ps1`，准备 ffmpeg、Python 环境和转写模型；通过插件市场安装的，第一次用时对 Agent 说“帮我安装口播剪辑的依赖”。

## 使用

1. 把口播原片放进“下载”文件夹，比如 `~/Downloads/0101_raw.MP4`。
2. 打开 Claude Code 或 Codex，对它说：

   > 剪口播 ~/Downloads/0101_raw.MP4

3. Agent 会依次给你：
   - 粗剪片，附上剪掉了哪些内容
   - 字幕里的错字和可能限流的词，请你确认
   - 花字和清单的关键帧预览
   - 成片，需要时也出中英双语版
   - 3 版封面

   每一步你都可以直接说“这里不要剪”“这个词换红色”之类的话来修改。

成片和封面都放在原片所在的文件夹里。中间文件放在 `~/Downloads/<编号>_work/`，剪完可以删掉。

## 文件说明

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 给 Agent 看的操作手册，包括流程和样式规范 |
| `AGENTS.md` | 给 Codex、Cursor 等 Agent 的入口说明 |
| `install.sh` / `install.ps1` | macOS / Windows 一键安装 |
| `scripts/koubo.py` | 剪辑脚本：粗剪、字幕、哔声、预览、烧录、封面 |
| `scripts/style.py` | 花字和清单的样式 |
| `config.example.json` | 一期完整配置的样板（11225《除了 A 股以外都有》） |
| `fonts/` | 内置字体：得意黑、思源宋体 Noto Serif CJK、马善政毛笔楷，都是 SIL OFL 开源字体，可免费商用和分发 |
