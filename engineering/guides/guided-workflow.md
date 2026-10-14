# 按下一步命令完成一次制作

适合首次接手或上下文较短的模型。基础能力是读写文件、执行命令、查看图像；补画需要可用的图像编辑能力。先按现有角色修复路线走通，做全新角色再读 [新角色入口](new-character.md)。

## 一次准备

Python 3.10+、Node 用于基础工程；自动采样/图像数学另用这个独立环境：

```sh
uv sync --project engineering
uv run --project engineering playwright install chromium
python engineering/tools/project.py doctor
uv run --project engineering python engineering/tools/project.py doctor --workflow
```

已有 Edge/Chromium 可用采样命令的 `--browser <程序绝对路径>`，无需重复下载。依赖版本记录在 `engineering/uv.lock`。不会安装其它绘画软件。没有 uv 时，在自己的 venv 安装 Playwright、Pillow、NumPy，然后用该解释器运行下面命令；CLI 缺依赖会给出修复命令。

Windows 没有 uv 时可直接复制以下替代命令（不要同时走两种安装路线）：

```powershell
python -m venv engineering/.venv
engineering/.venv/Scripts/python.exe -m pip install "playwright>=1.50,<2" "Pillow>=11,<13" "numpy>=2,<3"
engineering/.venv/Scripts/python.exe -m playwright install chromium
engineering/.venv/Scripts/python.exe engineering/tools/project.py doctor --workflow
```

之后将文中 `uv run --project engineering python` 替换为 `engineering/.venv/Scripts/python.exe`。其它平台解释器位于 `engineering/.venv/bin/python`。若需要严格复现锁定版本，使用 uv 路线。

## 1. 创建任务

在仓库根目录运行，任务 ID 换成未使用的短英文名：

```sh
python engineering/tools/flow.py start --job repair-wave --part arm --kind occlusion --request "修复招手时手臂与耳后发的遮挡"
python engineering/tools/flow.py next --job repair-wave
```

`scratch/jobs/repair-wave/TASK.md` 说明该读哪些文件；`scratch/candidates/repair-wave` 是唯一编辑目录。修复任务保留原发布 ID/版本，文件夹名只是隔离名。旧 `project.py candidate` 创建新 ID 的实验副本，用途不同。

`--part` 从 `project.py inspect unknown` 输出中选择，`--kind` 为 `motion`（动作）、`art`（素材）、`occlusion`（遮挡）。别重画与请求无关的部件。中断后只运行 `next`，不要再创建一次。

## 2. 定位并修改

先回答：哪一片像素属于谁、由谁变换、谁遮谁、移动后露出什么。用 `project.py case <关键词>` 查相近失败。`TASK.md` 已给出修改文件和对应指南。

需要配准位移时，以下命令只写候选，自动同步两份 JSON 并保留修改记录：

```sh
python engineering/tools/flow.py registration --job repair-wave --part arm-left --dx -2 --dy 0
```

这是命令示例，-2 不是默认美术答案。`--scale` 为等比增量，`--angle` 围绕源坐标原点；关节 pivot 和配准是不同概念。仅调整肩袖位置通常用 dx/dy。新绘素材先按 [素材辅助工具](asset-tools.md) 检查和配准，再在候选的语义区域接入。

## 3. 检查与自动采样

```sh
python engineering/tools/flow.py validate --job repair-wave
uv run --project engineering python engineering/tools/collect_qa.py --job repair-wave
python engineering/tools/flow.py next --job repair-wave
```

采样工具自行启动隔离本地服务和浏览器、结束后关闭，记录真实 `do` 返回值和 pointer 交互。默认覆盖常见动作、两个朝向、进入/恢复、坐下→开心→站起、跑步→招手→恢复、点击→提起→松手。`--full` 扩展到全部声明动作，耗时和磁盘占用更大。其它适配器若不具备该词表，需定义相应 QA profile，不能忽略缺项。

输出在 `scratch/jobs/repair-wave/qa/`：

- `contact.jpg`、后续编号接触表：每页 12 帧，深浅底并排。
- `frames.json`：动作、朝向、阶段与完整 PNG 对应表。
- `NNN-light.png` / `NNN-dark.png`：完整视口。
- 招手和交互还有 `*-upper.png`：上半身放大，便于看接缝。
- `qa.json` 在任务根目录：覆盖/数值/图片检查及当前文件指纹。

缺帧、空图、动作被拒绝、假提起、非有限数值、资源加载失败会报告失败。现有 `project.py qa` 仅用于读历史采样；新的交付流程使用这里的 schema 2 证据。

## 4. 看图并记下具体结论

先看接触表，再打开有疑点的完整帧和上半身图。按顺序核对全身比例、两种背景、左右方向、缺陷局部、切换恢复。看不到图像的模型把这些文件交给有视觉能力的审阅者；不能通过填写 true 来代替实际看图。

编辑任务内 `review-template.json`：从 `qa.json` 复制 `input_sha256` 到 `qa_sha256`、复制 `pack_fingerprint`；写实际审阅者、具体发现、五项检查、至少两条当前 QA 文件路径（接触表/全身与缺陷局部），结论为 pass 或 fail。`notes` 应指出检查了哪个动作、接缝/遮挡的结果，以及剩余局限。

```sh
python engineering/tools/flow.py review --job repair-wave --file scratch/jobs/repair-wave/review-template.json
```

视觉失败就回到第 2 步。改候选文件后，之前的机器/QA/审阅/ZIP 会自动视为过期。相同问题连续两次未改善，查像素来源和坐标父节点，不继续加大遮罩。

## 5. 打包与实际安装

```sh
python engineering/tools/flow.py package --job repair-wave
```

ZIP 和 SHA256 在任务的 `artifacts`，无需把候选复制到生产包才能打包。包内保留作者、仓库地址、许可。安装按用户实际授权和 [安装交付指南](validation-and-release.md) 执行，先备份明确目标，再导入/重载。

```sh
python engineering/tools/flow.py installed --job repair-wave --directory "实际的 figures/形象ID 目录"
```

该命令只比对文件；宿主画面、点击、拖拽、重启等结果另记，不能把文件相同写成所有交互已验收。发布使用打包回执里的 ZIP；完成后公开下载验 hash。任务可只要求本地候选，按其范围停止。

## 常见卡点

| 输出/症状 | 下一步 |
|---|---|
| Job already exists | 用相同 ID 运行 `next`；不要覆盖目录 |
| Embedded registration mismatch | 使用 `registration` 同步两份配置，或修正候选 model |
| Master hash mismatch | 查是否误用了旧母版；新角色需自己的 contract |
| Browser executable missing | 安装 Playwright Chromium，或传 `--browser` |
| QA stale / Missing current review | 最近修改使旧证据失效，重新采样并看图 |
| Similarity matching error | 重选未修改区域的对应点，禁止用拉伸消除误差 |
| 预览通过而宿主失败 | 查看 manifest、嵌入 model、CSP 和真实安装目录 |

这套流程能减少遗漏和状态混淆。形体、补底归属及自然度仍需视觉判断；自动检查只验证明确可测的项目。
