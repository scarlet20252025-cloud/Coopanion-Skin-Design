# 宣传片的可复制制作路线

本次选择 30 秒、1920 × 1080、30 fps。SVG 负责字幕/界面/镜头，线性运动是用户明确选择；龙娘沿用发布 PNG 和实际 kit 动画。对话气泡是示例文案，没有调用真实聊天模型。

## 文件

- `promo/BRIEF.md`：六段分镜及功能清单。
- `promo/assets/src/01-film/01-film.html`：SVG 舞台、文字和构图。
- 同目录 `timeline.js`：单调 `renderAt(t)`、实际 do/pointer/drop 调用、回执。
- `promo/render.py`：离线渲染、抽帧、FFmpeg 编码、全片解码检查。
- `promo/generate-audio.py`：原创合成背景音，需 NumPy；可用其他已授权音乐替代。
- `promo/assets/qa/video-validation.json`：原 900 帧成片验证记录。

## 上手

```sh
uv sync --project promo
# 按当前 Playwright 的安装方法准备 Chromium；也可 --browser 指定现有浏览器
uv run --project promo playwright install chromium
npm run preview
```

服务保持运行。在另一个终端先检查关键帧：

```sh
uv run --project promo python promo/render.py --ffmpeg /path/to/ffmpeg --samples 1.5,6,12,19,23,28
```

看关键帧后再完整渲染：

```sh
uv run --project promo python promo/render.py --ffmpeg /path/to/ffmpeg --out "promo/assets/GPT 龙娘宣传片.mp4"
```

默认不加音乐；需要本次背景音时先 `uv run --project promo python promo/generate-audio.py`，再传 `--music promo/assets/original-music.wav`。`--browser` 接受实际浏览器程序绝对路径，不把制作者机器的 Edge/FFmpeg 路径复制给别人。

本次中文字形使用 Windows 的 Microsoft YaHei。其他机器须有支持简体中文的字体，并在 SVG 样式中指定实际可用的字体；先抽帧检查缺字和排版。未验证跨系统字形完全一致。角色模块和资源使用相对路径，可随整个源码目录移动。

## 帧准确与常见错误

每帧先按 60 Hz 小步推进角色逻辑，再设置 SVG 场景到目标时间，等待字体/图片/ready，然后截图。900 张 PNG 经 FFmpeg 拼成 30 秒 MP4。暂停 CSS 动画后设置 currentTime；截图不传 `animations="disabled"`，它会覆盖定位，导致全片停在首帧。

`body.do()` 返回 true 与 actual mode/event 一起记录；粒子在真实 kit 中产生。提起演示必须 down → move 过阈值 → hold → up/drop → land；画一个上移的静态角色不能证明拖拽动画。

不同片段各有独立帧目录，避免并发混片。临时目录由本次进程创建，清理前验证位于任务输出目录。不在浏览器输入系统命令，不读取真实聊天记录/个人配置，也不把离线渲染当作真实账户操作。

最终用编码后的 MP4 抽帧和完整解码：验证时长、分辨率、fps、音轨、字形、遮挡、片尾和动作衔接。视频黑底上出现新接缝时回到素材归属，而不是用宣传片遮住它。

本次参考 animation-builder 的截图/FFmpeg方法；其建议缓动被用户指定的线性运动覆盖。仓库渲染器独立且路径可配置，不依赖仅在旧会话 tools-local 存在的技能副本。

---

## 第二支：亚托利（2026-10-31）

同一套三段式管线，独立目录 `promo/assets/src/02-atri/`，不复用龙娘的 `01-film/`，避免两支片子的时间轴互相污染。

### 新增文件

- `promo/assets/src/02-atri/atri-film.html`：深海版 SVG 舞台（三层视差光柱、气泡层、水波层、径向光晕、暗角）。
- `promo/assets/src/02-atri/timeline.js`：`renderAt(t)` + 场景变焦 + 指针跟随缩放。
- `promo/render-atri.py`：渲染器，默认输出 `promo/assets/亚托利宣传片.mp4`。
- `promo/generate-atri-audio.py`：原创合成配乐，92 BPM 水下 A 大调五声。
- `promo/README-ATRI.md`：面向使用者的说明。

### 这一轮踩到的坑

**1. `do()` 返回 false 是真实行为，不是 bug。**
点击后立刻 `word('surprised')` 会被拒，因为 `kit/body.js` 的 `doWord()` 里表情分支有 `if (busy()) return false` —— 点击触发的反应动作还在播。正确做法是**不抢发表情**，让 kit 自己播完点击反应。渲染器保留 `accepted` 记录并在任一为 false 时抛错，这样"动作没出现但视频照出"的情况不可能发生。

**2. 气泡必须确定性生成。**
`Math.random()` 会让同一时刻的两次渲染得到不同画面，`renderAt(t)` 就不再是纯函数，抽帧复现和并发渲染全废。改为固定种子 LCG（`seed=4021`），气泡的 x/半径/速度/摆动相位在页面初始化时一次算好，之后只按 `t` 求位置。

**3. 指针坐标要跟着场景缩放走。**
龙娘那支角色是固定缩放，指针直接用角色局部坐标。这一版对话段缩到 0.66、片尾 0.94，指针若仍用局部坐标就会飘到角色外面。写法：`screen = 场景原点 + 局部坐标 × 缩放`。

**4. 环境依赖要现场找，不要假设 PATH 里有。**
本机 `which ffmpeg` 为空，实际可用的是 `C:\Program Files\Virtual Desktop Streamer\ffmpeg.exe`（n4.4，`libx264` + `aac` 齐全）。Playwright 没装、没有自带 Chromium，直接用 `--browser "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"`，省掉 `playwright install` 的下载。

**5. 预览服务是前提，不是可选。**
`npm run preview` 起的是 `scripts/serve.mjs`，监听 `127.0.0.1:4319`，根就是仓库根。`packs/atri-v011/figure.js`、`model.json`、`tex/*` 都靠它经相对路径加载；用 `file://` 打开会因 CORS 直接失败。

### 2026-10-31 第二轮：36 秒版 + 指定 BGM + 多演示交互

用户要求：换 BGM 为 `szak - 親愛なるあの日々へ`，并且多演示交互动作和表情反馈，
例如"对话里说她是萝卜子，她会生气"。

改动：

- 时长 30 → **36 秒**（1080 帧）；`render-atri.py --duration` 默认 36、上限 60。
- 对话从一轮扩到**三轮**（陪伴 / 撒娇 / 闹别扭），加轮次指示点，逐行出字。
- 表情 chip 从 4 个扩到 **8 个**（招手/开心/跳舞/害羞/惊讶/嘟嘴/晕乎/生气）。
- 新增 **23.5–30 s 的「萝卜子」桥段**：惊讶 → 嘟嘴 → 生气三级递进，
  红色光晕 + 抖动 + 青筋，右侧三步指示条同步点亮。
- BGM 由 `--music promo/assets/atri-bgm.mp3` 传入（裁 36 s、1.2 s 淡入、2.5 s 淡出）。

#### 这一轮最贵的三个坑

**坑一：一个没闭合的 `<g>` 让半个画面消失。**

`seated` 组里新加的 `seatCards` 少了 `</g>`，于是 `seated` 把后面所有元素
（outro、角色挂载点、进度条）全吞成子节点；而 `seated` 自身 opacity=0，
从 y=240 往下整片黑。

DOM 层面完全看不出来：`getComputedStyle` 说 opacity=1，`getBBox()` 正常，
`elementFromPoint` 还能命中标题元素——因为它们只看元素自己，不看祖先。

唯一暴露问题的是：`svg.lastElementChild` 是 `g#seated` 而不是暗角 `rect`，
且 `seated` 的 bbox 是 `[0,0,1920,1080]`（一个只画左侧文案的组不该有整屏框）。

**判据**：渲染后检查根节点 `lastElementChild` 是否符合预期；每个场景组的
`getBBox()` 尺寸是否合理；标签配平用开闭计数对比（注意注释里别写带尖括号的标签名，
会被正则数进去）。

**坑二：`setAttribute('transform')` 是整体覆盖。**

想把角色挂载点从 `foreignObject x/y` 改成 `<g transform="translate(960 96)">`，
结果角色跑到左上角。因为 `timeline.js` 每帧 `setAttribute('transform', matrix(...))`
是**替换**，HTML 里写的 translate 第一帧就被冲掉；而 matrix 的平移量是
`px - 960*scale`，scale=1 时正好为 0（设计上是给 x/y 已定位的 foreignObject 做补偿）。

**结论**：定位量要么全在元素 x/y 属性里，要么全在每帧 transform 里，不能一半一半。

**坑三：「DOM 可见、截图空白」的排查顺序。**

走了两条弯路：先怀疑截图时机（加双 rAF → 无效），再怀疑 foreignObject 跨层重绘
（换嵌套 svg → 数值一点没变）。弯路本身有价值：A/B/C/D 四种截图方式
（直接截 / 双 rAF / 双 rAF+300ms / CDP `Page.captureScreenshot`）**逐像素相同**，
一次性排除了合成时序假设。

正确顺序是**先验结构、再看像素**：结构对了再谈渲染，结构不对谈渲染全是白费。

**可复用判据**：多个不相关时间点同时缺内容 → 结构问题；
零星个别帧异常 → 才可能是合成/时序问题。

#### 新增的三个诊断工具

| 脚本 | 用途 |
|---|---|
| `promo/check-atri-frames.py` | 按区域算 ink/亮度标准差/边缘强度，代替目视验收 |
| `promo/diagnose-atri-groups.py` | 逐场景组打印 style/计算 opacity、bbox、屏幕矩形、`lastElementChild` |
| `promo/diagnose-atri-pet.py` | 打印角色真实 bbox 与 mount 矩形，查角色跑偏/被裁 |

#### 版权提醒

指定 BGM 是第三方版权曲目，已在 `.gitignore` 加 `promo/assets/*.mp3` 排除。
公开分发成片前须自行确认授权；不能使用时改用 `generate-atri-audio.py` 的原创曲。

### 2026-10-31 第三轮：放慢到 60 秒

用户评价 36 秒版"演示的太急促了，放慢一点，篇幅长一点无所谓，我又没限制你"。

改动：30 → 36 → **60 秒**（1800 帧）。信息量几乎没变，多出来的时间全给停顿和情绪递进。

#### 节奏硬规则（改时间轴时照抄）

| 规则 | 数值 | 上一版 |
|---|---|---|
| 单个表情展示 | ≥ 1.4 s | ~1.1 s |
| 同段相邻动作间隔 | ≥ 1.4 s | 1.1–1.4 s |
| 「萝卜子」每级递进 | ≥ 2.4 s | 1.5 s |
| 气泡第二行延迟 | 1.3 s | 0.55 s |
| 场景淡入 / 位移 | 0.5 s / 0.7 s | 0.34 s / 0.45 s |
| 出场横线伸展 | 1.4 s | 0.75 s |

#### 关键认识：动作间隔不是观感问题，是被拒收的问题

`kit/body.js` 的 `doWord()`：

```js
if (KIT_EXPRESSIONS.includes(w) || words[w]?.expression) {
  if (busy()) return false;      // 点击反应没播完，表情真的被丢掉
```

上一版没暴露是因为点击后只发了一个动作。这一版想在点击后连发表情，`busy()`
立刻拒收——**间隔太密会导致动作根本不出现在画面里**。

所以排时间轴的正确顺序是：先问"这个动作自己要播多久 + busy 什么时候释放"，
再去填画面。反过来（先排满画面再塞动作）必然撞 `busy()`。

渲染器的 `accepted` 检查就是为此存在的：任一为 false 直接中止，
不会产出一条"姿态静态冒充满动作"的哑音视频。

#### 分段表（60 秒）

| 段 | 时间 | 长度 |
|---|---|---|
| intro | 0–7 | 7 s |
| talk（三轮对话） | 7–22 | 15 s |
| touch（点击/提起） | 22–31 | 9 s |
| actions（八个表情） | 31–42 | 11 s |
| radish（萝卜子桥段） | 42–52 | 10 s |
| seated | 52–56 | 4 s |
| outro | 56–60 | 4 s |

对话从一轮扩到三轮（陪伴 / 撒娇 / 闹别扭，每轮 ~4.8 s），
表情 chip 从 4 个扩到 8 个（每个 1.4 s），
「萝卜子」桥段从 6.5 s 拉到 10 s，三级递进每级 2.4 s 以上。

#### BGM 重新裁剪

60 秒版：`-t 60`，2.0 s 淡入、56.5 s 起 3.5 s 淡出，
`loudnorm=I=-20:TP=-4:LRA=9`（源曲较响，比上一版的 −24 目标提高 4 dB 以保留动态）。

#### 抽样验证（17 个点）

```sh
python promo/render-atri.py --ffmpeg <ff> --browser <exe>   --samples 3,6,10,15,20,25,29,33,36,39,41,44,47,50,53,55,58
```

结果：17 采样点 / 359 次动作校验 / **0 拒绝**，像素检查 ALL OK。

### 2026-10-31 第四轮：表情段删掉「蹭蹭」与「生气」

用户：「表情演示删掉 00:26 的蹭蹭和生气演示（萝卜子生气那里不要动）」。

改动只在两张表上，萝卜子桥段一行没碰：

| 位置 | 改前 | 改后 |
|---|---|---|
| `atri-film.html` `#actionChips` | 8 个 chip（4+4 两排） | **6 个 chip（3+3 两排）** |
| `timeline.js` schedule 表情段 | 8 个动作，各 1.4 s | **6 个动作，各 1.77 s** |
| `timeline.js` `actIdx` 分档 | 8 档 | 6 档 |
| `timeline.js` `actTitles` | 8 条 | 6 条 |
| `timeline.js` chip 循环 | `< 8` | `< 6` |

删的是 `word('pout')`（38.4 s）与 `word('angry')`（41.2 s）。
删完 6 个动作分摊原来 10.6 秒的段落：31.4 / 33.1 / 34.8 / 36.5 / 38.2 / 39.9，
每个间隔 1.7 秒，**比原来 1.4 秒更慢**，符合上一轮「放慢」的要求。

萝卜子桥段（42–52 s）的 `word('pout')`（46.0 s）与 `word('angry')`（48.4 s）
**保持原样**，它是剧情推进的三级递进之一，不是 chip 演示。

#### 为什么该删「蹭蹭」

`packs/atri-v011/model.json` 的 `words` 里没有「蹭蹭」这个概念，它只是个 UI 标签。
写进 chip 却没有对应真实动画，等于演示了一个不存在的动作——这正是第 20 条
「`do()` 返回 false 会静默吞掉动作」的另一种表现：不是被拒收，而是**根本没得发**。

「生气」则相反，它是真实动作（`KIT_EXPRESSIONS` 里有 `angry`，带青筋与抖动），
删掉它是因为**位置不对**：在 chip 里一闪而过，不如放到萝卜子桥段当剧情结果有力。

#### 验证

```sh
python promo/render-atri.py --ffmpeg <ff> --browser <exe>   --samples 3,6,10,15,20,25,29,32,34,35,37,39,41,44,47,50,53,55,58
```

结果：19 采样点 / 385 次动作校验 / **0 拒绝**；
表情段（31–42 s）实际出现的动作集合为
`{wave, happy, dance, shy, surprised, dizzy}` —— **`pout` 与 `angry` 已消失**，
确认删除生效且没有残留；像素检查 ALL OK。

### 校验顺序（照抄即可）

```sh
npm run preview &                                          # 1. 起服务
python promo/generate-atri-audio.py                        # 2. 配乐
python promo/render-atri.py --ffmpeg <ff> --browser <exe> \
  --samples 1.5,6,12,16,23,28                              # 3. 关键帧，看字形/遮挡/构图
python promo/render-atri.py --ffmpeg <ff> --browser <exe> \
  --music promo/assets/atri-music.wav                      # 4. 完整渲染 + 全片解码
```

`samples` 模式还会写出 `assets/qa/atri-states.json`，里面每个采样点的 `checks` 给出该时刻所有动作的 `accepted`，用来确认"画面里真的做了这个动作"而不是只画了个静态姿势。
