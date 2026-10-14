# Coopanion 形象制作工程库

面向接手仓库的 AI 和制作者。作者：**Asryto**。先运行现有形象，再按任务读取指南。当前范例是 GPT 龙娘 1.0.2；它是 **Coopanion 桌宠形象包**，在主程序「装扮 → 导入」中安装。

- [形象包 Release](https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design/releases/tag/v1.0.2)
- [Coopanion 官方主程序](https://github.com/Pal-AI-Lab/Coopanion)

本轮可执行流程与验证边界见 [完整性复查](guides/completeness-audit.md)。

## 5 分钟起步

首次制作建议直接进入 [逐步引导](guides/guided-workflow.md)：工具会输出下一步命令，并检测旧证据是否失效。新角色使用 [独立素材与运行骨架](guides/new-character.md)。下面的五分钟路线用于先查看已有形象。

```sh
git clone https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design.git
cd Coopanion-Skin-Design
python engineering/tools/project.py doctor
python engineering/tools/project.py check
npm run preview
```

打开 `http://127.0.0.1:4319/preview/engineering.html`。无需 npm install、图像生成 API、GPU 或绘画依赖。运行 `python scripts/package-pet.py` 生成现有形象 ZIP。

`doctor` 检查可用工具；`check` 检查当前形象契约、资源、词表、配准和文档索引。通过只代表这些项目通过，不代表所有动画帧或目标桌面环境通过。

## 按任务进入

| 要做什么 | 先读 | 第一条命令或入口 |
| --- | --- | --- |
| 接手、判断改哪里 | [当前事实与阶段](current-project.json) | `python engineering/tools/project.py inspect arm` |
| 新形象、从原画开始 | [制作流程](guides/pipeline.md) | 使用 [素材契约模板](templates/asset-contract.json) 锁定新母版 |
| 拆件、抠图、补底、肩袖接合 | [部件与配准](guides/parts-and-registration.md) | `inspect hair` / `inspect ahoge` |
| 表情、招手、翼、坐姿 | [动画与表情](guides/animation-and-expression.md) | `inspect expression` / `inspect seated` |
| 环境和工具选择 | [工具表](guides/tools.md) | `doctor --art` |
| 修具体问题 | [失败案例索引](cases/failures.json) | `python engineering/tools/project.py case ahoge-seam` |
| 动态复核、实际安装、发布 | [检查与交付](guides/validation-and-release.md) | 预览页导出 QA → `qa --input <JSON> --out scratch/qa/review` |
| 做宣传片 | [宣传片流程](guides/promo.md) | `python promo/render.py --samples 1.5,6,12,19,23,28` |

只读取任务需要的一行。历史 `docs/REUSABLE_WORKFLOW.md`、`docs/LAYER_OWNERSHIP_AND_OCCLUSION.md` 保留上下文，但最后的“未安装”等旧段落不是当前状态。

## 减少模型自行判断操作步骤

| 辅助工具 | 解决的问题 |
|---|---|
| `flow.py start/next` | 隔离候选、固定任务范围、中断后继续、给出下一步 |
| `flow.py registration` | 等比调整与两份配准同步，避免漏改 model |
| `asset.py inspect/register` | alpha/画布检查、对应点等比解算、叠图与误差报告 |
| `collect_qa.py` | 自动打开隔离预览，检查动作、恢复、双朝向和真实 pointer 流程 |
| `flow.py review/package/installed` | 绑定当前文件指纹，拒绝过期证据，打包和安装文件比对 |
| `layered.py` | 使用新角色自己的素材/锚点生成基础适配器和独立检查 profile |

详细命令均在 [逐步引导](guides/guided-workflow.md)，无需先读脚本实现。图层语义、补画形体和自然度仍要看图判断；检查通过不等于审美通过。基础新角色模板的能力边界见 [新角色入口](guides/new-character.md)。

## 给其他 AI 的接手提示

```text
在本仓库接手 Coopanion 形象工作。先读 AGENTS.md、engineering/README.md
和 engineering/current-project.json，运行 project.py doctor/check。
按任务读取相关 guide，用 inspect/case 找实际修改点和已知失败。
先给出问题区像素归属、父变换、遮挡关系，再选择修法。
修改后提供完整角色、问题区放大、深浅背景和动作切换证据。
机器检查、视觉抽查、用户接受、原生宿主检查分别报告。
不要调用历史 r04/r06 构建覆盖 r25，也不要把本角色坐标照搬给新角色。
```

支持技能的 AI 可读取 [coopanion-image-pack](../.agents/skills/coopanion-image-pack/SKILL.md)。不支持技能的 AI 直接用本页即可。

## 更高效的记录方式

工程库使用四种互补记录：短入口负责路由，机器可读事实负责定位，失败案例负责判断，可执行检查负责证明。每次变更只新增一份 [变更报告](templates/change-report.json)，链接其源图、矩阵、采样和结论；避免复制整篇旧教程造成版本漂移。影像与报告引用具体文件和版本，测试不了的项目写 `not-tested`。

当前贴图哈希快照见 [asset-inventory.json](asset-inventory.json)，不是对所有像素的美术保证。原始生产源见 [source-assets.json](source-assets.json)。运行期需要的所有资源都在 pack；重做局部素材时才读取原始源。

## 本次验证记录

[交接检查](evidence/handoff-validation.json)记录干净源码复核、7 个契约测试、84 张动作采样与发布 ZIP 字节一致性；[预览接触表](evidence/preview-qa.jpg)供快速视觉浏览。
