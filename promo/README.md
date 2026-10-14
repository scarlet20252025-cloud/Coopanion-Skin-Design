# GPT 龙娘 · 30 秒宣传片

作者：**Asryto**

仓库：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design

最终视频：`assets/GPT 龙娘宣传片.mp4`，30 秒，1920 × 1080，30 fps，H.264 + AAC。

## 内容

展示当前 1.0.2 形象包的招手、点击、提起挣扎、振翅、跳舞音符、坐姿和圈圈眼晕乎。对话气泡使用示例文案，并调用 Coopanion kit 的回应动作。不会调用真实聊天模型。

背景、界面、字幕、指针和镜头由 SVG 矢量元素组成，使用线性位移与透明度过渡。龙娘保留发布包的原位图纹理及实际动画逻辑，因此角色画面并非重新绘制的纯矢量角色。原创背景音由 `generate-audio.py` 合成，无第三方采样。

## 查看和修改

在仓库根目录启动 `npm run preview`，打开：

`http://127.0.0.1:4319/promo/assets/src/01-film/01-film.html?review=1`

使用底部时间输入框定位到任意时刻，或点击播放。SVG 场景在 `assets/src/01-film/01-film.html`；分镜、动作调用和线性插值在同目录 `timeline.js`；制作要求见 `BRIEF.md`。

## 渲染

仓库自带 `render.py`，路径与浏览器均可配置，不依赖本机旧技能副本。运行前启动预览服务，安装 uv、FFmpeg，并准备 Playwright Chromium（或使用现有浏览器的 `--browser` 绝对路径）：

```sh
uv sync --project promo
uv run --project promo playwright install chromium
uv run --project promo python promo/generate-audio.py
uv run --project promo python promo/render.py --ffmpeg /path/to/ffmpeg --music promo/assets/original-music.wav --out "promo/assets/GPT 龙娘宣传片.mp4"
```

先检查关键帧可加 `--samples 0.7,6,12,14.7,23,28`。完整渲染按 60 Hz 推进角色逻辑，以 30 fps 输出 900 张截图，FFmpeg 编码后进行全片解码检查。临时截图自动清理，回执保存在 `assets/qa`。

本次重做加入 1.0.2 招手耳后发修复。背景音改为柔和、轻快的原创钢琴感合成旋律：104 BPM、平缓起音、弱高频、无噪声打击；成片音量目标 -24 LUFS，峰值上限 -3 dBTP。声音舒适度仍是主观判断。

完整流程、真实动作与示例气泡的边界见 [宣传片指南](../engineering/guides/promo.md)。

## 技能和来源

- [find-skills](https://github.com/vercel-labs/skills/tree/main/skills/find-skills)：已用于技能检索并安装到用户技能目录。
- [animation-builder](https://github.com/ShawhinT/non-coding-skills/tree/main/animation-builder)：本轮参考并使用其逐帧截图及 FFmpeg 合成管线。
- 龙娘使用仓库 `packs/gpt-dragon-v005-r25`；Coopanion kit 及特效来源与许可见该包的 `UPSTREAM.json`、`LICENSE` 和 `preview/vendor`。

采用用户指定的线性运动，覆盖技能默认缓动建议。技能未要求的实时用户界面操作没有加入制作流程。
