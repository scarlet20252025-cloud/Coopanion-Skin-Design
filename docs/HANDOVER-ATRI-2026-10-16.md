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
词汇表与官方 kit 的透传路径打通（`do()` 走官方 `doWord`，动作与表情都生效）；
图侧特效层已完成并逐项看过（见第 11 节）。

**未验证**：真实动作采样（qа/current 的 104 帧属于改动前指纹，已标失效）；抬手极值时手是否压脸；
特效在坐姿以外状态下的逐帧时长相较；坐姿与转向下的层序。

## 6. 待办（按优先级）

1. **前景/后景关系**：用户曾要求"上段在蝴蝶结后、头顶头发前"；为消除残留线，当前实现把前景段
   限制在头部头发未覆盖处。需要用户确认最终取向，再做数值级微调（例如只排除出现残留的那几行）。
2. **残留线**：蝴蝶结右侧沿头部弧线仍有并行线（`head-clean` 自己的描边 vs 马尾/后发外缘）。
   方法论：**先量后削**——把该窄带内各层深色线像素数逐层列出，确定归属再动。
3. **特效时长并排比对**：官方 kit 只画自己的粒子（`z / heart / dust / note / drop`），
   其余特效标记由 figure 自绘（见第 11 节，已实现）；待做的是与鲸鱼娘并排量时长与出现时机。
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

## 11. 图侧特效层 + 大哭重做（2026-10-16，用户反馈"期待/拎起没特效""大哭太丑"）

**根因**：`preview/vendor/kit/body.js`（与官方发布包**逐字节一致**，`03520bb8…`）只在 `FACES` 表里
**声明**特效标记（`sparkle / sweat / anger / orbit / bang / question / listen / think / streams`），
文件内**从不消费**它们——官方做法是**由 figure 自己画**。官方鲸鱼娘 figure 的三处实现即：
`drawFx()`（汗滴／怒筋／问号／感叹号／晕乎星／倾听弧／思考泡）、`paintOpenEye()`（期待＝虹膜上的闪烁星，
官方词条写"眼睛里闪着星星"）、`paintStreams()`（大哭泪流）。ATRI 渲染器此前**整层缺失**，
所以"按了没反应"；而 kit 自己的粒子（难过泪滴、爱心、音符、睡 z、尘土）一直是好的。

**实现**（`renderer-template.js` 的 "figure-side effects" 段）：
- 位置用**官方数值**（kit logo 单位：x=128 在身体中线、脚底 y=256），再按 ATRI 自己的
  `logo_scale / center_x / feet_y` 换算，不靠目测；`probes/check-fx-clearance.py` 验证六个挂点在本包
  合成图上都是空白画布（alpha=0，PASS）。
- 尺寸 = 官方数值 × 一个 logo 单位对应的 master 像素。坐姿偏移沿用 `anchors` 的既有约定
  （dx −3 / dy +298，**单位是 master 像素**）；曾经误加成 logo 单位，导致坐姿特效落到 y≈1707（已修）。
- 期待星：两枚白色四角星画在虹膜上逐帧闪烁，用该眼贴图自身 alpha 做 mask，只在"睁眼"贴图显示时出现
  （闭眼自动消失）。虹膜中心**实测**（`probes/measure-iris-centre.py`，四张睁眼贴图）。
- 腮红：官方 figure 会画径向渐变腮红，但 ATRI 的成品脸贴图**自带腮红**
  （`tex/head-clean.png` 在 (556,544) 采样 rgb(252,206,195)），再叠一层会糊掉已验收的颜色 → 不画。
- 词汇表 1:1：补上官方有而 ATRI 缺的 6 个词（`sleepy 犯困 / thinking 思考 / pout 嘟嘴 /
  determined 认真 / cry 大哭 / flap 扑腾`），`figure.json.vocab` 37 项、`model.words` 49 项。
  **坑**：渲染器 `do()` 以 `model.words` 为准，只加 `vocab` 不加 `words` 会 `accepted:false`。

**大哭重做**：kit 的 `drop` 粒子是一整枚 logo 单位的泪滴（18.5×12 logo，与官方鲸鱼娘同尺寸）；
ATRI 的眼宽只有鲸鱼娘的约 45%，泪滴挂到眼睛上会盖住整张脸（试过单滴在近眼角，同样盖脸）。
改为：**细泪流**从每只眼下眼睑出发（官方 `paintStreams` 的锥形形状，方向指向挂点），
**泪滴挂到头部两侧**（`anchors.tears=[455,600,845,580]`）落在头发/背景上，脸完全露出。
单滴表情（难过/担心/慌张/害怕）保持原挂点 `tear=[719,509]` 不动 —— 见 `build-diagnostic.py` 注释。

**并排佐证**：`scratch/fx-shots/` 下留有预览页截图（期待星、生气怒筋、慌张/被拎起汗滴、晕乎三颗星、
疑惑问号、惊讶感叹号、大哭泪流＋两侧泪滴）；官方鲸鱼娘预览页
（`references/whale-coopanion-repro-kit/assets/shipped/preview-pkg/examples/whale/index.html`，
用同一个 8765 服务直接打开）截图证明官方泪滴尺寸一致、只是它脸大所以不盖脸。

### 11.1 嘴型（2026-10-16，用户："大哭丑更重要的原因是嘴型"）

官方鲸鱼娘的脸表把 cry 映到**它的惊讶嘴 ×0.8**（`MOUTH.cry = ['surprised_mouth', .8]`），所以大哭应该是
"惊讶的张口"缩小一点，而不是原先那条波浪糊块。现在 `expression-face.js` 的 `key` 先把 `cry` 路由到
`surprised` 嘴并加 `mouthScale=.8`（`styles.cry` 那条波浪已删，路由后不可达）。
**DOM 验证**：大哭 → `data-mouth-style="surprised"` + `transform=… scale(0.8 0.8)`；平静 → `neutral`；
惊讶 → `surprised`（同一形状，用户已验收过 惊讶，所以大哭的嘴就是它缩小版）。

### 11.2 眉毛（2026-10-16，用户："负面表情的眉毛没有变化"→"没动画"→"已解决"）

根因不是看不见，而是**可见段不位移**：`brow-mask`（刘海之间的额头皮肤）把眉线切成碎段，而 sad/angry 的
外端/内端位移在可见的中段几乎互相抵消（实测中段只位移 2~3px）。现在眉线加粗到 5（master px），位移约翻倍
（sad/worried/confused/**cry** 外端 +22、内端 −12；angry/determined 外端 −12、内端 +26；
happy/excited/surprised 外端 −9、内端 −10）。`cry` 归入 sad 组是因为官方脸表给 cry 标了 `brows:'sad'`。

### 11.3 面部代码搬进仓库 + 验证坑

- `buildFace/paintFace` 以前是"从 scratch 的 figure.js 里切出来"，现在改读**仓库内**的
  `pure-generation/expression-face.js`（与 scratch 版逐字节相同，scratch 版哈希仍记在
  `EXPRESSION-PRESERVATION.json`）。这样随包发布的面部代码在 git 里可评审，改眉毛/嘴型有据可查。
- **验证坑**：内置浏览器标签页在后台时 `requestAnimationFrame` 被节流，DOM 读到的嘴/眉状态可能整体落后
  一步（我遇到过整批读值偏移一格的假象），并且 `tab.screenshot()` / `getScreenshot()` 会直接报
  "Unable to capture screenshot"。要截图就把标签页切到前台，或改用页面内的确定性采样
  （`setEngineeringFrame` / 「导出左右动作 QA」）。

### 11.4 招手 / 开心 / 害羞（2026-10-16，用户："招手和开心的笑脸不是很自然，害羞也没有变化"）

**招手（手臂角度）**：原来抬手 111°，硬袖甩过竖直位，袖子被切断的肩口直接横在胸口，看起来像"贴上去的手臂"。
用本包自己的部件在本地合成对比 111°/90°/72°/60°（`scratch/probe-blush-and-arm.py` → `arm-angles.png`），
**72°** 最自然（手在头侧上方、袖子不横跨胸口），现为 `72*e + 5*sin(k*π*6)*e`。

**开心（笑脸）**："^^"那两道弧就是眼睛，官方脸表只在 sad/worried/scared/angry/determined 上画眉毛，
从来不给 happy 画——所以弧线之上再压两条眉线，一张脸出现四道弧，才显得别扭。现在 `selected==='happy'`
（含 wink 的闭眼侧）时把眉毛隐藏。嘴也从"2.8px 细线"改成**实心张口笑＋舌头**（官方 happy 嘴是实心张口），
细线在舞台缩放下只有 1.5px，像一道划痕。

**害羞**：原来只换了嘴型，几乎看不出变化（官方脸表 shuffle 是"眼睛缩小并内移下移 + 满脸通红"）。现在
眼睛按官方比例缩放（0.90×0.82）并向内下移（±5, +7），另外加了一层**动态腮红**（见下）。

**动态腮红**：本包脸贴图自带的腮红只在 (550,542)/(733,515) 两点、很淡；官方给 shy/flustered 的是 blush 1
（满脸通红）。现在在这两个实测中心上叠一层径向粉红（用 `head-clean` 实测得到，见同上的探针脚本），
透明度按 `face.blush` 走：`clamp((blush-0.35)/0.65)*0.75` —— 害羞/慌张（1）= 0.75，喜欢（0.7）= 0.40，
开心（0.45）= 0.11、期待（0.4）= 0.06（等于不动），不会糊掉已验收的脸。

**本地验脸工具**：浏览器会话不可用时，`scratch/preview-face.py` 会把眼睛贴图按渲染器的变换合成、并把嘴/眉的
矢量路径按同一变换画出来（`face-sheet.png`），用来判断脸部改动是否成立。

### 11.5 坐姿表情复用站立表情（2026-10-16，用户："绝大多数坐下的表情都有问题，复用跟站立时一样的表情"）

**根因**：坐姿用的是**另画的一套五官**（`seat-eye-0/1` 等 14 张），那套贴图把刘海糊在瞳孔上、形状也不如
站姿干净——所以坐姿表情怎么调都别扭。合层对比：`scratch/probe-seated-face.py` → `seated-compare.png`
（左＝原来的坐姿贴图，右＝站姿贴图按相似变换贴到坐姿头上）。

**实现**：`expression-face.js` 的 `buildFace` 现在两种姿势都读**站姿**的脸部贴图与站姿 rig，坐姿时给整个
面部组一个相似变换 `FX_POSE_FIT.seated`（由两个 rig 的眼框自动求出：缩放 0.9517、旋转 −4.25°、
平移 (−5.9, +370.4)，即把站姿双眼中点映到坐姿双眼中点）。眉/嘴/腮红/泪流/期待星都在这个组里，因此
**一起被映射**、整套表情与站立完全一致；`seat-*` 那 14 张贴图保留在包里但不再引用。
头两侧的特效标记（汗滴/怒筋/晕乎星等）画在面部组之外，仍按 `anchors` 的站姿→坐姿偏移 (−3, +298) 走。

**坐姿脸部仍是"不随点头旋转"**（站姿的 `faceHost` 会跟 `head` 一起转，坐姿没有对应节点）——这是既有差异，
本次未动，列为待办。

