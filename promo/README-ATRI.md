# 亚托利 · 60 秒宣传片

作者：**Asryto**

仓库：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design

最终视频：`assets/亚托利宣传片.mp4`，60 秒，1920 × 1080，30 fps，H.264 + AAC。

## 内容

展示 `packs/atri-v011`（v1.1.0 已验收发布版）的完整交互面，节奏刻意放慢，一个动作给足时间：

- **出场（0–7 s）**：挥手 → 注视 → 开心 → 眨眼，标题横线 1.4 秒慢慢展开；
- **三轮对话（7–22 s）**：陪伴 → 撒娇 → 闹别扭，每轮约 4.8 秒，两行台词间隔 1.3 秒出字，左下角有轮次指示点；
- **点击与提起（22–31 s）**：指针戳呆毛、停一下、再提起来 3 秒、松手落地；
- **八个表情（31–42 s）**：招手 / 开心 / 跳舞 / 害羞 / 惊讶 / 嘟嘴 / 晕乎 / 生气，每个 1.4 秒，chip 依次点亮；
- **「叫她萝卜子」桥段（42–52 s，本片重点）**：惊讶 → 嘟嘴 → 生气，三级递进每级 2.4 秒以上，右侧三步指示条同步点亮，生气时红色光晕压上来并伴随抖动；
- **坐姿与圈圈眼（52–56 s）**；
- **片尾（56–60 s）**：名称、作者、版本、安装指引。

对话气泡是示例文案，不调用真实聊天模型。

背景、光柱、气泡、水波、界面、字幕、指针与镜头全部是 `atri-film.html` 里的 SVG 矢量元素，用线性位移与透明度过渡驱动。亚托利本体保留发布包的原位图纹理和真实 kit 动画，因此角色画面不是重新绘制的纯矢量角色。

## 节奏为什么这么定

上一版 36 秒被评价「太急促」。这一版把每条规则写死，改时间轴时照抄：

| 规则 | 数值 |
|---|---|
| 单个表情展示 | ≥ 1.4 s |
| 同段相邻动作间隔 | ≥ 1.4 s |
| 「萝卜子」每级递进 | ≥ 2.4 s |
| 场景淡入 / 位移 | 0.5 s / 0.7 s |
| 气泡第二行延迟 | 1.3 s |

这不只是观感问题：`kit/body.js` 的 `doWord()` 在 `busy()` 时会**真的拒收**表情，
间隔太密动作会被丢掉。渲染器记录 `accepted`，任一为 `false` 直接中止。

## 配乐

成片使用 `szak - 親愛なるあの日々へ`，裁前 60 秒，2.0 s 淡入、56.5 s 起 3.5 s 淡出，loudnorm 到 −20 LUFS / TP −4。

**这是第三方版权曲目，没有进仓库**（`.gitignore` 有 `promo/assets/*.mp3`）。公开分发成片前请自行确认授权范围。若不能使用，改用本仓库的原创合成曲：

```sh
python promo/generate-atri-audio.py          # 生成 assets/atri-music.wav
python promo/render-atri.py ... --music promo/assets/atri-music.wav
```

## 查看和修改

在仓库根目录启动 `npm run preview`，打开：

`http://127.0.0.1:4319/promo/assets/src/02-atri/atri-film.html?review=1`

底部时间输入框可定位到任意时刻（0–59.9）。SVG 场景在 `assets/src/02-atri/atri-film.html`；
分镜、动作调用和插值在同目录 `timeline.js`；分镜表与硬约束见 [BRIEF.md](assets/src/02-atri/BRIEF.md)。

## 渲染

```sh
npm run preview    # 另开一个终端，保持运行

# 先看关键帧（改完时间轴务必先抽样，别直接跑全片）
python promo/render-atri.py --ffmpeg <ffmpeg> --browser <浏览器exe> \
  --samples 3,6,10,15,20,25,29,33,36,39,41,44,47,50,53,55,58

# 再完整渲染
python promo/render-atri.py --ffmpeg <ffmpeg> --browser <浏览器exe> \
  --music promo/assets/atri-bgm.mp3 --out "promo/assets/亚托利宣传片.mp4"
```

`--browser` 接受实际浏览器程序路径（Edge/Chrome 均可），不把制作者机器的路径写死给别人。
`--ffmpeg` 必须支持 `libx264` 与 `aac`。`--duration` 默认 60，上限 120。

完整渲染按 60 Hz 推进角色逻辑、以 30 fps 输出 1800 张截图，FFmpeg 编码后做全片解码检查。
临时截图自动清理，回执保存在 `assets/qa/atri-video-validation.json`。

### 辅助工具

| 脚本 | 用途 |
|---|---|
| `check-atri-frames.py` | 按区域统计 ink/亮度标准差/边缘强度，没眼睛看画面时用它代替目视 |
| `diagnose-atri-groups.py` | 逐场景组打印 style/计算 opacity、bbox、屏幕矩形、`lastElementChild`，专治「DOM 可见但截图空白」 |
| `diagnose-atri-pet.py` | 打印角色真实 bbox 与 mount 矩形，专治「角色跑偏或被裁掉」 |
| `generate-atri-audio.py` | 原创合成配乐，无第三方采样（版权替代方案） |

中文字形使用 Windows 的 Microsoft YaHei。其他机器须有支持简体中文的字体并在 SVG 样式中指定实际可用字体；先抽帧检查缺字和排版。

## 素材归属

- 角色与特效：`packs/atri-v011`，见该包 `VERSION.md`、`SOURCE.json`、`LICENSE`。
- 背景、界面、字幕、指针：`promo/assets/src/02-atri/atri-film.html` 内联 SVG。
- 配乐：第三方版权曲目，仅本机渲染使用，**不入库**。原创替代见 `promo/generate-atri-audio.py`。
