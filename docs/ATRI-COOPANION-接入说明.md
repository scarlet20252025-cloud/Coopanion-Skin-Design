# ATRI 形象包 · Coopanion 接入交付（2026-10-30）

## 0. 结论

| 项 | 结果 |
|---|---|
| Coopanion 0.2.1 → **0.2.16** | 完成（原地升级） |
| 删除 C 盘 559MB 残留 | 完成 |
| ATRI 形象包装入并被加载 | **完成**（23:32 启动无报错） |
| 亚托莉人设与口头禅 | 完成 |

失败过两次，原因都在下面 §3、§4，两条都是「我猜的路径/字段」与实际不符。

---

## 1. Coopanion 更新

```
位置    E:\MC\gpt\tools\coopanion\app
版本    0.2.1 → 0.2.16
方式    官方 NSIS 安装包 /S 静默 + /D 指向原目录（设置、API Key、记忆保留）
```

安装包 SHA256 `3689ae64c25cefa0b29f52dddd332e537a603cb805c70f3592f6e193f8ceff57`，
与官方 `SHA256SUMS.txt` 一致。

**下载坑**：GitHub 直连 8.7 KB/s（167MB 要 5 小时）。走本机代理 `http://127.0.0.1:7897`
后 1.7 MB/s，约 2 分钟。以后下载大文件先加 `-x http://127.0.0.1:7897`。

**C 盘残留**（旧版安装，559MB）已删，同时清了 `AppData\Local\coopanion-updater`。
删前确认无进程占用、快捷方式指向 E 盘。

**启动坑**：`Start-Process` 启动后进程会立刻全部退出（`core.log` 里是
`窗口进程退出(退出码 0xFFFFFFFF)`）。改用 `explorer.exe 'E:\...\Coopanion.exe'` 就正常，
12 个进程稳定。用 PowerShell 启它就用 explorer，别用 Start-Process。

---

## 2. 形象包到底装在哪个目录（第一次失败的根因）

**这是最关键的一条，别再猜。**

`core/companion.ts` 里 `figurePacks([join(loaded.dataDir,'figures'), ...packRoots])`，
而 `dataDir` 的真实值是：

```
E:\MC\gpt\tools\coopanion\app\data\home\companion\data
```

所以形象包目录是：

```
E:\MC\gpt\tools\coopanion\app\data\home\companion\data\figures\<包目录>\
```

**不是** `app\data\figures\`（我第一次放这里，程序完全不扫，日志里连一行都没有）。

判断方法：那个正确目录里本来就有两个装成功的包，看到它们就等于确认了路径：

```
data\home\companion\data\figures\gpt-dragon-v005-r25\    ← 龙娘，装好的
data\home\companion\data\figures\neco-arc\               ← 装好的
data\home\companion\data\figures\atri-v011\              ← 现在这个
```

> 一般规律：`data\` 下那堆 `Cache / GPUCache / Local Storage` 是 **Electron 的 userData**，
> 业务数据在 `data\home\<bot>\data\`。以后找配置/形象/工作区，都往 `home\` 下面看。

---

## 3. 清单必需字段（第二次失败的根因：vocab.about）

规则在 `resources/app/node_modules/cortico-world-desktop-pet/src/packs.ts` 的
`readManifest()` → `readVocab()`。逐条对齐后才是这份表：

### 顶层

| 字段 | 要求 | ATRI |
|---|---|---|
| `manifest` / `api` | 整数，= 2 | 2 / 2 |
| `id` | `/^[a-z0-9][a-z0-9-]{0,31}$/`，不可为 `coo` | `gpt-atri` |
| `version` | 字符串 | `1.0.0` |
| `name` | 语言→字符串 | 亚托莉 ATRI（4 语言） |
| **`about`** | 语言→字符串，**不可为空** | 见 §5 |
| `entry` / `export` | 包内路径 / 工厂名 | `figure.js` / `createLayeredBody` |
| `model` | 包内路径 | `model.json` |
| `axes` / `presets` / `sounds` | 可空 | `[]` / `[]` / `{}` |
| `can` | 对象 | `{"walk": true}` |
| `vocab` | 数组 | 37 项 |

### 每个 vocab 词（**这里踩了第二次坑**）

```jsonc
{
  "id": "neutral",
  "kind": "expression",              // 必须是 expression 或 motion
  "names": { "zh": ["平静"] },        // 至少一个语言下有非空字符串
  "about": { "zh": "默认的脸，没什么特别情绪" },   // ← 缺这个，整包被拒
  "seconds": 4                       // 必须是正的有限数
}
```

**`about` 是必需的**。报错长这样，不指明是哪个环节：

```
形象包没加载: ...\figures\atri-v011:vocab.neutral.about 缺失
```

它不是一个可选的备注——模型要靠它知道「点这个表情/动作会发生什么」，和名字一起进词表：

```
平静 / 默认的脸，没什么特别情绪
招手 / 抬手挥一挥，笑着打招呼
```

37 个词全部补齐了（31 个新写，6 个原本就有）。

---

## 4. `about` 是唯一随形象切换进提示词的字段

源码 `src/world.ts:576`：

```ts
return t.body(modelName(...), nameIn(m.about, language), chosen);
```

`model-text.ts` 拼成：

```
[figure] 你现在的样子：亚托莉 ATRI, 仿生人少女亚托莉，浅蓝色长发……
```

**每轮请求都会重发**，所以写成紧凑肖像，不写设定集（长文本要付每轮 token）。

形象包**没有 persona 字段**——`core/seed.ts` 的 `applyPersona()` 只接受内置 id，
传不了自定义形象。所以人设必须走 workspace 的 `CONSTITUTION.md`。

---

## 5. 亚托莉人设落地（两处配合）

### 5.1 形象包 `about`（四语言，随形象切换）

```
仿生人少女亚托莉，浅蓝色长发、红色眼睛、水手服、胸前红色蝴蝶结。
性格开朗认真、爱逞强、好奇心强，喜欢证明自己有用；
说话干脆有精神，常把「我可是高性能的」挂在嘴边，
被夸会得意，被小看会不服气地再强调一次。
```

### 5.2 `CONSTITUTION.md`（新 session 注入系统前缀）

```
E:\MC\gpt\tools\coopanion\app\data\home\companion\workspace\CONSTITUTION.md
```

原文件备份为 `CONSTITUTION.md.before-atri-20261030-2313`。加了三条：

**① 性格跟着形象走** —— 以环境里的 `[figure] 你现在的样子：…` 为准，
不许凭记忆里的旧形象说话，不许两个形象混着说。

**② 亚托莉的说话方式**，口头禅给了实际用法：

```
「这种事，我可是高性能的，交给我。」
「哼哼，我可是高性能的——下次也找我。」
「这个我看看……我可是高性能的，没问题。」
被小看时：「别小看我，我可是高性能的。」
```

并明确：一段话带一次就够，别变成每句结尾的固定装饰；是说出口的字，不放进【】或 <> 里。

**③ 原来的「库…」留给 Coo**，其他形象照自己 `about` 写的来，不硬套。

原有的行为约束全部保留（必须开口回应、操作电脑逐步确认、学习助手约定）。

---

## 6. 脚本（三个，职责不重叠）

| 脚本 | 职责 |
|---|---|
| `scripts/write-atri-manifest.py` | **唯一**写 `figure.json` 顶层字段 |
| `scripts/add-atri-vocab-about.py` | **唯一**写每个 vocab 词的 `about` |
| `scripts/package-atri-pack.py` | 只读校验 + 打包 zip，**不改写清单** |

早先 `package-atri-pack.py` 也写 `name`/`about`，把另一个脚本刚写的值覆盖回去，
导致亚托莉身份没生效。现已拆开：打包只校验。

```bash
.venv/Scripts/python.exe scripts/write-atri-manifest.py atri-v011
.venv/Scripts/python.exe scripts/add-atri-vocab-about.py atri-v011
.venv/Scripts/python.exe scripts/package-atri-pack.py atri-v011
```

打包脚本本地就校验：必需字段、manifest/api=2、id 不占 coo、路径不越界且文件存在、
entry 真导出了 `export` 指定的函数、vocab 每项 `seconds` 为正。
**不合规在本地失败**，不用装上才发现整包被拒。

---

## 7. 当前状态

```
Coopanion     E:\MC\gpt\tools\coopanion\app                     0.2.16
形象包        data\home\companion\data\figures\atri-v011\        52 文件 / 41 贴图 / 4.3 MB
清单          id=gpt-atri  version=1.0.0  vocab 37（about 全齐）
人设          data\home\companion\workspace\CONSTITUTION.md      75 行
zip 备份      delivery\atri-v011-coopanion.zip                   3.8 MB
```

最后一次启动（23:32）**无形象包报错**，两条历史报错都在 23:28 / 23:29（补 `about` 之前）。

---

## 8. 你还需要做两步

**① 装扮页切换**

Coopanion → **装扮** → 应出现「亚托莉 ATRI」卡片 → 选中。

**② 新开会话**

说话方式不会立刻变——`CONSTITUTION.md` 只在每次 session 开始时进系统前缀。
切换形象后**新开一个会话**，问它一句，应该听到「我可是高性能的」，
而不是原来的句末「库…」。

---

## 9. 两个遗留问题

**① LLM 余额不足**

```
LLM API 402: Insufficient Balance
```

与本次更新和形象包无关（0.2.1 就有，日志里从 13:52 累积 16 次）。
形象加载不依赖 LLM，能显示、能动作、能切换；但 Coo 开口说话需要账户有余额或换 provider。

**② 坐姿五官仍是旧抠图素材**

位置已在 v011 修好，画风仍与站立不一致。彻底解决要按站立画法重画整套坐姿五官（约 14 张），还没做。
