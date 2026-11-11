# shared

各剪辑风格共用的代码和资源放这里。装插件时只会装到插件自己的目录，所以正本放这里，用 `bash shared/sync.sh` 复制到各风格的 `scripts/` 里。

| 目录 | 是什么 | 已接入的风格 |
|---|---|---|
| `review/` | 审片台：出完一版后在浏览器里看片、定点改，提交成修改单交回 Agent。`review.py` 是本地服务，`page.html` 是网页 | 课程横版、朴素版口播、像素风 |
| `templates/` | 版式模板渲染器 `engine.py`：按风格文件 + 模板库（仓库根目录的 `templates/`、`styles/`）合成画面，sync 时连模板库一起复制 | 朴素版口播 |

改了正本记得跑 `shared/sync.sh`，不要只改某个风格里的复制品。
