# AGENTS.md

这个仓库是「像素风剪辑」技能：给真人口播视频加星露谷式像素画面。Claude Code、Codex、Cursor、Gemini CLI 等任何编程 Agent 都可以用。

- **流程和样式规范**：完整写在 [SKILL.md](SKILL.md)。用户说“像素风剪辑”“像素风”“加像素动画”时，先读 SKILL.md，再照着做。
- **代码**：`scripts/` 是样板片《Git 和 GitHub 到底是什么》的完整剪辑工程。新片复制一份到工作目录，只改内容和时间表。Python 用技能目录下的 `venv/bin/python`（Windows 是 `venv\Scripts\python.exe`）。
- **还没安装时**（技能目录下没有 `venv/`）：先让用户安装。macOS / Linux 运行 `bash install.sh`；Windows 运行 `powershell -ExecutionPolicy Bypass -File install.ps1`。
- **每一步都先给用户看再往下**：镜头表、关键帧、小样、双语字幕对照表、封面，都要等用户确认。
