# v005-r06：掌心差分与走跑脚底修正

使用 v005 唯一母版，继承 r04 分层与 r05 小幅附属动态。待机弹性 0.7、跳跃 0.65 保持不变。

- 招手独立生成掌心朝外手臂，仅配准并取 wave-mask.json 指定手部区域；袖子和肩原像素保持不变。抬手换差分、落手恢复。
- 走跑不再直接用腿段夹角大幅旋转靴子；分别配置步幅、抬脚、有限转角，补偿旋转造成的鞋底偏移。跑步手臂后摆。
- 预览 QA 使用 960px 固定舞台和指定起终点，避免随机短行程。80 张抽样涵盖 walk/run/wave/jump；接触表和 timeline 在 qa-limbs。

修改 motion-config.json 后运行 scripts/sync-r06-config.py；手部生成结果或遮罩改动后运行 scripts/build-v005-r06.py。secondary-config.json 在 r05 源目录；局部柔性效果不等于完整拆层物理，坐姿不启用。

本版腿部仍为刚性可见腿/靴分件，没有膝踝独立弯曲，不宣称已复刻官方所有动作。美术与自然度仍需用户验收。

完整方法、失败与迁移步骤见 docs/REUSABLE_WORKFLOW.md。内置 imagegen edit 模式生成 wave-arm-edit.png，提示词见 prompt.txt，遮罩和配准见 wave-validation.json。

源记录：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design/tree/main/characters/original-01/rig-v005-r06
本包入口 figure.json，按宿主 API 2 加载。
0.6.1：修正跑步手臂被身体遮挡的层序；连续跑停招手 40 张抽样回看通过。

0.6.2：0.6.1 的近手完全被长发/翅膀吞掉，原验收有误。现区分近远臂，以躯干/衣裙遮挡路径保留近手自然露出；新增 qa-layer-v062 检查证据。
