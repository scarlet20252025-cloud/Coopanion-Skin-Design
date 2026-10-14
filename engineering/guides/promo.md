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
