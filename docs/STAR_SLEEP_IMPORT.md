# 星眠 0.1.0 源素材导入与打包

本次交付提供两份压缩包：

- `star-sleep-source-0.1.0.zip`：完整角色工程源文件、母版、缩略图、配准与运行文件。
- `star-sleep-0.1.0-preview.zip`：可在 Coopanion「装扮 → 导入」中选择的形象包。

## 将源素材放入 GitHub 工作区

1. 克隆仓库并切换到 `design/star-sleep-v0.1.0` 分支。
2. 将源素材归档解压到仓库根目录，允许合并同名目录。
3. 确认出现 `characters/star-sleep-01/art-source/master.png`、`characters/star-sleep-01/thumbnail-upper.png`、`packs/star-sleep-01-v001/tex/star-sleep.png` 和 `packs/star-sleep-01-v001/thumb.png`。
4. 本轮图像二进制未通过 GitHub 内容 API 上传，需从源素材归档补入并单独提交。远程分支上的规格与运行文本文件需同这些图像素材合并后才构成完整可运行包。

## 重新打包

从仓库根目录运行：

```sh
python scripts/package-star-sleep.py
```

脚本校验 API 2 manifest、vocab、画布、透明通道和母版 SHA-256，再生成 `dist/star-sleep-0.1.0.zip` 与 SHA-256 文件。

## 当前验收边界

本版本是完整原画单图层预览：已保存母版与 API 2 运行适配器，尚未拆出头发、眼睛、手臂、腿或坐姿源图。需要独立动作前，必须以母版为锚点完成透明补绘、层级归属、同画布配准和动作极值检查。不能通过矩形裁切或编造隐藏像素来伪造这些层。
