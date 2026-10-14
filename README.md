# GPT 龙娘 · Coopanion 形象包

作者：**Asryto**  
仓库：[Coopanion-Skin-Design](https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design)  
当前发布版：**1.0.2**，形象名称：**GPT 龙娘**。

银白浅紫 Q 版龙娘桌宠，支持 39 个动作与表情标签，包含独立眉毛、点击呆毛晃动、情绪振翅、提起挣扎、招手、原坐姿及圈圈眼晕乎。封面采用上半身近景。采用 Coopanion 官方 kit 驱动行为，源素材与配准围绕锁定 v005 母版维护。

## 安装与打包

在 Coopanion「装扮 → 导入」中选择形象 ZIP，再选用「GPT 龙娘」。安装包根目录包含 `figure.json`、作者与仓库说明。

从仓库生成安装包，仅需 Python 标准库：

```sh
python scripts/package-pet.py
```

输出为 `dist/gpt-dragon-v005-r25-1.0.2.zip` 与校验文件；与交付文件 `GPT 龙娘 1.0.2.zip` 内容相同。ZIP 不随 Git 提交。当前源码在 [`packs/gpt-dragon-v005-r25`](packs/gpt-dragon-v005-r25)。

## 本地预览与检查

```sh
npm run preview
npm run check
```

预览只需 Node.js，无需 npm install。打开 `http://127.0.0.1:4319/preview/dragon-r25.html`，检查动作、表情、深浅背景及采样帧。`npm run check` 校验母版、历史参数约定与当前发布元数据；不替代视觉检查。

已验证本机 Coopanion 的安装文件一致性、装扮页渲染和当前形象选择。呆毛清理与音符检查覆盖 64 张动态采样。多屏、不同 DPI 和应用进程重启尚未完整验收。

## 说明与来源

- [安装、更新与复核](docs/INSTALL_AND_VERIFY.md)
- [当前版本记录](docs/RELEASE_NOTES.md)
- [制作方法与失败复盘](docs/REUSABLE_WORKFLOW.md)
- [分件归属与遮挡要求](docs/LAYER_OWNERSHIP_AND_OCCLUSION.md)
- [母版锁定](characters/original-01/production-lock.json)
- [上游来源及许可](packs/gpt-dragon-v005-r25/UPSTREAM.json)

角色制作署名为 Asryto；上游代码署名与 AGPL 许可保留在包内。历史版本和失败案例用于制作记录，当前预览、打包和安装应使用 r25。
