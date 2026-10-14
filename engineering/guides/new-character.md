# 全新角色：先备齐素材，再生成运行骨架

龙娘的 1254px 坐标、39 个词、衣裙遮罩和弹性不是通用规格。新角色使用自己的图片、锚点与 profile。`layered.py` 把准备好的原位分层素材编译成可预览、可采样、可打包的 API 2 候选，减少从零写宿主接口的工作。

## 必需输入

1. 完整原画 RGBA PNG，并记录作者、来源和用户选定结果。
2. 同画布原位图层：头部、躯干/衣裙、双腿、完整肩袖手；需要前后遮挡的耳朵/头发可继续拆为 fixed 图层。透明背景，不把被移走的旧肢体残留在 body。
3. 头部表情差分：开心、晕乎、被提起、闭眼。像素坐标不漂移，差分外区域保持一致。
4. 坐姿、晕坐的身体素材，先依据整体人物设计再分离。明确头部是否共用同一位置；不能共用时分别提供该 pose 的 head 图层。
5. 上半身封面 PNG；脚底位置、人体中心线、边界、点击圆、眼部/气泡锚点。

图像编辑用会话实际可用的工具及 [定点提示词](../templates/image-edit-prompt.md)。模型无图像编辑能力时，先交付明确的素材请求和已完成工程，不将几何测试图称为成品原画。源素材用 [asset 工具](asset-tools.md) 检查和等比配准。

## 配置与生成

把 [new-character.json](../templates/new-character.json) 复制为 `characters/my-character/spec.json`。替换所有路径、署名和 null；null 会让构建失败，避免模型误用一组看似可用的龙娘坐标。

字段说明：

| 字段 | 如何取得 |
|---|---|
| center_x / feet_y | 原画中心线与脚底的源像素坐标 |
| logo_scale | 原画到 kit 256 单位空间的等比比例；先用 `220 / 角色可见高度`，再检查边界 |
| bounds | `[左,上,右,下]`，从完整人物 alpha 边界测量 |
| hits | `[圆心x,圆心y,半径]` 数组，放在实际头/身体内部，不能全覆盖透明空白 |
| anchors.gaze / bubble | 原画眼部中心、气泡起点；可补 z/tear/hearts，长度按官方 kit 约定 |
| part.pivot | 该部件实际关节，用源像素；不是图片中心 |
| part.z / wave_z | 小值在后，大值在前；wave_z 可在招手时换层 |
| part.poses | standing、seated、dizzy 中哪些姿态显示该层 |
| role | fixed/head/wave-arm/wing/leg；会动的角色需要对应 motion 参数 |
| motion | wave-arm 为 degrees/swing；wing、leg 为 degrees/hz（腿可加 phase） |
| owner / reveals_when_moved | 谁的像素，以及移开后应露出谁；无隐藏区填 none |

```sh
uv run --project engineering python engineering/tools/layered.py --spec characters/my-character/spec.json --job my-character-first
python engineering/tools/flow.py validate --job my-character-first
uv run --project engineering python engineering/tools/collect_qa.py --job my-character-first
python engineering/tools/flow.py next --job my-character-first
```

生成器先校验输入，再创建隔离候选；原图和生产目录保留。候选包含自己的 manifest、model、词表、配准、作者/仓库说明和许可；任务目录保存独立母版锁、贴图清单、来源哈希及 contract。新 profile 不要求龙娘的 39 个词或肩部坐标。接下来按 [引导流程第 4 步](guided-workflow.md) 看图、打包、实际安装。

模板提供 11 个基础词：neutral/happy/stand/wave/walk/run/jump/sit/dizzy/turn/dance。点击、拖拽、落地和官方粒子交给 kit；自绘表情由你提供的差分负责。不要给缺少美术实现的更多表情批量加词。

## 模板的边界与升级入口

这是刚性图层基础模板。复杂头发连续变形、立体翼、衣裙、坐姿转场、眼眉独立驱动需要在候选 `figure.js` 进一步适配。当前模板以坐下程度 0.5 切换姿态；若切换可见，应设计角色自己的过渡，不能将基础模板通过当成自然度通过。

先让单个关节和两个方向正确，再添加网格/次级运动。耳后发、前发若共用一张头部图但需要位于臂的两边，须拆出正确的源层，使用相同头部变换。配准矩阵不会自动解决语义遮挡。

工程提供 `engineering/tests/make_layer_fixture.py` 的几何夹具来验证编译器和宿主契约。它是测试图，不是可发布角色，也不能证明任意新原画能自动达到龙娘的完成度。
