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
