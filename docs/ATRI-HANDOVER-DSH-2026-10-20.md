# ATRI 桌宠 · DSH 会话交接（2026-10-20）

> 本文由 **DeepSeek Harness（DSH）会话**写于 2026-10-20，作用是继承
> `C:\Users\63526\Desktop\codex-ATRI皮肤-提取.md`（Codex 会话
> `rollout-2026-10-16T14-32-25-01a14369-6f66-7300-9d1b-04cd9a8f7a03.jsonl` 的完整提取，
> 15590 行）的全部工作记录，并把「仓库内工作记录 + 可用工具链」固化下来。
> 与 `docs/HANDOVER-ATRI-2026-10-16.md` 并列：**那一篇是工程交接，这一篇是会话/状态交接**。
> 冲突时以本仓库实际文件与实测为准。

---

## 0. 本会话做了什么

| 项 | 状态 |
|---|---|
| 读取并继承 Codex 会话提取文件（15590 行） | 完成 |
| 核对素材库仓库状态、候选包、版本注册、回滚备份 | 完成（见 §1–§3） |
| 把 Codex 会话「用户指示 / 已完成 / 下一步」写进仓库 | 本文 |
| 启动 8765 预览静态服务 | 完成（HTTP 200 已验证） |
| 验证 `build-diagnostic.py` 重建 + `node` 导入 | 完成（40 贴图，IMPORT OK） |
| 验证出图通道（imagegen CLI / openai / 密钥） | 完成（12 个模型可见，含 `gpt-image-2.5-sunburst`） |
| 建立 DSH 接手基线版本快照 | 完成（`atri-pure-components-01-3`） |
| 推送到 GitHub | 完成（走本机代理 `127.0.0.1:7897`，见 §6） |

---

## 1. 位置与当前状态

| 内容 | 值 |
|---|---|
| 仓库（本地） | `D:\Codex\Coopanion-Skin-Design` |
| 仓库（远端） | `https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design`（main） |
| HEAD | `3150575` — Withdraw the from-scratch lid model, restore the 22:21 face baseline, and version candidates（2026-10-19 00:22） |
| 回滚保险点 | git tag `backup-before-rollback-20261017` → `e544428` |
| 22:21 基线提交 | `01ee8f6` — Move the drawn face into a tracked file, and give 大哭 the official mouth |
| 当前候选包 | `scratch/candidates/atri-pure-components-01`（**40 贴图 / 40 零件**，node 导入通过） |
| 版本快照 | `scratch/candidates/atri-pure-components-01-2`（40 贴图，备注「22:21 baseline (01ee8f6)…」） |
| 版本注册表 | `scratch/versions/registry.json` |
| 预览 | `http://127.0.0.1:8765/preview/engineering.html?pack=scratch/candidates/atri-pure-components-01` |
| 回滚备份目录 | `scratch/rollback-backup-20261017/`（未删除，可恢复） |

**候选包状态**：未安装、未发布、未做用户美术验收。`scratch/` 被 `.gitignore` 忽略，不进仓库。

---

## 2. 用户明确指示（按时间顺序，全部仍然有效）

来自 Codex 会话，逐条保留原意：

1. 害羞的眼睛大小和制作流程**不合规**，要找回主工程方案。
2. **回滚到 10 月 16 日 22:21 左右**（提交 `01ee8f6`），从「开始改大哭表情和坐姿表情」处重做。
3. 重新按**母版**生成，替换**所有不合格**的表情。
4. **禁止使用裁切工具**；尽可能不用裁切，按官方鲸鱼娘规则做。
5. 生气表情崩坏了 → **按就方案重新生成**，不要所有表情都完全从零生成。
6. **只替换不合格的**，不要整体推倒；要具备合格审美判断，不要断记忆。
7. **预览工程必须分版本**，否则会造成严重验证损失。
8. （最后一条，2026-10-19）**先别工作，把当时要求的工作记录先保存到仓库** —— 本文件即为此项。

---

## 3. 已完成（截至本会话）

### 3.1 回滚到 22:21 基线

- `expression-face.js` / `build-diagnostic.py` / `renderer-template.js` 三件套用
  `git checkout 01ee8f6 --` 恢复到 22:21 基线。
- 22:21 之后的产物全部**移到** `scratch/rollback-backup-20261017/`（未删除）：
  - `new-art/`（`happy-arc-0/1.png`，即「新生成笑眼」素材）
  - `restore-smiling-eyes.py`（旧工程裁切恢复脚本）
  - `eye-layers/`、`split-eye-layers.py`、`eye-geometry.json`（被撤销的「从零眼睑模型」）
  - `tex-orphans/`、`tex-orphans-2/`（8 张 `*-lash/ball.png`、2 张 `happy-arc-*.png`）
- 包内孤儿贴图已清出，现为 40 贴图 / 40 零件。
- 预览已验证：42 个按钮、无控制台报错、`lidPaths=0`，**生气已恢复正常**（不再有眼角黑色撕裂）。

### 3.2 候选版本化（用户第 7 条指示）

新增 `scripts/snapshot-candidate.py`：

```
python scripts/snapshot-candidate.py <candidate-name> "<note>"
```

- 复制当前候选为 `scratch/candidates/<name>-N`；
- 在快照里写 `VERSION.md`（来源提交号、母版 sha256、每张贴图哈希）；
- 维护 `scratch/versions/registry.json`（按贴图指纹去重，避免同状态重复入册）。

---

## 4. 官方鲸鱼娘规则（核心，来自复现包 docs/07、kit/body.js、whale/figure.js）

> 复现包在仓库内：`references/whale-coopanion-repro-kit/`。

**脸部模型**：表情**不缩放整只眼**，轮廓固定，只降眼睑 + 移瞳孔。

```
open   = clamp(ry / rx, 0, 1)
drop   = (1 - open) * travel
travel = max(rimFit - lidFit) + 2
lash   : sy = .55 + .45 * open        # 睫毛随眼睑下移并压扁
```

官方 FACES 眼部参数（中性 ring = 16/16）：

| 表情 | 参数 | open |
|---|---|---|
| shy | ring(rx 13, ry 12, dx −3, dy +5) | 12/13 ≈ .92 |
| angry | ring(ry 11, dy 4) | 11/16 ≈ .69 |
| sad | ring(ry 14, dy 4) | .875 |
| worried | ring(ry 17, dy 2) | 1.06 |
| determined | ring(ry 13, dy 1) | .81 |
| thinking | ring(rx 14, ry 15, dx 3, dy −4) | .94 |
| pout | ring(rx 14, ry 13) | .93 |
| smug | lid(ry 8, dx 4) | .50 |
| listening | ring(rx 17, ry 18, dy −1) | 1.06 |
| surprised | ring(rx 20, ry 21) | 1.05 |
| excited | ring(rx 18, ry 19, dy −1) | 1.06 |
| scared | ring(rx 18, ry 19) | 1.06 |
| confused | 近 ring()，远 ring(rx 14, ry 11) | 远 .79 |
| cry | lid(ry 0) + sad 眉 + 泪 | 0 |

**不合规证据（22:21 基线代码里仍有）**：旧代码把整只眼缩放 ——
`shy 0.90×0.82`、`scared 1.035×1.10`、`sad 0.90`、`worried 0.96`。
这正是用户说的「不合规」。

**工作模式**（复现包 docs/07 + docs/08）：

1. 美术一律交给模型画；我们只做测量、标注、上传下载、配准、导入、合成、打包。
2. **不自己改像素、不用代码描线补洞、不用代码过滤抠图、不拉伸对齐**。
3. 以**完整原图为输入**，用品红 `#FF00FF` 标区域；一个部件一条完整提示词一次发出。
4. 位置偏了只允许**小幅平移**；比例不对就整张重做。
5. 单次 `images/edits` 调用复现不了「工作模式」（已实测，见 §6）。

---

## 5. 工具与命令（本机已验证可用）

### 5.1 环境

```
python（工程 venv）  D:\Codex\Coopanion-Skin-Design\.venv\Scripts\python.exe
                     PIL 12.3.0 / numpy 2.5.4 / scipy 1.18.1 / openai 3.31.0
                     playwright 未安装（真实浏览器采样需要时再装）
node                  24.21.0
git                   2.56.0.windows.2
```

**git 推送必须带 `-c http.version=HTTP/1.1`**（本机 TLS renegotize 问题，AGENTS.md 铁律 5）。

### 5.2 重建候选包（改完必跑）

```powershell
cd D:\Codex\Coopanion-Skin-Design
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe characters\atri-01\official-regeneration\pure-generation\build-diagnostic.py
node --input-type=module -e "import('file:///D:/Codex/Coopanion-Skin-Design/scratch/candidates/atri-pure-components-01/figure.js').then(()=>console.log('IMPORT OK')).catch(e=>{console.log('IMPORT FAIL',e.message)})"
```

### 5.3 预览静态服务

```powershell
cd D:\Codex\Coopanion-Skin-Design
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","http.server","8765" -WorkingDirectory "D:\Codex\Coopanion-Skin-Design" -WindowStyle Hidden
# 浏览器打开
# http://127.0.0.1:8765/preview/engineering.html?pack=scratch/candidates/atri-pure-components-01
```

坑：服务会绑到 IPv6 `::`，只查 IPv4 `Get-NetTCPConnection -LocalPort 8765` 会看不到；
用 `Invoke-WebRequest http://127.0.0.1:8765/preview/engineering.html` 验证最可靠。
另：`figure.js` 是 ES module，浏览器会缓存，改动后用 `?cb=<时间戳>` 强制刷新。

### 5.4 版本备份与回退（用户要求「确保能按版本回退补救」）

```powershell
cd D:\Codex\Coopanion-Skin-Design
.\.venv\Scripts\python.exe scripts\version-candidate.py list                 # 看所有版本
.\.venv\Scripts\python.exe scripts\version-candidate.py snapshot "<note>"    # 给当前预览态存一个版本
.\.venv\Scripts\python.exe scripts\version-candidate.py rollback atri-pure-components-003
```

- 版本号单调（`atri-pure-components-002 / 003 / …`），取自 registry，不随目录增删复用。
- 每个版本同时打 git tag `atri-pack-vNNN`（贴图在 gitignore 的 `scratch/`，代码不在，所以两侧都要锚）。
- `rollback` 会**先把当前态存成一个新版本**再覆盖实时候选，所以回退本身可撤销。
- 回退后必须重建 + 验导入才信预览：见 §5.2。
- **当前基线版本：`atri-pure-components-003`**（tag `atri-pack-v003`，提交 `4d6339d`）= 用户认可过的预览态：22:21 脸部基线、40 贴图、`arm-left` 挂在所有头发之后。

旧的 `scripts/snapshot-candidate.py` 仍可用（只复制不编号），新工作一律走 `version-candidate.py`。

### 5.5 出图通道（imagegen 技能 CLI 回退）

```powershell
$env:OPENAI_API_KEY  = $env:OPENAI_BASE_URL          # 密钥放在 OPENAI_BASE_URL 里（坑）
$env:OPENAI_BASE_URL  = 'https://edge.lingsuan.org/v1'
cd D:\Codex\Coopanion-Skin-Design
.\.venv\Scripts\python.exe "$env:USERPROFILE\.codex\skills\.system\imagegen\scripts\image_gen.py" edit `
  --image <输入图> --prompt-file <提示词.txt> --model gpt-image-2.5-sunburst --size 1024x1024
```

- CLI 位置：`C:\Users\63526\.codex\skills\.system\imagegen\scripts\image_gen.py`。
- 支持透明底 PNG。
- 提示词范本在 `characters/atri-01/prompts/eyes-compliant/`。

### 5.6 本地合层验证（无浏览器时）

`scratch/preview-face.py`、`scratch/probe-seated-face.py`、`scratch/probe-closed-happy.py`、
`scratch/measure-eye-geometry.py` 等仍在 `scratch/` 下（`scratch/` 不进 git，换机会丢，重要脚本应搬进仓库）。

---

## 6. 已知坑（本机 / 本通道实测）

| 坑 | 结论 |
|---|---|
| 整幅母版 + 品红标区 → `images/edits` | **会被无视，整张角色重画（黑底）**，尺寸也变。已复现两次，与复现包失败表一致。 |
| 编辑 520×520 脸部裁图 | **可用**（眼睛外改动约 4%，尺寸一致）。仓库现有 6 套 v2 表情就是这样来的。 |
| 内置浏览器后台标签 | `requestAnimationFrame` 被节流，DOM 读值整体落后一步；`tab.screenshot()` 报 "Unable to capture screenshot"。要用页面内确定性采样（`setEngineeringFrame` / 「导出左右动作 QA」）或前台标签。 |
| 眼裁框猜坐标 | 曾用 `(605,363)-(1191,651)` 结果落在刘海上，测量无效。**必须重新定位眼睛**（站立眼在导出图中的相对位置需重测）。 |
| clipPath 眼睑方案 | 会在眼角产生黑色撕裂（用户据此否掉了「生气」），已撤销，**不要再重演**。 |
| DeepSeek / WorkBuddy 渠道 | 402 Insufficient Balance、限流、transport closed 多次中断会话；本机 DSH 侧模型由用户自行切换。 |
| git push 到 github.com:443 | **直连不通**（2026-10-23 实测 curl 超时），但本机有 HTTP 代理 `http://127.0.0.1:7897` 可用（也支持 socks5/socks5h）。已写入本仓库 `.git/config`：`http.proxy=http://127.0.0.1:7897` + `http.version=HTTP/1.1`，**此后 git push/fetch 免带参**。另：`api.github.com` 与 `raw.githubusercontent.com` 直连正常，git 不通时可临时用 GitHub REST API 逐文件落地。 |

---

## 7. 关键几何数据（母版 1145×1374）

站立睁眼贴图 alpha 包围盒：

- `source-014.png`（近眼）：`(464,425)-(611,535)`，中心 (548,483)
- `source-015.png`（远眼）：`(680,400)-(781,510)`，中心 (730,459)

坐姿：

- `source-025.png`：`(464,741)-(593,832)`
- `source-026.png`：`(678,705)-(762,802)`

`model.expression_rig`：站立眼 `[548,483,53,42]`、`[730,459,33,42]`；嘴 `[648,549]`；
眉 `[545,384,26]`、`[733,368,19]`。

`travel` 测量（站立 ≈110、坐姿 ≈92–100）产物备份在
`scratch/rollback-backup-20261017/eye-geometry.json`。

---

## 8. 下一步（建议顺序）

1. **先把本文提交并推送 main**（用户第 8 条指示）。
   ```powershell
   cd D:\Codex\Coopanion-Skin-Design
   git add docs/ATRI-HANDOVER-DSH-2026-10-20.md
   git -c http.version=HTTP/1.1 commit -F -   # 消息：Record the DSH session handoff for ATRI
   git -c http.version=HTTP/1.1 push origin main
   ```
2. **重定位眼睛并导出基线对照**：用页面自带的「导出左右动作 QA / 下载高清 PNG(2×)」导出
   `scratch/gen/compliant/baseline-check/*.png`，逐表情判断「眼睛是否变形/外观不合格」。
3. **只改不合格项**（用户第 6 条）。已知最小改动：
   - `shy` 在 22:21 基线里**完全没有眼睛变化**（只换嘴），按官方应为 open 12/13 + 瞳孔 (−3,+5)。
   - `angry / sad / worried / determined` 走整眼缩放，属不合规；但**生气刚被修好**，改动要极小心、逐项验证。
4. **实现方式**：保留轮廓、只动眼睑与瞳孔；不要重演 clipPath 方案。可行方向：
   以官方 `travel` 做小幅度眼睑下移，或按官方做法用**面部裁图生成**对应表情贴图
   （与现有 6 套 v2 同管线）。
5. **每改一版立即**：`build-diagnostic.py` 重建 → `node --input-type=module` 验导入 →
   页面导出对照图 → `scripts/snapshot-candidate.py` 存版本。

---

## 9. 相关文档

- `docs/HANDOVER-ATRI-2026-10-16.md` —— 工程交接（主文档，第 11 节是表情/特效复盘）
- `characters/atri-01/official-regeneration/STATUS.md` —— 生成线状态
- `characters/atri-01/official-regeneration/pure-generation/PLAN.md` / `REVIEW.md` / `REVIEW-CURRENT.md` / `VALIDATION.json`
- `docs/LAYER_OWNERSHIP_AND_OCCLUSION.md` —— 图层归属与遮挡（分件前必读）
- `AGENTS.md`（仓库根）—— 工程约定
- `references/whale-coopanion-repro-kit/` —— 官方鲸鱼娘复现包（规则与参数来源）
