# ATRI 形象包 · 经验与坑（v1.1.0 验收后整理）

> 这份文件只记**踩过的、有代价的**结论。每条都带实测数字或源码位置，方便下一个人别重试。
> 配套阅读：`docs/ATRI-COOPANION-接入说明.md`（格式与流程）、`docs/ATRI-HANDOVER-DSH-2026-10-20.md`（会话交接）。

---

## 一、Coopanion 宿主环境

### 1. 形象包目录不是 `data/figures`

```
✅ E:\MC\gpt\tools\coopanion\app\data\home\companion\data\figures\<包目录>\
❌ E:\MC\gpt\tools\coopanion\app\data\figures\        ← 这个目录程序从不扫描
```

源码：`core/companion.ts` → `figurePacks([join(loaded.dataDir,'figures'), ...])`，
`dataDir` 实为 `data/home/companion/data`。

**判断方法**：那个目录里本来就有装成功的包（`gpt-dragon-v005-r25`、`neco-arc`）。
看到它们就等于确认了路径。`data/` 顶层那堆 `Cache`/`GPUCache`/`Local Storage` 是 Electron 的 userData，
业务数据一律在 `data/home/<bot>/data/` 下面。

**教训**：放错目录时程序**完全静默**——日志里连一行都不提这个包。先看参照包在哪，比读源码快。

### 2. 启动它不要用 `Start-Process`

```
❌ Start-Process Coopanion.exe   → 进程起来后立刻全部退出，core.log 末尾是
                                   窗口进程退出(退出码 0xFFFFFFFF)
✅ explorer.exe 'E:\...\Coopanion.exe'   → 12 个进程稳定
```

手动双击同一个 exe 也正常，所以是启动方式的问题，不是安装损坏。

### 3. 大文件下载必须走代理

GitHub 直连 **8.7 KB/s**（167MB 要 5 小时），走本机 `http://127.0.0.1:7897` 后 **1.7 MB/s**，
差 **200 倍**。以后下 release 附件一律加 `-x http://127.0.0.1:7897`。

---

## 二、形象包清单（`figure.json`）

### 4. `vocab` 每个词都必须有 `about`

```jsonc
{ "id":"neutral", "kind":"expression", "names":{"zh":["平静"]},
  "about": {"zh":"默认的脸，没什么特别情绪"},   // ← 缺这个，整包被拒
  "seconds": 4 }
```

报错会明确指出：

```
形象包没加载: ...\atri-v011:vocab.neutral.about 缺失
```

`about` 不是备注——模型靠它知道「点这个会发生什么」，和名字一起进词表。
37 个词全部要写（`scripts/add-atri-vocab-about.py` 负责，有 alias 与 fallback，新增词不会再把整包搞挂）。

### 5. `about` 是唯一随形象切换进提示词的字段

`src/world.ts:576` → `t.body(name, about, picks)` → `model-text.ts` 拼成
`[figure] 你现在的样子：<name>, <about>`，**每轮请求重发**。

所以写紧凑肖像，不写设定集。形象包**没有 persona 字段**，
`core/seed.ts` 的 `applyPersona()` 只接受内置 id，自定义形象只能走
`workspace/CONSTITUTION.md` + `about` 两处配合。

### 6. 三个脚本各管一件事，不要重叠

| 脚本 | 所有物 |
|---|---|
| `write-atri-manifest.py` | `figure.json` 顶层字段（含 `VERSION` 常量） |
| `add-atri-vocab-about.py` | 每个 vocab 词的 `about` |
| `make-atri-thumb.py` | `tex/thumb.png` |
| `package-atri-pack.py` | 只校验 + 打包，**不改写** |
| `publish-atri-pack.py` | 编排上面四个，是 `scratch/` → `packs/` 的唯一通路 |

**曾经两个脚本都写 `name`/`about`**，打包脚本把清单脚本刚写的值覆盖回去，
导致亚托莉身份描述**静默没生效**。职责必须唯一。

**版本号也归 `write-atri-manifest.py`**：`build-diagnostic.py` 会用上一版 manifest 重新生成，
不在清单脚本里钉住 `VERSION`，每次重建都会被冲回旧版本号。

---

## 三、构建与发布流程

### 7. `scratch/candidates` 是构建输出，`packs/` 是副本

两者**不会自动同步**。重建只写 `scratch/`，装到 Coopanion 的是 `packs/`。
曾经因此出现「预览是新的、安装的是旧的」（`logo_scale` 仍是旧值）。

`scripts/publish-atri-pack.py` 是唯一通路，顺序固定：

```
拷贝构建产物 → 重写 manifest → 补 vocab about → 重做 thumb → 校验打包
```

顺序不对会静默丢东西。

### 8. 手修的美术会被两道工序吃掉

**事故**：你手修的左侧马尾（md5 `6ab6bf6a`）被回退了，原因叠加两条：
1. `build-diagnostic.py` 每次都用 `raw/pony-pair-left-01.png` + 配准矩阵**重新生成** `tex/tail-left.png`；
2. `publish-atri-pack.py` 又把这份构建产物整个复制到 `packs/tex/`。

**三处防护（已落地）**：

| 防护 | 实现 |
|---|---|
| 存到不会被覆盖的地方 | `official-regeneration/hand-edited/tail-left.png`，构建优先读它，原始素材作 fallback |
| 不再叠加一次位移 | `add()` 支持 `matrix=None`——手修图直接画在画布上（bbox 148–370 × 279–933），再套配准会二次错位 |
| 发布时保留 | `publish-atri-pack.py` 的 `HAND_EDITED` 白名单，跳过并打印保留了哪些 |

重建后逐字节验证：**不透明区 RGB 最大差 0，alpha 完全一致**（透明区 RGB 被 premultiply 清零属正常）。

**流程约定**：以后手修图丢进 `hand-edited/` 覆盖同名文件，再跑一次 `publish-atri-pack.py` 即可。

### 9. `matrix=None` 曾让构建**静默不产出**

`add()` 里接受 `None` 之后，后面 `records.append(... matrix=matrix.tolist() ...)` 直接
`AttributeError: 'NoneType' object has no attribute 'tolist'`。

后果很隐蔽：**脚本崩在写 `figure.js` 之前**，磁盘上留的是上一次的旧文件，
看起来像"改了没生效"。修法：记录里写单位矩阵 `(identity if matrix is None else matrix).tolist()`。

**教训**：改完必须看 `figure.js` 的 mtime 和关键字计数，不能只看"脚本跑完了"。

---

## 四、渲染与手感（对着官方 kit 量出来的）

### 10. 默认尺寸对齐鲸鱼娘

```
原来 1290px × 0.17350 = 223.8 / 256 = 87.4% 舞台高
鲸鱼 EXTENT [20,12,236,256]       = 244  / 256 = 95%
现在 0.190543                     = 245.8/256 = 96%
```

`logo_scale` 是唯一入口：hits / anchors / extent / 部件变换全从它换算，
所以角色和点击热区一起缩放，不会错位。

### 11. 弹性曾被我们自己**精确抵消**

`renderer-template.js` 的补偿原来写 `rigid = uniform / k`，代进 kit 的
`sx = (1+sq*.7)...`、`sy = (1-sq)...`：

```
最终 x = kx × uniform/kx = uniform
最终 y = ky × uniform/ky = uniform      ← 两轴恒等
```

kit 的 squash 全靠 `ky/kx` 这个比例，被这一除**精确除掉**，落地/跳跃/被扔全部退化成平的呼吸脉冲。

改成 `rigid = (uniform/k)^(1-SQ_KEEP)`，`SQ_KEEP = .85`：绝对尺寸仍归一化，各向异性保留 85%。

### 12. 提起的形变单独压

kit 在 `drag` 时 `pet.stretch → 1`（额外 −5% x、+9% y），而亚托莉是被**头**拎起来，
整条身体被拉长的观感特别重。`DRAG_KEEP = .45`：提起时只保留不到一半，落地跳跃仍 `.85`。

### 13. 步态：固定频率 vs 速度驱动

| | 我们原来 | 官方 kit |
|---|---|---|
| 步频 | `sin(t*8)` ≈ 1.27 步/秒 | `pet.phase += 2π·rate·dt`，walk **2.1** / run **4.4** 步/秒 |
| 步幅 | 固定 ±8°，脚尖行程 59px | `strideT = (run?17:10)·(.4+.6k)`，**随速度增长** |

步频只有官方的**六成**，步幅完全不动 —— 所以像滑行。

现在相位从 `o.swing` 积分（kit 自己的平滑速度代理，**是 figure 自绘身体唯一能拿到的速度信号**，
`custom.draw` 不传原始 velX），步幅 11–16° 跟速度走，停下时吸附到最近的落脚步相位。

### 14. 顺拐 = 同侧手脚同相

原来 `arm-left` 和 `leg-left` 都是 `+swing*gait`，左手和左腿同时向前。

```
arm-left  -1.2   leg-left  +1     同侧反相  → 不再顺拐
arm-right +0.8   leg-right -1     同侧反相
左臂与右腿同相                     → 自然行走的斜对角
```

### 15. 坐姿判定**不能看 `o.sit` 的值**

这是 v1.1.0 之前那个"每次点击都挤压一下然后坐下再站起"bug 的根因。

`kit/body.js` 会**瞬时**抬高 `sitT`：

```
crouch（jump / hop）  sitT = .3
land（点击落地缓冲）   sitT = .35 * (1-smooth(mt/.35))
sit / sleep / dizzy   sitT = 1     ← 只有这三个是真的坐下
```

把阈值降到 `.14` 之后，**每次点击都经过 `land`，全都越过阈值**，于是切到坐姿贴图再切回来。
小跳是 `crouch → air → land`，同样触发。

**正确做法：按 mode 判定，值只做兜底**

```js
const seatMode = o.mode==='sit' || o.mode==='sleep' || o.mode==='dizzy';
const seated   = seatMode || o.sit > .75;
```

`.75` 兜底用于坐姿模式刚结束、`sitK` 还在 `ease(6)` 衰减的那几帧。

### 16. 摔晕"先站一会才坐下"是阈值太高

`sitK` 按 `ease(6)` 爬升，旧映射要求 `sit = .5` 才翻图，所以前半段抖动是站着做完的。
改成按 mode 判定后，`sit` 一开始抬就翻图（kit 在同一帧开始降低身体），`poseDy` 的弹簧仍负责平滑。

---

## 五、预览与缩略图

### 17. `thumb` 不能指整画布贴图

原来指向 `tex/head-clean.png`——一张 **1145×1374** 的整画布，内容只占头部那一块。
装扮卡把它塞进小方框，就是"空框"。

`make-atri-thumb.py` 从 `master.png` 裁真实角色轮廓，等比居中放进 512×512。
加 `--bust` 取角色顶部 **62%**（头、双蝴蝶结、马尾根），装扮卡用这个。

### 18. 预览站与本地开发是两套源

- 本地：`http://127.0.0.1:8765/...?pack=scratch/candidates/atri-pure-components-01`
  （`scripts/serve-preview.py` 发送 `Cache-Control: no-store`，否则改图后浏览器仍给旧图）
- 线上：`https://scarlet20252025-cloud.github.io/Coopanion-Skin-Design/`
  （`scripts/deploy-preview.py <pack>`，只发布 `packs/` 那份）

`python -m http.server` 不发任何缓存头，改图后必须清缓存——这是"改了没生效"的常见假象。

---

### 19. 版本快照必须抓 `packs/`，不是 `scratch/`

`scripts/version-candidate.py` 原来 `LIVE = scratch/candidates/atri-pure-components-01`，
所以 012 快照抓的是**构建输出**，与真正安装发布的 `packs/atri-v011` 差了 3 个文件：

```
tex/tail-left.png    手修马尾（scratch 里是重建产物）
tex/thumb.png        半身缩略图（只有 publish 时才生成）
figure.json          version 1.1.0 与 thumb 字段（只有 publish 时才写）
```

后果：快照标记为"已验收"，但里面的东西**不是**验收的那一版，回退时会拿到错的图。

已改成 `LIVE = ROOT / "packs" / "atri-v011"`。核对方式：快照与 packs 逐文件 md5 对比，
**52/52 一致、不一致 0** 才算数。

**根本规律**：这个仓库里"被验收的东西"永远是 `packs/`（以及安装目录），
`scratch/` 只是中间产物。任何"存档 / 快照 / 对比 / 回退"都应以 `packs/` 为准。

---

### 20. 宣传片里 `do()` 返回 false 会静默吞掉动作

做第二支宣传片（亚托利版）时，在点击后 0.6 秒补了一个 `word('surprised')`，
渲染直接报 `Movie action rejected`。查 `preview/vendor/kit/body.js` 的 `doWord()`：

```js
if (KIT_EXPRESSIONS.includes(w) || words[w]?.expression) {
  if (busy()) return false;      // ← 点击触发的反应动作还在播
  setExpr(w);
  return true;
}
```

**`busy()` 期间表情一律被拒。** 这不是 bug，是真实运行时行为——真人在桌面上戳一下，
那 2 秒里再调表情也会被丢掉。所以：

- 宣传片不要"抢发"表情，让 kit 把点击反应播完；
- 渲染器必须检查 `accepted`，任一为 `false` 就抛错中止。只靠"画面看起来有动作"会漏掉这种情况，
  因为静态姿势和真实动作在截图上可能长得很像，但 audio 轨和后续帧的时间轴已经错位了。

### 21. 宣传片的气泡/粒子必须确定性生成

`Math.random()` 会让 `renderAt(t)` 不再是纯函数：同一时刻两次渲染得到不同画面，
抽帧复现、并发渲染、逐帧比对全部失效。改用固定种子的 LCG（本版 `seed=4021`），
所有装饰元素（气泡的 x / 半径 / 上浮速度 / 摆动相位）在页面初始化时一次算好，
之后只按 `t` 求位置。这样 900 帧里任何一帧都能单独重渲出来核对。

### 22. 指针坐标要跟着场景缩放联动

龙娘那支角色固定缩放，指针直接用角色局部坐标就行。亚托利这版为了给对话气泡让位，
对话段把角色缩到 0.66、片尾收到 0.94 —— 指针若仍用局部坐标，就会飘到角色鼻子外面。

正确写法：`screen = 场景原点 + 局部坐标 × 缩放`。同理，`clickRing` / `clickCore`
的圆心也要一起换算，否则点击波纹会和指针分离。

### 23. 没眼睛看画面时，用像素指标代替目视

本机模型无法读图，所以写了 `promo/check-atri-frames.py`：按区域（标题 / 正文 / 角色 / 页脚）
统计 ink 占比（显著亮于或暗于背景的像素比例）、亮度标准差、相邻像素亮度差（边缘强度）。

它当场抓出一个真问题：**23 秒坐姿段左侧只有两行文字，`ink=0.0005`**，画面几乎空着。
补了三张信息卡（坐姿 / 圈圈眼 / 60fps）+ 一条伸展横线 + 一句台词后重新抽样，
`ink` 回到 0.1263，六帧全部 `ALL OK`。

**阈值不是拍脑袋定的**：各区域下限按"一段正常排版的文字大约占多少墨"反推，
`title≥0.010`、`body≥0.004`、`pet≥0.060`、`footer≥0.001`，再配合"相邻采样帧的角色区
不能完全一样"来确认场景真的切换了。这套指标只能证明"有东西、有变化"，不能证明"好看"，
所以仍然需要人最后看一眼。

---

### 24. 一个没闭合的 `<g>` 能让半个画面消失，而且 DOM 看不出来

36 秒版改场景时，`seated` 组里新加的 `seatCards` 少了一个 `</g>`。后果不是报错，
而是 `seated` 把后面**所有**元素都吞成了自己的子节点——`outro`、角色挂载点、
底部进度条全成了它的孩子。而 `seated` 自身的 opacity 是 0（不在它的时间段内），
于是从 y=240 往下整片黑掉。

最坑的是 DOM 层面完全正常：

```
outro    styleOp=0 compOp=0 bbox=[112, 234, 634, 582]   ← 属性都对
outro .title box=[138, 277, 366, 158] top=text#.title   ← 元素也在
```

`getComputedStyle`、`getBBox`、`elementFromPoint` 全都说"好着呢"，
因为它们只看元素自己，不看**祖先有没有被隐藏**。真正暴露问题的是这一行：

```
svg lastChild=g#seated        ← 应该是 rect（暗角）！
```

`seated` 的 bbox 是 `[0,0,1920,1080]`，一个只画左侧文案的组不该有整屏的框。

**判据**：渲染完检查根节点的 `lastElementChild` 是不是你以为的那一个；
以及每个场景组的 `getBBox()` 是否符合预期尺寸。标签配平用
`grep -c '<g[ >]'` 与 `grep -c '</g>'` 对比，两者必须相等。

### 25. `setAttribute('transform')` 是整体覆盖，会冲掉你在 HTML 里写的 translate

为了让角色挂载点用 SVG 原生嵌套 `<svg>`（想避开 foreignObject），把

```html
<foreignObject id="petFrame" x="960" y="96" ...>
```

改成了

```html
<g id="petFrame" transform="translate(960 96)"><svg id="petMount" .../></g>
```

结果角色跑到了左上角。原因是 `timeline.js` 每帧执行：

```js
fp.setAttribute('transform', `matrix(${scale} 0 0 ${scale} ${px - 960*scale} ${py - 96*scale})`)
```

`setAttribute` 是**替换**不是追加，HTML 里那个 `translate(960 96)` 第一帧就被冲掉了。
而 matrix 里的平移量是 `px - 960*scale`，在 scale=1 时正好等于 0 —— 设计上就是给
"位置已经由 x/y 属性承担"的 foreignObject 用的补偿量，换成 `<g>` 后平移就丢了。

**结论**：定位量要么全放在元素自身的 x/y 属性里（foreignObject 的写法），
要么全写进每帧计算的 transform 里，不能一半一半。这一处最终回退到 foreignObject。

顺带记一个误判：我用 `<g[\s>]` 数标签时得到 38 开 / 37 闭，以为还有一处没配平，
实际是注释里写了 `<g transform=...>` 这串文字被正则数了进去。**注释里别写带尖括号的标签名**。

### 26. 「DOM 说可见、截图说没有」时，先怀疑自己改了没用，再怀疑合成器

排查上面那个黑屏花了很久，中间走了两条弯路，都值得记下来：

**弯路一：以为是截图时机问题。** 加了双 `requestAnimationFrame` 等待，没用。
做了 A/B/C/D 四种截图方式对比（直接截、双 rAF、双 rAF+300ms、CDP `Page.captureScreenshot`），
四种结果**逐像素相同**。这一步很有价值——它一次性排除了"合成分层没刷新"这个假设，
否则会一直在错误的方向上加等待。

**弯路二：以为是 foreignObject 的跨层重绘问题。** 把 foreignObject 换成嵌套 `<svg>`，
数值一点没变。这个改动本身是错的（见第 25 条），但它的"无效"恰好证明了
问题不在渲染机制，而在**画什么**。

正确的顺序是：**先用 `getBBox()` / `lastElementChild` 验证结构，再看像素**。
结构对了再谈渲染，结构不对谈渲染全是白费。

**一个可复用的判据**：如果多个不相关的时间点同时出现"内容缺失"，
大概率是结构问题（某个祖先被隐藏、某个元素被吞）；如果只是零星个别帧异常，
才更可能是合成/时序问题。

---

### 27. 宣传片的节奏要按"动作能播完"倒推，不是按"信息够不够"排

36 秒版被用户评价"演示的太急促了"。复盘下来问题不在拍了多少内容，而在于
**动作之间没留呼吸**：气泡第二行只隔 0.55 秒就出，表情 chip 每 1.1 秒换一个，
点击后 1.5 秒就进下一段。

真正卡住节奏的是 `kit/body.js` 的 `doWord()`：

```js
if (KIT_EXPRESSIONS.includes(w) || words[w]?.expression) {
  if (busy()) return false;      // ← 点击反应还没播完，表情直接被丢
```

也就是说**间隔太密不只是难看，动作会被真的丢掉**。上一版之所以没暴露，
是因为点击后只发了一个动作；这一版想在点击后连发表情，`busy()` 立刻拒收。

据此定了硬规则（写进 `promo/README-ATRI.md`，改时间轴时照抄）：

| 规则 | 数值 |
|---|---|
| 单个表情展示 | ≥ 1.4 s |
| 同段相邻动作间隔 | ≥ 1.4 s |
| 「萝卜子」每级递进 | ≥ 2.4 s |
| 气泡第二行延迟 | 1.3 s |
| 场景淡入 / 位移 | 0.5 s / 0.7 s |

时长从 30 → 36 → **60 秒**，用户明确说"篇幅长一点无所谓，我又没限制你"。
信息量几乎没变，多出来的时间全给了停顿和情绪递进。

**推广的规律**：这套渲染器里"一个动作"的最小单位不是帧数，而是
**kit 的模式时长 + busy 释放时间**。排时间轴前先问"这个动作自己要走多久"，
再去填画面，而不是先排满画面再指望动作塞进去。

---

### 28. UI 标签不等于可演示动作：先把 `model.words` 对一遍

宣传片的表情 chip 原来写了 8 个：「招手/开心/跳舞/害羞/惊讶/嘟嘴/晕乎/生气」，
用户要求删掉「蹭蹭」和「生气」时才发现——**「蹭蹭」根本不在 `model.words` 里**。

```
model.json words: neutral happy wink love shy surprised angry sad smug worried
                  flustered scared excited confused stand wave walk run jump hop
                  look turn nod shake spin sit sleep dizzy bow shiver dance bubble
                  heart note pointer ring spiral star sweat tear drag dragged
                  tremble sleepy thinking pout determined cry flap
```

没有「蹭蹭」。它只是一个我写进 UI 的标签，底下没有对应的真实动画。
放进去等于演示了一个不存在的动作。

「生气」则相反：`angry` 确实在 `KIT_EXPRESSIONS` 里，有青筋和抖动，是真实动作。
删掉它是因为**位置不对**——在 chip 里 1.4 秒一闪而过，不如放到「叫她萝卜子」桥段
当剧情结果（惊讶→嘟嘴→生气）有力。

**教训**：给宣传片写动作清单前，先 `grep` 一遍 `model.words`。
不在表里的词不是"还没做"，是"不存在"。这和 kit 的 `doWord()` 返回 false 是两种失败：
一个是拒收，一个是**根本没得发**。

改动落地（只动这两张表，萝卜子桥段一行没碰）：

| 位置 | 改前 | 改后 |
|---|---|---|
| `#actionChips` | 8 个（4+4 两排） | 6 个（3+3 两排） |
| schedule 表情段 | 8 动作 × 1.4 s | 6 动作 × 1.77 s |
| `actIdx` 分档 / `actTitles` / chip 循环 | 8 | 6 |

删完 6 个动作分摊原来 10.6 秒的段落，间隔从 1.4 秒变成 1.7 秒，**比原来更慢**。

**验证手法**：抽帧后用 `promoState.checks` 反查该时间窗内实际发过的动作集合：

```python
words = sorted({c['word'] for s in d for c in s['checks'] if 31 <= c['time'] < 42})
# 期望: ['dance','dizzy','happy','shy','stand','surprised','wave']  ← 没有 pout / angry
```

比"看画面有没有生气脸"可靠得多，也不依赖人眼。

---

### 29. 演示的前提是动作真的发生；没动作就别占演示位

用户看完成片指出：「46 秒这里的嘟嘴没做动作，不要做演示」。

核实属实。`pout` 在 `model.words` 里有，`doWord()` 也返回 true，但**画面上的变化极轻微**——
这个形象的脸部贴图在嘟嘴状态下几乎没有差别，观众看到的是一张没变的脸。

这和前面几类失败不同：

| 失败类型 | 表现 | 判据 |
|---|---|---|
| 词不在表里 | 根本没得发 | `grep model.words` |
| `busy()` 拒收 | `accepted=false` | 渲染器已中止 |
| **动作发了但看不出来** | `accepted=true`，画面无变化 | **只能靠人看** |

第三类是自动化检查抓不到的：我的像素指标只能证明"区域有内容、场景切换了"，
证明不了"这个表情看起来和上一个不一样"。

处理：删掉这一级演示。删完 46.0–48.4 空出 2.4 秒，把生气爆发从 48.4 提前到 46.2 填上。
现在两级（惊讶 43.6 → 生气 46.2）都是确认会播出来的。

**写进 `pout` 的词条描述里**，避免下一个人再犯：

```
嘴嘟起来、脸红、扭头不看你——有点不服气的小情绪。
注意：这个表情在当前形象里脸部变化很轻微，不适合当作独立演示动作。
```

### 30. 人设禁忌要写进提示词，不只是拍进宣传片

用户要求：「对应的皮肤包环境提示词里也要有演示的效果」。

宣传片里演一遍不等于角色真的"有"这个设定。装到 Coopanion 之后，模型靠 `figure.json`
的 `about` 字段认识这个角色——那里没写，她就不知道自己忌讳被叫萝卜子。

改了三处，四语（zh / zh-Hant / en / ja）同步：

1. **`about`**：追加这段禁忌——
   「最忌讳被叫『萝卜子』——听到这个词会先愣住，然后立刻炸毛否认，强调自己是高性能的仿生人而不是蔬菜；情绪上来时头顶会冒青筋、身子发抖，这时候哄她也没用，只能等她自己消气。」
2. **`vocab.angry.about`**：带上触发语境——
   「眉毛压低、头顶冒出怒气符号、身子发抖——被叫『萝卜子』时就是这个反应……」
   原来只写「眉毛压低，头顶冒怒气符号，身子发抖」，模型不知道什么时候该用。
3. **`vocab.surprised.about`**：标注它是前置反应——
   「眼睛睁大，头顶冒出感叹号——听到意外的话（比如被叫『萝卜子』）时的第一反应，先是愣住。」

**规律**：`about` 是角色的"世界观"，`vocab[].about` 是每个动作的"适用场景"。
宣传片里想让观众看到的因果链（被叫萝卜子 → 愣住 → 炸毛），
两处都要写，否则装进应用后模型只会随机演表情。

顺手修了一个拼接 bug：`en` 的 about 追加后出现 `underestimated.Her one hard taboo`（缺空格），
四语之间也补了段落分隔。

---

## 六、这一轮之后的功能清单（v1.1.0）

```
Coopanion      E:\MC\gpt\tools\coopanion\app      0.2.16
形象包         data\home\companion\data\figures\atri-v011\   53 文件 / 42 贴图
清单           id=gpt-atri  version=1.1.0  vocab 37（about 全齐）
人设           data\home\companion\workspace\CONSTITUTION.md
手修源头       official-regeneration/hand-edited/tail-left.png
zip            delivery/atri-v011-coopanion.zip
```

| 项 | 值 |
|---|---|
| 舞台占比 | 96.0%（对齐鲸鱼娘 95%） |
| 弹性保留 | 常态 85% / 提起 45% |
| 步频 | walk 2.1 / run 4.4 步·秒⁻¹（对齐 kit） |
| 步幅 | 11–16°，随速度 |
| 四肢相位 | 对角配对（无顺拐） |
| 坐姿判定 | mode 白名单 + `.75` 兜底 |
| 缩略图 | 512×512 上半身 |

## 七、仍未完成

1. **坐姿五官是旧抠图素材**（`source-023` ~ `source-033`）。位置已修好，画风与站立不一致；
   彻底解决要按站立画法重画约 14 张。用户已明确「五官不用改了」。
2. **LLM 余额不足**：`LLM API 402`，与形象包无关，说话需要账户有余额。
3. **真实动作采样未重跑**：本机 venv 无 playwright，`qa/current/` 仍是旧指纹。
