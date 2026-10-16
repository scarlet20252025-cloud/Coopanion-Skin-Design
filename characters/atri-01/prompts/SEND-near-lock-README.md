# 近侧马尾：在 ChatGPT「工作」里发这一件（2026-10-16）

环境限制：本机 Computer Use 只能看到 Codex 内置浏览器与 MCP Apps 面板，没有登录着 ChatGPT 的
Chrome 标签页，`docs/08` 的发送/取图脚本无法执行。所以这一条由你手动发一次，我只负责准备与收件。

## 怎么发

1. 新开一个 ChatGPT 会话，切到「工作」模式，推理强度选「高」（复现包 `docs/08`：不需要 MAX）。
2. 附件加两张（都在仓库里，全画布 1145×1374 透明底 PNG）：
   - `characters/atri-01/master.png` —— 完整原图
   - `characters/atri-01/official-regeneration/raw/near-lock-magenta-v6.png` —— 同一张图，近侧马尾所在
     区域用**品红方带**标出（只是区域标记，不是轮廓）
3. 把 `characters/atri-01/prompts/near-lock-v6-workmode.txt` 的正文整段粘贴进去，发一条，不要追问。
4. 出图后把文件给我（或者放进 `characters/atri-01/official-regeneration/raw/`），我按收件清单验：
   同坐标叠母版、品红/黑底看边、alpha>0 连通块必须为 1、数孤立深色点、单独看形状是否是一根完整自然
   的马尾、按枢轴转到招手最大角看根部。

## 已知失败（不要重复）

同一件用单次 `images/edits` 调用连发三次都不合格，都在 `raw/` 里留档：

| 出图 | 结果 |
|---|---|
| `ponytail-near-complete-09.png` | 交回整片左侧头发（alpha>0 连通块 228，深色点 65，bbox x247–598 / y7–1359） |
| `ponytail-near-complete-10.png` | 仍是大片头发（连通块 158，深色点 71，bbox x295–552 / y51–1231） |
| `ponytail-near-complete-11.png` | 加了品红方带仍是大片头发（连通块 575，bbox x321–672 / y33–1333） |

单次编辑调用复现不了「工作模式」；「工作模式」是模型自己在会话里跑 Python、用遮罩合成并验证遮罩外
像素的代理流程。所以这件必须走网页里的「工作」。

## 收件后我做什么

只做测量、标注、配准（小幅平移）、合成、打包：把这件接回 `scratch/candidates/atri-pure-components-01`
的后层，按母版实测的前景带再合成一次，重新采样、更新记录。不改像素、不拉形。
