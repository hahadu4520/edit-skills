# vlog 卡点剪辑（vlog-beat-edit）

把一组手机拍的旅行、日常素材，按配乐的拍子剪成 ins 感 vlog 开头：

- **钩子停在前奏**：一个有情绪的镜头先停约 2 秒
- **落点进鼓，每半拍硬切**：约 0.25 秒一个镜头，切点压在拍上（误差 1 帧以内）
- **细衬线英文大标题**：标题不动、底下素材继续切；可以做「字在人后」
- **暖调 + 胶片颗粒**，左右细体角标
- **配乐**：现场合成一段免版权配乐（house / lofi / pop），或者用你自己的歌，自动测节拍

## 用法

装好后对 Agent 说：“剪一个 vlog 卡点开头，素材在 ~/Movies/东京，标题 Tokyo”。它会先问清楚素材、文字和配乐，出几帧给你看，确认后出片。

## 两个开头模板

| 模板 | 结构 |
| --- | --- |
| ins 感卡点开场 `opening-vlog-beat` | 钩子 4 拍 → 每半拍快切 8 拍 → 衬线标题 + 快切 8 拍 → 收尾 4 拍 |
| 字在人后开场 `opening-vlog-behind` | 钩子 4 拍 → 超大衬线字压在人身后 4 拍 → 快切 8 拍 → 标题 4 拍 → 收尾 4 拍 |

模板只定结构，字体和调色在 `styles/vlog.json`。维度说明见仓库的 [剪辑维度配置表](../../../../DIMENSIONS.md)「14 配乐与卡点」。

## 字体

Playfair Display（SIL Open Font License，见 `fonts/OFL-PlayfairDisplay.txt`）、得意黑 Smiley Sans（SIL OFL）。
