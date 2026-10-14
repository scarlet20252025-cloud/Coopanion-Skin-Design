> 历史制作记录：其中阶段状态和旧命令不代表当前发布版。接手请先读 [工程库](../engineering/README.md)、[当前事实](../engineering/current-project.json) 与 [Release 回执](github-release-v1.0.2.json)。

# 工具与 Skill 选型

核对日期：2026-10-13。以下状态更新到 r06：内置图像编辑、Python 原位素材流水线、官方 kit 预览和运行中 Coopanion 导入已使用；未使用 See-Through 或 PSD2Live 制作本角色。

## 主线路

| 工具 | 用途与选择理由 | 当前状态 |
| --- | --- | --- |
| 当前会话 imagegen | 母版、遮罩局部补画、表情差分；复用现成入口 | 已用于母版、局部补画和招手掌心差分；提示词/遮罩随版本保存 |
| [Krita](https://docs.krita.org/en/user_manual/animation.html) | 可编辑图层、遮罩、补缝与 PSD 交换 | PATH 未发现；尚未确认 GUI 安装位置 |
| [See-Through 官方](https://github.com/shitagaki-lab/see-through) / [用户提供的魔搭入口](https://modelscope.cn/studios/ljsabc/See-Through) | 单母版自动分层候选，减少手动初拆 | 官方说明已读；魔搭页面内容未能由文本抓取读取，服务可用性未验证 |
| [OpenCV](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html) + NumPy | ECC 配准、遮罩和漂移检查 | 项目 .venv 已验证；用 .venv/Scripts/python.exe，勿混用系统解释器 |
| [Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) | RGBA 合成、裁剪元数据、接触表、导出检查 | 项目 .venv 已验证；用 .venv/Scripts/python.exe，勿混用系统解释器 |
| Coopanion kit / rig | 行为复用和分件变形，目标平台一致 | 已按固定版本复制 kit 至 preview/vendor；开发包使用实际宿主 kit |
| Git + Python + Node | 版本记录、图像处理、轻量预览 | 已在 PATH 检出 |

默认不装完整模型训练环境。先用自动分层服务试验；只有质量通过且确有批量需求时，再评估本地 See-Through 的 GPU 与依赖开销。外部服务的上传和本地图像生成是不同步骤，实际使用前明确选用哪一个。

## 用户提供的 Live2D 工具

| 项目 | 已核验能力 | 在本工程的位置 |
| --- | --- | --- |
| [Auto_Vtb_beta](https://github.com/lTwTlol/Auto_Vtb_beta) | README 描述 PSD 自动绑定、物理、Cubism 工程与运行文件导出；Release 有 Windows ZIP | 快速试验备选；不是 Coopanion 导出器 |
| [PSD2Live 原作者项目](https://github.com/tsunehimatoi/psd2live) | 当前 README 描述可编辑工程、Cubism、p2lrt、分层 PSD 与序列帧等输出 | 优先跟踪原作者维护版本；后续确需 Live2D 时单独验证 |

已发现 Auto_Vtb `v0.2.4.beta` 的 [Auto_Vtb_2.4_beta.zip](https://github.com/lTwTlol/Auto_Vtb_beta/releases/download/v0.2.4.beta/Auto_Vtb_2.4_beta.zip)，约 77.5 MB（十进制）；仅核验发布资产，未下载/解压/启动。用户给出的 09.22 经验作为参考，具体能力以选定版本实测为准。

首轮比较只用同一份 PSD，检查中立姿态、眨眼、张嘴、发梢、裙摆和腿部。记录人工调整时间；选一个保留，不同时维护两套自动绑定工程。PSD2Live 侧别使用角色自身左右；输入口型建议有完整张口图，上睫毛与下眼线分开。

## Skill 搜索结果与取舍

采用用户指定的 [find-skills](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) 流程：先看 skills.sh，再运行 `npx --yes skills find "sprite animation"` 与 `npx --yes skills find "character design"`，并读取候选 SKILL.md、核验源码仓库。

下表为查询时快照，安装数与星数会变化；它们不是质量实测。

| Skill | 查询快照 | 结论 |
| --- | --- | --- |
| vercel-labs/skills@find-skills | 榜单约 3.8M 安装；源仓库 34,071 星 | 本次用于发现与筛选；已在线读取，无需为搜索再装一套工具 |
| 当前自带 imagegen | 本地已有说明及工具 | 主流程使用；无需另装图像生成 Skill |
| [openai/plugins@sprite-pipeline](https://skills.sh/openai/plugins/sprite-pipeline) | CLI 43 安装；官方源仓库 7,421 星 | 已读源码：从确认帧生成整条动画、共享缩放与锚点。适合特殊逐帧动作，暂不安装 |
| [omer-metin/skills-for-antigravity@pixel-art-sprites](https://skills.sh/omer-metin/skills-for-antigravity/pixel-art-sprites) | CLI 约 2.5K 安装；源仓库 165 星 | 已读源码，偏像素画；与当前非像素 Q 版分件路线不匹配，不采用 |
| frontend-design / PixiJS 类结果 | 搜索可见 | 分别偏网页外观或引擎使用，不能直接解决母版一致性与拆件，排除 |
| ChatGPT work-pets | 当前环境可见 | 目标是 ChatGPT Pets；与 Coopanion 契约不同，不采用 |

若未来确需安装：

```powershell
npx skills add vercel-labs/skills --skill find-skills
npx skills add openai/plugins --skill sprite-pipeline
```

先检查 CLI 当前帮助及实际安装目录。`sprite-pipeline` 引用了其插件内共享 scripts 与 references，单拷贝 SKILL.md 不够；安装后必须核对相对依赖齐全。这些命令本轮未执行。

本阶段不新增专用 Skill：先完成一个真实角色，再把经过验证的分层映射、导出命令和返工规律提炼成项目 Skill，避免固化尚未验证的流程。
