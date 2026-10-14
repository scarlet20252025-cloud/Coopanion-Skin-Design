# 工具选择与环境

以下是本次实际使用及可复制的路线。外部服务和技能的可用性可能变化；工具存在不等于本角色用它制作过。

| 任务 | 使用的工具 | 输入/输出 | 何时需要 |
| --- | --- | --- | --- |
| 母版/定点补画 | 会话 imagegen | 完整参考+问题区+逐字提示词 → 原始透明 PNG | 真正需要新像素时 |
| 配准 | OpenCV ECC + NumPy | 固定未编辑区域 → 矩阵/相关系数 | 编辑图坐标漂移时 |
| 遮罩/合成/导出 | Pillow、Canvas 2D | 源/alpha/矩阵 → 注册部件 | 不用它凭空重画插画 |
| 可编辑层记录 | ORA、PNG、JSON、提示词 | 部件和变换；本次旧 ORA 是历史小样 | 提交真正使用的层，不把失败 ORA 当母版 |
| 运行与预览 | Node 静态服务 + 官方 kit/rig | pack → 浏览器动作 | 所有动作修改 |
| 检查/ZIP | Python 标准库 + Node | source lock/manifest → 检查/ZIP/hash | 无需绘画依赖 |
| 视觉 QA | 完整角色截图、深浅底、接触表 | PNG/dataURL → 报告与放大图 | 所有像素或遮挡修改 |
| 真实宿主 | Coopanion API 2 导入/装扮页 | ZIP → 安装+运行 | 发布前；不要只看预览 |
| 宣传片 | SVG 场景、离线 Chromium、FFmpeg | 60 Hz 时间轴 → 30 fps 截图 → MP4 | `promo/render.py` |
| 技能检索 | find-skills | 任务关键词 → 阅读候选来源 | 工具不足时，不自动安装全部搜索结果 |
| 经验封装 | skill-creator 的渐进披露结构 | 短技能入口+指南+脚本+案例 | 本工程库采用此方法 |

See-Through、PSD2Live、Auto_Vtb、Krita 在早期研究中出现，但没有证据证明用于本龙娘的最终生产。它们不是预览/打包依赖。Coopanion 形象包也不是 Cubism 工程或 ChatGPT Pets 的固定方向 sprite sheet。

## 最小环境

```sh
python engineering/tools/project.py doctor
```

运行/打包只需 Node 和 Python。处理美术时才安装：

```sh
python -m venv .venv
# Windows
.venv/Scripts/python -m pip install -r requirements-art.txt
# macOS/Linux
.venv/bin/python -m pip install -r requirements-art.txt
python engineering/tools/project.py doctor --art
```

脚本实际使用哪个解释器，就在该解释器下运行 doctor。不要看到系统解释器有 Pillow 就假设项目 venv 也有。

## 成本更低的取舍

- 已有已验证素材：直接加载 PNG，不重跑图像生成。
- 调动作：改生效参数/代码，不碰素材生成脚本。
- 隐藏区欠缺：局部补画，先完整人物设计，再分离。
- 需要新工具：先读技能和依赖、用一个小样验证；本任务的 find-skills 检索未找到比短入口/契约/脚本结构更贴合的外部教程，采用现有 skill-creator。
- FFmpeg、浏览器、uv 使用可配置路径，不硬编码制作者机器的盘符；工程库不保存凭据。
