# 亚托莉 ATRI 桌宠形象 · 工程交接文档（2026-10-16）

接手人先读这一篇，再读 `AGENTS.md`、`characters/atri-01/official-regeneration/STATUS.md`、
`docs/LAYER_OWNERSHIP_AND_OCCLUSION.md`。冲突时以本文与 STATUS 为准；仓库里更早的失败记录、
旧素材取舍、旧配准分数只作历史证据，不要再引用。

## 0. 一句话现状

`scratch/candidates/atri-pure-components-01` 是当前唯一在做的候选（**未安装、未发布**）。
近侧马尾素材已按用户要求还原为旧候选那一层（身份矩阵、后层），手臂层序已修好，
"动作/特效/表情 1:1 复刻鲸鱼娘"仍在进行中（清单见第 6 节）。

## 1. 工程与数据位置

| 内容 | 路径 |
|---|---|
| 仓库（GitHub，main） | https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design |
| 本地工作目录 | `D:\Codex\Coopanion-Skin-Design` |
| 生产入口（纯生成线） | `characters/atri-01/official-regeneration/pure-generation/` |
| 候选包 | `scratch/candidates/atri-pure-components-01/`（`scratch/` 被 .gitignore 忽略，不进仓库） |
| 预览页 | `preview/engineering.html?pack=scratch/candidates/atri-pure-components-01` |
| 动作/表情采样 | `pure-generation/qa/current/`（**当前已失效**，见 STALE.md） |
| 母版（唯一几何权威） | `characters/atri-01/master.png`（1145×1374） |
| 鲸鱼娘复现包（规则与参数来源） | `references/whale-coopanion-repro-kit/` |

启动预览：仓库根目录起静态服务，再开预览页（file:// 会被浏览器拦，必须走 http）。

```powershell
python -m http.server 8765 --bind 127.0.0.1     # 仓库根目录
# 浏览器打开 http://127.0.0.1:8765/preview/engineering.html?pack=scratch/candidates/atri-pure-components-01
```

## 2. 约定的工作模式（必须遵守，来自复现包 docs/07 + docs/08）

1. **美术一律交给模型画**。我们只做测量、标注、上传下载、配准、导入、合成、打包；
   不自己改像素，不用代码描线或纯色补洞，不用代码过滤抠图。
2. 位置偏了只允许**小幅平移**（不动像素）；**不允许拉伸对齐**，比例不对就整张重做。
3. 以**完整原图为输入**，用品红 `#FF00FF` 标区域；一个部件**一条完整提示词一次发出**，
   不合格就把问题写进新提示词另开会话，**不在原会话追问**。
4. 不给模型画目标线、不给轮廓坐标、不描述形状；只写以哪张为原图、包含/去掉什么、为什么必须完整、
   要和哪些已验收件拼得上。
5. 「工作模式」是模型自己在会话里跑 Python、用遮罩合成并验证遮罩外像素的代理流程；
   **单次 `images/edits` 调用复现不了它**（实测见第 7 节）。
6. 收件清单：同坐标叠母版、品红/黑底看边、`alpha>0` 连通块必须为 1、数孤立深色点、
   单独看形状是否完整自然、按枢轴转到最大角度看根部。

## 3. 生产链路（脚本各管一段）

| 脚本 | 职责 |
|---|---|
| `pure-generation/build-diagnostic.py` | 组装候选：把各件按矩阵贴到画布、写 `tex/*.png`、生成 `model.json`（含 `words`）、`figure.js`（由 `renderer-template.js` + `buildFace` 生成）。**绘制顺序 = 挂载顺序**（本渲染器不按 z 排序） |
| `pure-generation/fit-locks.py` | 马尾配准（曲线配准：外缘轮廓对母版剪影）与前景带测量，写 `lock-placement.json` |
| `pure-generation/renderer-template.js` | 运行时：站/坐姿、手势、步态、头发与呆毛弹簧、表情、拎起挣扎、层序 |
| `pure-generation/collect-review-qa.py` | 真实浏览器采样（需要 playwright，本机 venv 未安装） |

改完必须重建候选：`python characters/atri-01/official-regeneration/pure-generation/build-diagnostic.py`
（在仓库根目录跑），然后刷新预览页。

## 4. 当前候选的关键状态

- 候选指纹：`9a73e9ff…6ac1`（每次重建后按 `build-diagnostic.py` 的输出重算，记录见 git 提交信息）。
- 近侧马尾：`raw/pony-pair-left-01.png` + `scratch/asset-candidates-fit.json` 的 `left-library` 矩阵
  （外缘轮廓误差 3.0px），前景段 `clip=(0,545)`；远侧 `raw/ponytail-far-complete-06.png` + `right-current`。
- 层序：后发 0 → 腿 → 远臂 4 → 衣身 5 → 头部头发 6（含蝴蝶结 6.1/6.2、呆毛 8）→ **近臂（挂载在最后，位于所有头发之上）** → 五官组（镜像头部 transform）。
- 已做的修正：
  1. 近臂排在**所有头发图层之上**（挂载顺序修复，`b428689`）；
  2. 后发归属裁剪：`head-clean` 轮廓外 6px、限 y150–520 的薄片削除（`f88646c`）；
  3. `front piece` 不得画在头部头发之上（`1b65c4a`）——**这一条与"上段要覆盖到前景"的旧要求冲突，待用户定夺**；
  4. 词汇表补齐 43 项（`f95a86a`）；挣扎参数对齐（`4cf71cb`）。

## 5. 已验证 / 未验证

**已验证**：预览页可正常渲染；五官与眨眼正常；近臂位于头发之上；后发裁剪后脸侧不再出现空洞；
词汇表与官方 kit 的透传路径打通（`do()` 可到官方特效实现）。

**未验证**：真实动作采样（qа/current 的 104 帧属于改动前指纹，已标失效）；抬手极值时手是否压脸；
特效逐词验收；坐姿与转向下的层序。

## 6. 待办（按优先级）

1. **前景/后景关系**：用户曾要求"上段在蝴蝶结后、头顶头发前"；为消除残留线，当前实现把前景段
   限制在头部头发未覆盖处。需要用户确认最终取向，再做数值级微调（例如只排除出现残留的那几行）。
2. **残留线**：蝴蝶结右侧沿头部弧线仍有并行线（`head-clean` 自己的描边 vs 马尾/后发外缘）。
   方法论：**先量后削**——把该窄带内各层深色线像素数逐层列出，确定归属再动。
3. **特效逐词验收**：`sweat / tear / heart / note / star / spiral / ring / bubble / pointer`
   与鲸鱼娘并排比对时长与位置（特效由官方 kit 绘制，ATRI 已命名 `bubble/gaze/hearts/tear/tears/z` 挂点）。
4. **剩余动作曲线**：`bow / dizzy / jump / hop / spin / shiver` 的时长与恢复曲线对齐鲸鱼娘。
5. **全词汇 1:1 并排验收**：两边同动作截图对照，存证。
6. 重新跑一次真实渲染采样（装 playwright 或用浏览器手动触发页面的「导出左右动作 QA」）。

## 7. 失败与坑（不要再踩）

| 坑 | 后果 |
|---|---|
| 用自己 P 图抠的素材（`complete-ponytails-reextract`） | 素材切割本身有误，内部线条与母版不符，退件 |
| 用代码按母版形体/蝴蝶结遮罩删 alpha | 等于代码抠图，违反工作模式；且整圈 8px 裁剪会把脸侧头发一起削掉，出现空洞 |
| 逐行横向网格变形去对齐外缘 | 就是被否掉的"拉伸对齐" |
| 提示词里写坐标/画目标线/描述形状 | 交回一条细带（`image25-near-lock-v3`） |
| 单次 `images/edits` 出整件（马尾） | 连续三次都交回整片头发（连通块 228/158/575），退件 |
| `fit-locks.py` 的 `cap_hard` 硬约束 | 会让所有初值失败、拟合退化解 |
| 以为 `model.json` 的 z 决定层序 | 本渲染器按**挂载顺序**画，z 不参与排序 |
| `head-blank-01` 的五官区是透空的 | 用距离变换算"轮廓外"前必须 `binary_fill_holes`，否则整脸被当成轮廓外 |

## 8. 出图通道

- 用户 ChatGPT 会员已过期，**网页版「工作」模式当前不可用**。
- 现可用：`https://edge.lingsuan.org/v1` 的 `gpt-image-2.5-sunburst`（`/images/edits`）。
  密钥在环境变量里（注意：本机把它放在 `OPENAI_BASE_URL`，不是 `OPENAI_API_KEY`）。
- 该通道**不适合"整件抠出来 + 透明底"**（实测见第 7 节）；**适合小范围补画/定点编辑**
  （例如"在品红区域内把这根发束被挡住的那一段补出来，区域外不动"）。
- 待交接的下一件美术活：近侧马尾的完整重绘（用户表示将人工手绘修复；若改由模型出，
  材料已备在 `characters/atri-01/prompts/handoff-near-lock/`，含完整原图、品红标区图与自洽任务说明）。

## 9. 交接后第一件事（建议）

1. 起静态服务、打开预览页，按第 4 节的层序与第 5 节的未验证项过一遍，确认你看到的状态与本文一致；
2. 与用户确认第 6.1 条（前景/后景关系）的最终取向，然后按"先量后削"处理残留线；
3. 再做第 6.3→6.5 的特效与动作对齐，每项都在预览页留截图证据。

## 10. 决策记录（2026-10-16，用户确认）

- **前景/后景关系（已定，方案 A）**：副马尾（近侧马尾）**上段覆盖到前景**——压住头顶头发（此前为消除残留线而把前景段限制在头部头发未覆盖处，已撤销）；**下段从发束中段 y=640 起走后层**，显示在发尾下面。实现：`build-diagnostic.py` 的 `NEAR_LOCK_FRONT_CLIP=(0,640)` 且前景段不再排除 head-clean 覆盖区，提交 `ee452de`，候选指纹 `0d2734280d41127b3f0d728c94b8b6ac2e8396896bfd12de01c28480ab2624b5`。
- 用户对该版评价："可以的很完美"，此取向作为后续基线，不要再反复。

