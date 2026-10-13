# v005-r03：跳跃腿部增量修正

唯一母版仍为 v005，SHA-256 由 ../production-lock.json 固定。r02 的头部、眼睛、坐姿直接复用。

## 修改入口

- `leg-config.json`：屏幕左右腿的原画坐标遮罩、靴子边界、锚点、旋转角度、抬腿距离、阶段时间。改此文件后运行 `.venv/Scripts/python.exe scripts/build-v005-r03.py`。
- `left-mask.png` / `right-mask.png`：构建导出的可视遮罩；权威源为 JSON 内多边形和矩形。
- `leg-left.png` / `leg-right.png`：直接取自 v005 的原画像素；不单独缩放。
- `skirt-underpaint-edit.png`：使用内置 imagegen，仅一次生成，完整提示见 `prompt.txt`。运行时只使用两腿遮罩区域中的裙内衬补全。
- `packs/gpt-dragon-v005-r03/figure.js`：官方 kit 负责起落轨迹；本角色补预备压低、空中收腿、接地前伸腿、落地缓冲。
- `preview/dragon-r03.html`：可定位 60 fps 时间步的跳跃帧、暂停、下载 PNG；针对 jump/hop 导出检查帧。

## 验证与边界

静态腿层重新组合与原身体层逐像素一致；眼睛、头和配色没有重新生成。浏览器检查记录位于 qa/report.json 与 contact 图。

当前为裙下可见腿和靴子的刚性旋转/平移；没有独立膝关节网格。手臂配合、完整步态、连续坐下差分过渡及实际桌面客户端导入仍未完成。

## 减少返工

先确认具体缺陷及影响部件，再改遮罩/参数；只有缺少被遮挡的画面才局部生成。每次仅构建受影响的 r03 腿部，复用 r02 眼睛与姿势。原始 60 fps 官方参考帧直接读取，不重复采样；检查输出只版本化接触表、时间轴和结论，逐张 PNG 留本地。
