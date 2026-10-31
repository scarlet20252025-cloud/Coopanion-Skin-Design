# 亚托利 · 36 秒宣传片

作者：**Asryto**

仓库：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design

最终视频：`assets/亚托利宣传片.mp4`，36 秒，1920 × 1080，30 fps，H.264 + AAC。

## 内容

展示 `packs/atri-v011`（v1.1.0 已验收发布版）的完整交互面：

- **三轮对话**：陪伴 → 撒娇 → 闹别扭，气泡逐行出字，左下角有轮次指示点；
- **点击与提起**：指针戳呆毛、提起来后挣扎、松手落地；
- **八个表情动作**：招手 / 开心 / 跳舞 / 害羞 / 惊讶 / 嘟嘴 / 晕乎 / 生气，chip 依次点亮；
- **「叫她萝卜子」桥段**（23.5–30 s，本片重点）：惊讶 → 嘟嘴 → 生气，三级递进，右侧三步指示条同步点亮，生气时红色光晕压上来并伴随抖动；
- **坐姿与圈圈眼**：自然坐下，切到晕乎状态。

对话气泡是示例文案，不调用真实聊天模型。

背景、光柱、气泡、水波、界面、字幕、指针与镜头全部是 `atri-film.html` 里的 SVG 矢量元素，用线性位移与透明度过渡驱动。亚托利本体保留发布包的原位图纹理和真实 kit 动画，因此角色画面不是重新绘制的纯矢量角色。

## 配乐

成片使用 `szak - 親愛なるあの日々へ`，裁前 36 秒，1.2 s 淡入、33.5 s 起 2.5 s 淡出。

**这是第三方版权曲目，没有进仓库**（`.gitignore` 里有 `promo/assets/*.mp3`）。公开分发成片前请自行确认授权范围。若不能使用，改用本仓库的原创合成曲：

```sh
python promo/generate-atri-audio.py          # 生成 assets/atri-music.wav
python promo/render-atri.py ... --music promo/assets/atri-music.wav
```

## 与 GPT 龙娘那支的差别

同一套管线（逐帧截图 → FFmpeg 编码 → 全片解码校验），这一版在这几处做了升级：

- **时长更足**：36 秒 / 1080 帧，多出的 6 秒全给了交互演示和「萝卜子」桥段；
- **背景有纵深**：三层视差光柱、34 个确定性上浮气泡（固定种子，可复现）、7 条漂移水波、径向光晕与暗角；
- **镜头会动**：对话段缩到 0.66 给气泡让位，坐姿段重心上移，片尾略收，指针坐标跟着缩放联动；
- **情绪有层次**：生气不是一步到位，而是惊讶→嘟嘴→生气三级推进；
- **动作失败即中止**：任一 `body.do(word)` 返回 false 直接抛错，不会产出哑音视频；
- **配乐可替换**：`--music` 传任意音频，自动 loudnorm 到 −24 LUFS。

分镜和硬约束见同目录 [BRIEF.md](assets/src/02-atri/BRIEF.md)。

## 查看和修改

在仓库根目录启动 `npm run preview`，打开：

`http://127.0.0.1:4319/promo/assets/src/02-atri/atri-film.html?review=1`

底部时间输入框可定位到任意时刻（0–35.9）。SVG 场景在 `assets/src/02-atri/atri-film.html`；分镜、动作调用和插值在同目录 `timeline.js`。

## 渲染

```sh
npm run preview    # 另开一个终端，保持运行

# 先看关键帧（强烈建议：改完时间轴先抽样，别直接跑全片）
python promo/render-atri.py --ffmpeg <ffmpeg> --browser <浏览器exe> \
  --samples 2,6,9,11.5,16,20,22.5,25,28,31.5,35

# 再完整渲染
python promo/render-atri.py --ffmpeg <ffmpeg> --browser <浏览器exe> \
  --music promo/assets/atri-bgm.mp3 --out "promo/assets/亚托利宣传片.mp4"
```

`--browser` 接受实际浏览器程序路径（Edge/Chrome 均可），不把制作者机器的路径写死给别人。`--ffmpeg` 必须支持 `libx264` 与 `aac`。`--duration` 默认 36，上限 60。

完整渲染按 60 Hz 推进角色逻辑、以 30 fps 输出 1080 张截图，FFmpeg 编码后进行全片解码检查。临时截图自动清理，回执保存在 `assets/qa/atri-video-validation.json`。

### 三件辅助工具

| 脚本 | 用途 |
|---|---|
| `check-atri-frames.py` | 按区域统计 ink/亮度标准差/边缘强度，没眼睛看画面时用它代替目视 |
| `diagnose-atri-groups.py` | 逐场景组打印 style/计算 opacity、bbox、屏幕矩形，专治「DOM 可见但截图空白」 |
| `diagnose-atri-pet.py` | 打印角色真实 bbox 与 mount 矩形，专治「角色跑偏或被裁掉」 |

中文字形使用 Windows 的 Microsoft YaHei。其他机器须有支持简体中文的字体并在 SVG 样式中指定实际可用字体；先抽帧检查缺字和排版。

## 素材归属

- 角色与特效：`packs/atri-v011`，见该包 `VERSION.md`、`SOURCE.json`、`LICENSE`。
- 背景、界面、字幕、指针：`promo/assets/src/02-atri/atri-film.html` 内联 SVG。
- 配乐：第三方版权曲目，仅本机渲染使用，**不入库**。原创替代见 `promo/generate-atri-audio.py`。
