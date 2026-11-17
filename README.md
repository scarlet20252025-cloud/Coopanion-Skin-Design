# 黑金魔女 · Coopanion 桌宠工程

当前工程包含朝右透明母版、生成供体、提示词、原坐标分层、模型、运行贴图、预览与验收工具。受控重建从归档供体开始，无需联网生成同一张图。以其他角色制作新稿时，可照[制作与复现手册](docs/制作与复现手册.md)重做美术并建立自己的定位点。

[桌宠工程通用手册](docs/桌宠工程通用手册.md)汇总此前验收的星云 v1/v2、星眠与黑金魔女做法，包含拆件铁律、拎起惯性和低位齐掌、独立坐姿、三轴头部、倾听、摆尾以及对侧步态。[案例代码与工具索引](docs/案例代码与工具索引.md)可查正式版本的实现、提示词与复现入口。

当前版本 **0.1.2**。拎起沿用星云 v2 的弹性余摆；眩晕在坐下的同一帧启动圈眼与星星，随后摇头恢复；后裙底部绘制在腿后；站姿转头和抬低头有局部眼口视差。[动作回归](review/preview-qa.json) · [裙摆层序对照](review/skirt-leg-depth.jpg)

## 直接打开预览

安装 Node.js 24，在本文件所在目录执行下列命令。无需 `npm install`。

```powershell
node .\serve.mjs 4334
```

打开 [黑金魔女本地预览](http://127.0.0.1:4334/)。单击动作按钮，也可直接用鼠标拎起并放下角色。切换深色底检查发尖、帽坠和裙边，按「原位站姿」固定头身作母版对照。改 `parts/` 内原画布的对应透明 PNG，或重建贴图后，预览会自动重新加载素材。改 `preview.js` 或 `preview.html` 后刷新页面。预览服务只监听本机。

站姿倾听时头部沿颈轴倾斜，身体保持直立。坐姿使用独立画稿，倾听时保留原坐姿。浏览器已跑过动作与表情回归，Coopanion 原生客户端的导入与多显示器表现仍待验证。[浏览器验收](review/preview-qa.json)

## 重建、检查、打包

以下环境验证过 Windows、Python 3.14、Node.js 24 与 Edge。安装包及工程包由 `pack/star-witch/figure.json` 中的版本号命名。先保留已验收原件的副本。重建会重新生成 `parts/`、模型和运行贴图。

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 assemble_left_arm.py
.\.venv\Scripts\python.exe -X utf8 assemble.py
.\.venv\Scripts\python.exe -X utf8 assemble_expressions.py
.\.venv\Scripts\python.exe -X utf8 review_parts.py
.\.venv\Scripts\python.exe -X utf8 review_portraits.py
.\.venv\Scripts\python.exe -X utf8 package_project.py
```

服务运行时可在另一个终端执行 `node .\qa_preview.mjs`。此检查使用 Edge，路径可用 `WITCH_EDGE` 指定，地址可用 `WITCH_PREVIEW` 指定。报告写入 `review/`，需配合截图和真实速度预览验收。

打包输出到 `dist/`，两份 ZIP 各有 SHA-256 校验文件。

- `star-witch-<版本>.zip` 用于 Coopanion「装扮 → 导入」。ZIP 根目录包含 `figure.json`，只打包被运行时引用的文件。
- `star-witch-<版本>-engineering.zip` 用于编辑和完整重建。解压后进入 `star-witch/` 目录，按本页命令运行。交接包内的脚本也能重新生成两个 ZIP。

本工程署名 Asryto，现行源文件发布在 [Coopanion-Skin-Design](https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design)。预览所用 Coopanion kit 固定在上游提交 `91293b3e31b94397a8f2eb79dffec40f4c6d8817`，快照与 AGPL 许可证随工程提供。[上游项目](https://github.com/Pal-AI-Lab/Coopanion) · [快照说明](vendor/Coopanion-web/SOURCE.txt) · [许可证](LICENSE)
