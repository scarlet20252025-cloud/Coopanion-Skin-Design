# 安装与交付：v005-r06 / 0.6.6-preview

这是可以导入 Coopanion 的开发包。母版、美术参数没有在本轮验收中重绘；最终视觉验收、独立嘴型和完整桌面窗口测试仍未完成。

## 最短使用路线

1. 克隆本仓库。在根目录运行 `npm run preview`，打开 `http://127.0.0.1:4319/`，进入动作预览。只需要 Node；不需要 npm install、图像 API 或 GPU。
2. 运行 `npm run check`，再运行 `python scripts/package-pet.py`。打包只用 Python 标准库，不需要 Pillow 或 OpenCV。
3. 得到 `dist/gpt-dragon-v005-r06-0.6.6-preview.zip` 和同名 `.zip.sha256`。在 Coopanion 的形象导入入口选择 ZIP，确认名称为 GPT 龙娘 v005 r06，再按需选用。不要导入历史失败的 `packs/gpt-dragon`。

ZIP SHA-256：`b08e2c0c30c590ccb261288b417a7b30f3633d64589eaf1c9a5529631f4ad0ca`。同一源码重复打包应得到相同哈希。ZIP 位于本地忽略目录，不随 Git 提交；其他人按上面一条命令生成即可。

## 已执行的验收

| 范围 | 结果 | 证据 |
| --- | --- | --- |
| 原画版本与参数 | v005 哈希锁定；待机 0.7、跳跃 0.65 未漂移 | `npm run check` |
| 左右朝向视觉抽查 | 96 张交互采样帧、6 张放大关节图 | `characters/original-01/rig-v005-r06/qa-interactions-v066/` |
| 真实导入 | 0.6.6 已导入本机 Coopanion | 包 ID `gpt-dragon-v005-r06` |
| 安装文件一致性 | 27 个文件与工作区一致 | `installed-files-v066.json` |
| 官方沙箱词表 | 18 个词各 120 次 tick 回执，无错误 | `installed-sandbox-v066.json` |
| 宿主输入协议与重载 | 13 项通过 | `installed-interactions-v066.json` |

后三份报告在 `characters/original-01/rig-v005-r06/`。视觉抽查不是逐帧全检，沙箱回执不是美术验收。

## 在自己的机器上复核

先启动并导入到 Coopanion，再运行 `python scripts/verify-installed.py`。脚本只读默认本机 7797 端口；若安装目录、端口或包版本不同，会失败而不是自动替换应用中的资产。

打开 `http://127.0.0.1:4319/preview/installed-r06.html`。依次运行词表检查、宿主交互检查，保存报告。它加载实际应用提供的沙箱和贴图；模型参数来自当前仓库，所以运行前必须先通过文件一致性检查。检查页不会切换当前桌宠。

完整桌面验收仍须在选用龙娘后完成：

- 用真实鼠标拎起、松手及点击睡眠中的角色，确认窗口命中与动作一致。
- 如有多个显示器，检查跨屏拖拽、窗口缩放和不同 DPI；沙箱 drop 消息无法覆盖这些系统行为。
- 正常退出并重开 Coopanion，确认仍选中本角色、贴图加载正常且无残留拖拽状态。
- 观察走跑、招手、站坐和跳跃的连续动态；发现问题时记录版本、朝向、动作及关键帧。

这几项目前未标记通过。不要把重新加载检查页写成应用进程重启通过。

## 修改而不重做

编辑 `characters/original-01/rig-v005-r06/motion-config.json` 或 `behavior-config.json`，运行 `python scripts/sync-r06-config.py`，再检查受影响的动作。源图不变时无需重新生成、分层、配准或采集官方参考帧。

详细制作路线与失败案例见 [实做工作流](REUSABLE_WORKFLOW.md)。
