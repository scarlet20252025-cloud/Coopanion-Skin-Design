# 亚托利 · 30 秒宣传片

作者：**Asryto**

仓库：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design

最终视频：`assets/亚托利宣传片.mp4`，30 秒，1920 × 1080，30 fps，H.264 + AAC。

## 内容

展示 `packs/atri-v011`（v1.1.0 已验收发布版）的招手出场、桌面对话、点击呆毛、提起挣扎、招手/开心/跳舞/害羞、坐姿与圈圈眼晕乎。对话气泡是示例文案，不调用真实聊天模型。

背景、光柱、气泡、水波、界面、字幕、指针与镜头全部是 `atri-film.html` 里的 SVG 矢量元素，用线性位移与透明度过渡驱动。亚托利本体保留发布包的原位图纹理和真实 kit 动画，因此角色画面不是重新绘制的纯矢量角色。配乐由 `generate-atri-audio.py` 原创合成，无第三方采样。

## 与 GPT 龙娘那支的差别

同一套管线（逐帧截图 → FFmpeg 编码 → 全片解码校验），但这一版在这几处做了升级：

- **背景有纵深**：三层视差光柱、34 个确定性上浮气泡（同一个种子永远得到同一帧，可复现）、7 条漂移水波、径向光晕与暗角。
- **镜头会动**：对话段缩到 0.66 给气泡让位，坐姿段重心上移，片尾略收，指针坐标跟着缩放联动。
- **动作失败即中止**：任一 `body.do(word)` 返回 false 直接抛错，不会产出一条哑音视频。
- **配乐更克制**：92 BPM 水下 A 大调五声，低频水压床打底，水铃只出现在段落切换处。

分镜和硬约束见同目录 [BRIEF.md](assets/src/02-atri/BRIEF.md)。

## 查看和修改

在仓库根目录启动 `npm run preview`，打开：

`http://127.0.0.1:4319/promo/assets/src/02-atri/atri-film.html?review=1`

底部时间输入框可定位到任意时刻。SVG 场景在 `assets/src/02-atri/atri-film.html`；分镜、动作调用和插值在同目录 `timeline.js`。

## 渲染

```sh
npm run preview    # 另开一个终端，保持运行

python promo/generate-atri-audio.py

# 先看关键帧
python promo/render-atri.py --ffmpeg <ffmpeg> --browser <浏览器exe> \
  --samples 1.5,6,12,16,23,28

# 再完整渲染
python promo/render-atri.py --ffmpeg <ffmpeg> --browser <浏览器exe> \
  --music promo/assets/atri-music.wav --out "promo/assets/亚托利宣传片.mp4"
```

`--browser` 接受实际浏览器程序路径（Edge/Chrome 均可），不把制作者机器的路径写死给别人。`--ffmpeg` 必须支持 `libx264` 与 `aac`。

完整渲染按 60 Hz 推进角色逻辑、以 30 fps 输出 900 张截图，FFmpeg 编码后进行全片解码检查。临时截图自动清理，回执保存在 `assets/qa/atri-video-validation.json`。

中文字形使用 Windows 的 Microsoft YaHei。其他机器须有支持简体中文的字体并在 SVG 样式中指定实际可用字体；先抽帧检查缺字和排版。

## 素材归属

- 角色与特效：`packs/atri-v011`，见该包 `VERSION.md`、`SOURCE.json`、`LICENSE`。
- 背景、界面、字幕、指针：`promo/assets/src/02-atri/atri-film.html` 内联 SVG。
- 配乐：`promo/generate-atri-audio.py` 合成，无第三方采样。
