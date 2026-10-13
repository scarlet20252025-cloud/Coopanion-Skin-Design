# 工程约定

- 默认简体中文。先读 README、docs/PRODUCTION_PLAN.md 和角色 brief.json。
- 目标为 Coopanion 原创 Q 版人物分件动画。不要套用 ChatGPT Pets 的动作表、十六方向或 Minecraft 像素 UI 规格。
- 区分来源事实、工程建议和实测结果。资料宣称支持，不等于本项目已验证。
- 每个角色先锁定母版、画布、锚点和分件编号，再扩展表情、换色、服装。
- 当前 GPT 龙娘唯一生产母版为 `characters/original-01/production-lock.json` 指定的 v005；构建前校验 SHA-256。禁止用 v002-v004、旧 atlas 或失败 ORA 当新流程输入。
- 官方参考帧在 `tools-local/whale-reference-91293b3`；优先复用现有 60 fps 帧、时间轴和 WebP，不重复采样。其贴图不进入龙娘分件。
- 静态像素重组一致只验证原位合成；遮挡补全、关节接缝、闭眼过渡和真实运行效果仍需分别验收。
- 保留母版原文件、分层源文件、提示词、遮罩与变换记录；已验收产物不覆盖，改版使用新版本号。
- 默认优先调用当前环境的图像生成/编辑能力；程序仅做明确的配准、遮罩、合成、检验及导出。不要为了生成一张图再搭另一套图像 API。
- 自动分层先做一个小样；失败只修具体部件。相同问题连续两次没有改善时更换方法并记录原因。
- 不重复实现官方 kit 的移动、拖拽与行为系统；需要独立渲染器时先验证 figure-frame 契约。
- 只向 vocab 声明已经实现且检查过的动作；保留发布后的词和装扮 ID。
- 不把官方大肥鱼贴图复制为原创项目资产。采用上游代码时记录版本与对应许可。
- 大型原始素材和外部软件放忽略目录；需要版本化大文件时先设 Git LFS 或 Release 交付方式。
- 最新动作入口为 preview/dragon-r06.html；当前手臂/步态参数在 characters/original-01/rig-v005-r06/motion-config.json，交互姿态在同目录 behavior-config.json。腿部继承 r03，头脸/坐姿继承 r02。只调动作运行 scripts/sync-r06-config.py；禁止调用旧 r04 构建覆盖当前包。待机 idle_strength=0.7、跳跃 strength=0.65 不变。
- r06 修正招手掌心与脚底落点。调动作使用 scripts/sync-r06-config.py，手部差分使用 build-v005-r06.py。原袖子和肩不改，招手结束恢复原手臂。r05 附属配置为微动而非完整拆层物理。
- 对外经验入口 docs/REUSABLE_WORKFLOW.md；同步最新已验证事实、失败原因与边界。宿主 vocab 每项必须有正数 seconds；纯预览通过不可替代实际导入。

- 涉及分件、遮罩、补画、头发/翅膀/尾巴交叠时，先读 docs/LAYER_OWNERSHIP_AND_OCCLUSION.md。检查像素归属和变换父节点，禁止把扩补片或调整层序当作通用修复。先提供完整角色视觉证据，再声明完成。未验收候选不得自动替换当前安装版。
