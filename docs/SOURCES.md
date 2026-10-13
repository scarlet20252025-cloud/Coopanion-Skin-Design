# 来源与版本

核对日期：2026-10-13。以下为公开文档/源码核验，不代表软件已经本机实测。

## Coopanion

研究基线提交：`91293b3e31b94397a8f2eb79dffec40f4c6d8817`。

- [官方鲸鱼娘经验](https://github.com/Pal-AI-Lab/Coopanion/blob/91293b3e31b94397a8f2eb79dffec40f4c6d8817/packages/cortico-world-desktop-pet/examples/whale/README.md)：母版编辑、分件配准、共用几何、坐姿差分、五官复用和自定义绘制接口。
- [形象包规格](https://github.com/Pal-AI-Lab/Coopanion/blob/91293b3e31b94397a8f2eb79dffec40f4c6d8817/packages/cortico-world-desktop-pet/README.md)：`manifest: 2`、`api: 2`、`entry`/`export`、词表、打扮维度、沙箱加载和导入。
- [kit body](https://github.com/Pal-AI-Lab/Coopanion/blob/91293b3e31b94397a8f2eb79dffec40f4c6d8817/packages/cortico-world-desktop-pet/web/kit/body.js)、[rig](https://github.com/Pal-AI-Lab/Coopanion/blob/91293b3e31b94397a8f2eb79dffec40f4c6d8817/packages/cortico-world-desktop-pet/web/kit/rig.js)：下一阶段适配前的代码核对入口。
- [第三方资产声明](https://github.com/Pal-AI-Lab/Coopanion/blob/91293b3e31b94397a8f2eb79dffec40f4c6d8817/packages/cortico-world-desktop-pet/THIRD_PARTY_NOTICES.md)：大肥鱼贴图不在包的 AGPL 授权范围；工程学习制作方法，原创素材自行制作。
- [Cortico](https://github.com/Pal-AI-Lab/Cortico)：Agent 框架，皮肤制作以 Coopanion 桌宠包为准。

适配时必须重新核对目标安装版本。形象包根目录包含 `figure.json`，自定义 id 不与 `coo`、`whale` 冲突；官方当前导入上限为 128 MB。读取图片使用沙箱提供的 `loadImage`，不依赖外部 CDN。

## 自动分层与绑定

- [See-Through 原作者仓库](https://github.com/shitagaki-lab/see-through)：单张动漫人物图分解为语义层并补全遮挡，论文方案可提供最多 23 层；绑定不属于该项目自动完成的部分。
- [用户提供的 ModelScope 服务](https://modelscope.cn/studios/ljsabc/See-Through)：入口已记录；可用性与产出待实测。
- [Auto_Vtb_beta](https://github.com/lTwTlol/Auto_Vtb_beta/tree/dd1342d19cdf497aaf2ffff6cd8df25e6ad3b670)：核验时 main 提交 `dd1342d19cdf497aaf2ffff6cd8df25e6ad3b670`。
- [Auto_Vtb PSD 图层规范](https://github.com/lTwTlol/Auto_Vtb_beta/blob/dd1342d19cdf497aaf2ffff6cd8df25e6ad3b670/docs/zh/PSD_LAYER_SPEC.md)：命名、左右侧、眼部/嘴部的拆分与 RGB/8 位输入要求。
- [PSD2Live](https://github.com/tsunehimatoi/psd2live)：原作者项目，当前 master 文档支持的目标比用户分享摘要更广；不推断每个输出都已适配 Coopanion。

## Skills

- [find-skills 固定版本](https://github.com/vercel-labs/skills/blob/13e4063a1cf913f5606d57d42ab83a86f5001e04/skills/find-skills/SKILL.md)。
- [sprite-pipeline 固定版本](https://github.com/openai/plugins/blob/0722921d5542fc593105c27bd52630babd8b8c2a/plugins/game-studio/skills/sprite-pipeline/SKILL.md)。

官方描述、工程选型、已完成本机验证分别在本文件、PRODUCTION_PLAN.md、TOOLS.md 中记录。不要把建议的 1024 母版、阶段预算或小样策略当成官方强制规格。
