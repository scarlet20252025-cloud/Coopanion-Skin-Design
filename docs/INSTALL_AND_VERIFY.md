# GPT 龙娘 · 安装与交付

当前版本：**1.0.2**；作者：**Asryto**。  
仓库：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design

## 导入与更新

1. 获取交付文件 `GPT 龙娘.zip`，或从仓库运行 `python scripts/package-pet.py` 生成 `dist/gpt-dragon-v005-r25-1.0.2.zip`。
2. 打开 Coopanion「装扮 → 导入」，选择 ZIP；选用「GPT 龙娘」。ZIP 根目录直接包含 `figure.json`，无需解压后再压缩外层文件夹。
3. 当前 ID 固定为 `gpt-dragon-v005-r25`。升级替换同 ID 包；如果应用提示重名，按应用提示更新或先移除同 ID 旧条目再导入。旧 r06–r18 条目可从装扮列表移除。

安装包包含作者、仓库地址、版本说明、完整贴图、脚本及上游许可。半身封面在 `thumb.png`；源码地址另见 `SOURCE.json`。

## 从仓库预览

```sh
npm run preview
npm run check
python scripts/package-pet.py
```

预览只需 Node.js，打包只需 Python 标准库。打开 `http://127.0.0.1:4319/preview/dragon-r25.html`。当前包自带配准配置，并从宿主提供的 model 读取；不要恢复会被宿主 CSP 禁止的配准 JSON fetch。

## 已执行的检查

- v005 母版 SHA-256 与生产锁一致，39 个标签各有正数时长。
- 本机 Coopanion 已安装并选用 GPT 龙娘，装扮页正确渲染；安装文件与交付 ZIP 逐文件一致。
- 1.0.1 抽查 64 张晕乎、点击、跳舞、转向采样，复查完整角色与深色背景呆毛根部；确认跳舞音符由官方 kit 产生。
- 1.0.2 更新署名、来源、文档与包元数据，沿用 1.0.1 形象素材及动画。

采样检查不等于全帧检查。多屏拖拽、不同 DPI、正常退出并重启应用，仍需在目标机器上复核。旧 r06 专用验证脚本和报告是历史证据，不能当作当前 r25 的验证报告。

详细版本记录见 [RELEASE_NOTES.md](RELEASE_NOTES.md)，制作方法见 [REUSABLE_WORKFLOW.md](REUSABLE_WORKFLOW.md)。
