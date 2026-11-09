# AGENTS.md

这个目录是「横版课程剪辑」技能：把真人讲课口播剪成 16:9 横版课程视频（左课件/录屏/动效卡 + 右人像小窗 + 顶部章节进度条 + 中英双语字幕）。Claude Code、Codex、Cursor、Gemini CLI 等任何编程 Agent 都可以用。

- **流程和样式规范**：完整写在 [SKILL.md](SKILL.md)。用户说“横版课程”“课程风格剪辑”“按豆包电商那集的风格剪”时，先读 SKILL.md，再照着做。
- **哪些是定死的**：画面骨架、配色、字体、字幕、进度条、PPT 样式、时间轴结构照做。动效、转场、镜头运动是底线不是上限，鼓励做得更好，但新动效要先出小样给用户确认。
- **代码**：`scripts/` 是样板片（豆包电商第 1 集）的剪辑工程。新片用 `bash new_project.sh <工作目录>` 复制一份，只改内容和时间表。Python 用技能目录下的 `venv/bin/python`（Windows 是 `venv\Scripts\python.exe`）。
- **还没安装时**（`bash check.sh` 报缺东西）：直接帮用户装。macOS / Linux 运行 `bash install.sh`；Windows 运行 `powershell -ExecutionPolicy Bypass -File install.ps1`。
- **每一步都先给用户看再往下**：素材清单、时间轴、关键帧（改前 / 改后并排）、动效小样，都要等用户确认再合成整片。
