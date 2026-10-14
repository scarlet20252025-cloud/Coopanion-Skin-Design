# 工程约定

- 默认简体中文。先读 `engineering/README.md`、`engineering/current-project.json`，按任务读取对应指南；事实以当前文件和实测为准。
- 目标为 Coopanion API 2 桌宠形象包，不套用 ChatGPT Pets、Cubism 或 Minecraft 规格。作者 Asryto，当前 GPT 龙娘 1.0.2，生产入口 `packs/gpt-dragon-v005-r25`。
- 起步运行 `python engineering/tools/project.py doctor` 和 `check`；`inspect <part>` 定位部件，`case <id>` 查失败经验。可复用技能为 `.agents/skills/coopanion-image-pack/SKILL.md`。
- 首次接手优先 `engineering/guides/guided-workflow.md` 与 `flow.py start/next`。新角色用独立 spec/profile 和 `layered.py`，不继承龙娘坐标。自动采样使用 `collect_qa.py`，审阅绑定当前文件指纹；`next` 提示过期证据时重新采样和看图。
- 用 `preview/engineering.html` 预览生产包或隔离候选。默认打包 `python scripts/package-pet.py`。旧 r04/r06 构建和同步命令只供历史研究，禁止覆盖 r25。
- 当前唯一母版以 `characters/original-01/production-lock.json` 的哈希为准；旧 atlas、失败 ORA 和旧身体不能作为新流程输入。新角色另锁母版、画布、坐标、锚点和归属，不照搬龙娘坐标。
- 图像生成/编辑用于新绘像素；程序用于配准、遮罩、合成、检查及导出。保留实际输入、原始输出、遮罩和变换；相同问题连续两次没有改善，先诊断方法，不盲目堆补片。
- 涉及分件、遮罩、头发、翅膀和尾巴交叠时，先读 `docs/LAYER_OWNERSHIP_AND_OCCLUSION.md` 及部件指南。明确像素归属、父变换、遮挡顺序，再修复。不能用旧轮廓垫底、拉伸手臂或通用覆盖片掩盖错误。
- 招手中耳朵与耳后头发在手臂后，脸旁前发仍在手臂前；后发和头使用一致变换。肩、袖口及手连续自然，不把袖口做空洞。
- 保留连续刘海与独立刚性呆毛，清理根部实际残线，不截掉造型。当前坐姿沿用原形体，晕坐只自然放下两边手臂，不恢复被否决的鸭子坐/加长四肢方案。
- 待机 `idle_strength=0.7`、跳跃 `strength=0.65` 保持用户基线。发布后词表和形象 ID 稳定；每项 vocab 必须有有限正数 `seconds`。
- 使用官方 kit 的行为和真实 `do/pointer/step` 契约。提起后使用 `drop`；不能凭视觉位移声称宿主交互通过。眉毛、表情及翅膀分别检查过渡与恢复。
- 配准维护 `part-registration.json` 并同步嵌入 `model.json`；宿主 CSP 下不能额外 fetch 配准文件。静态重组相同只证明原位合成，不证明动态接缝正确。
- 检查至少包含完整角色、局部放大、深浅背景、两个朝向和动作切换。机器契约、视觉采样、用户接受、原生宿主分别报告；有限采样不冒充全帧验收。
- 候选放 `scratch/candidates`，不自动替换用户安装版或发布。当前用户已明确授权的更新范围优先；同版本覆盖仅在明确授权时做，并记录旧/新哈希和公开下载验证。
- 保留作者、仓库地址、上游版本与许可；不复制鲸鱼娘贴图作为原创资产。运行文件及必要生产源版本化，失败大图、原始下载、临时帧和本机备份保持忽略。
- 原生安装需确认实际目录、逐文件比对、重新加载当前形象；测试不了的多屏/DPI/重启写明未测。旧 docs 中的阶段记录是历史证据，不覆盖当前工程事实。
- 宣传片采用 SVG 场景、当前实际角色纹理/动画、用户指定线性运动。逐帧截图后 FFmpeg 编码，再检查编码成片和音乐；示例气泡不声称真实模型回应。
