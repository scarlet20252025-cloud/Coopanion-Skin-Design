# 检查、安装和交付

## 分开报告四种结论

| 项目 | 能证明 | 不能替代 |
| --- | --- | --- |
| 静态机器检查 | hash、文件、清单、矩阵、资源和脚本契约 | 美术自然性 |
| 视觉采样 | 所采样状态下完整角色/局部是否有缺陷 | 所有中间帧、系统鼠标路由 |
| 用户选择/接受 | 明确选定的形体、姿态、版本 | 后来所有变更都自动被接受 |
| 真实宿主 | 导入、安装文件和实际运行 | 未测过的多屏、DPI、进程重启 |

不要复述 model 内历史 `rest_pixel_mismatches=0` 作为新坐姿或重绘身体的结果。记录测量版本和输入 hash。

## 当前包检查

```sh
python engineering/tools/project.py check
python engineering/tools/project.py check --strict-assets
python scripts/package-pet.py
```

严格资产检查比较发布基线的贴图 hash。编辑产生差异时，普通检查会列出变更；严格检查失败是预期提醒。先完成有版本的视觉验收，再显式更新资产记录，不为了绿灯随意改 hash。

## 采样与看图

通用预览 `preview/engineering.html` 支持当前/实验包、左右朝向和 QA 下载；r25 专用预览保留详细历史动作检查。导出的 JSON 必须带版本、master hash、动作返回值、朝向、时间及图像。

```sh
python engineering/tools/project.py qa --input downloaded-qa.json --out scratch/qa/review
```

此命令需要 Pillow，写完整浅/深背景图、接触表与数值摘要。它检查脚本能判断的有限数值/动作返回值；**不自动判断图像无缝**。再按症状检查肩袖、脖领、呆毛、刘海、裙腿、翼根；必须同时看全身和放大，而不是只挑一张好看的图。

## 实际导入与一致性

Coopanion「装扮 → 导入」导入 ZIP，选用当前形象。ZIP 根目录含 `figure.json`；API 2 词表每项需要正数 seconds。当前形象 pack id 保持 `gpt-dragon-v005-r25`，名字 GPT 龙娘，作者 Asryto。新角色使用自己的 id。

```sh
python engineering/tools/project.py compare --installed /absolute/path/to/companion/data/figures/gpt-dragon-v005-r25
```

只读所指定的安装目录，不读取 `.env` 或整份宿主配置。更换目录、端口、版本后重新确认。GET `/api/figures/status` 可验证扫描问题；`/dress` 可检查沙箱渲染。当前本机 7797 是运行实例事实，不是所有安装的默认保证。

目录替换前备份精确目标；旧包清理只处理用户指定的旧龙娘，保留 coo/whale。源码、失败证据和用户个人配置不能作为“旧版本”随手删除。重载形象不是应用进程重启。

## 字节一致的源码与打包

当前 pack 在 .gitattributes 中关闭换行转换，防止 Windows 的 autocrlf 改变 Release 文件字节。以暂存源码导出的干净目录重新打包，ZIP 的 SHA-256 与已发布 1.0.2 一致。不要在复制时自动格式化发布文件。

## Release

公开交付应同时给出名称、版本、作者、主程序/形象包区别、安装步骤、ZIP、SHA-256 与源码。用明确的 tag/commit，上传完成后经公开地址下载校验；未知结果先查是否已存在，不重复创建或覆盖冲突资产。

GPT 龙娘 v1.0.2 已发布并公开下载校验：`docs/github-release-v1.0.2.json`。这是一次验证记录，不保证所有未来下载或 API 状态不变。

简介范例：

```text
GPT 龙娘是 Coopanion 的桌宠形象包，下载 ZIP 后在「装扮 → 导入」中安装。
形象包：https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design/releases/tag/v1.0.2
主程序：https://github.com/Pal-AI-Lab/Coopanion
```

视频投稿未由本助手完成。浏览器登录、素材上传、表单填写、公开提交与 Release 是各自的外部动作，按用户当次授权处理；不能由教程推定一律获准发布。
