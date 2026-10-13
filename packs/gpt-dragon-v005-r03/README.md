# GPT 龙娘 v005-r03 开发包

入口 `figure.js` 的 `createDragonBody(base, opts)`；依赖宿主官方 kit API 2。所有角色贴图来自本仓库锁定的 v005 及局部差分，不包含官方鲸鱼娘贴图。

本轮加入裙下双腿与靴子独立旋转、平移，以及跳跃/小跳的压低、收腿、伸腿和落地恢复。原位头部、三档眨眼、独立坐姿与睡眠继承 r02。未实现完整膝关节、手臂配合和步态；坐姿仍是差分切换。实际 Coopanion 客户端导入尚未测试，不能视为正式成品包。

开发预览：仓库 `node scripts/serve.mjs`，打开 `/preview/dragon-r03.html`。腿参数源：`characters/original-01/rig-v005-r03/leg-config.json`，修改后运行 `.venv/Scripts/python.exe scripts/build-v005-r03.py`，再刷新页面。原画、遮罩、ORA、提示词与检查图均保留。

检查：`node scripts/check-production.mjs` 校验母版和静态契约；浏览器“检查跳跃修正”导出两个动作各 24 张（间隔 3 个 60 fps 时间步）检查图。PNG 与逐帧时间轴分别用于视觉和阶段核验，不代表所有组合都已测试。

预览内使用的上游 kit 原始代码、固定 commit 和 AGPL-3.0 许可位于 `preview/vendor/source.json` 与 `preview/vendor/LICENSE`。
