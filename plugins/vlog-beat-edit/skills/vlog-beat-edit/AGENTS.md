# AGENTS.md

这是一个「vlog 卡点剪辑」技能，任何编程 Agent 都可以使用，包括 Claude Code、Codex、Cursor、Gemini CLI 等。

- **流程和规范**：完整写在 [SKILL.md](SKILL.md)。用户说“vlog 卡点”“vlog 开头”“ins 感快剪”“按音乐节奏剪”，或给出一组旅行、日常素材要剪开头时，先读 SKILL.md，再照着做。
- **所有操作**：`scripts/templates/engine.py`（出帧、出片）、`scripts/templates/beatgen.py`（合成配乐）、`scripts/templates/beats.py`（测节拍），用技能自带 venv 里的 Python 跑。
- **还没安装时**（技能目录下没有 `venv/`）：macOS / Linux 运行 `bash install.sh`；Windows 运行 `powershell -ExecutionPolicy Bypass -File install.ps1`。
- **先出几帧给用户看，再出片**。
