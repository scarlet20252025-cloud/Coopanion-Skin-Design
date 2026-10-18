# 这组采样已失效（2026-10-16 近侧马尾第二轮修改之后）

本目录的 104 帧 PNG 与 `samples.json` 采集于候选指纹
`1fef49be289d650f54fb58250726e47b628e3efa8cd30052dc58d7efeedfd0d3`。

近侧马尾已换成完整素材（`raw/ponytail-near-complete-06.png`）、
前景带改为实测的 y 551–978，候选指纹变为
`2ce51915465e7384a57c8874c940d87904bd97360cccc4cdb099d79a98a6569e`。

因此这些帧只能作为改动前的历史证据，不能用来证明当前候选的遮挡与动作表现。
重新采集：在仓库根目录运行
`python characters/atri-01/official-regeneration/pure-generation/collect-review-qa.py <chromium 可执行文件>`
（本机 venv 没有 playwright，本轮未执行）。
