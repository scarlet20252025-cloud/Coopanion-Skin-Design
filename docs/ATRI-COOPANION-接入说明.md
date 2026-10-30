# ATRI 形象包 · Coopanion 接入交付（2026-10-30）

## 0. 这次做了什么

| 项 | 结果 |
|---|---|
| Coopanion 从 0.2.1 更新到 **0.2.16** | 完成（原地升级，设置/记忆保留） |
| 删除 C 盘 559MB 残留安装 | 完成 |
| 按官方格式重写 ATRI 形象包清单 | 完成 |
| 补全亚托莉人设与口头禅 | 完成 |
| 形象包装入 Coopanion | 完成 |

---

## 1. Coopanion 更新

```
位置    E:\MC\gpt\tools\coopanion\app
版本    0.2.1 → 0.2.16
方式    官方 NSIS 安装包 /S 静默安装，/D 指向原目录
```

安装包校验：SHA256 `3689ae64c25cefa0b29f52dddd332e537a603cb805c70f3592f6e193f8ceff57`，
与官方 `SHA256SUMS.txt` 一致。

**下载坑**：GitHub 直连只有 8.7 KB/s（167MB 要 5 小时），改走本机代理
`http://127.0.0.1:7897` 后 1.7 MB/s，约 2 分钟下完。

**C 盘残留**（原来的旧安装）：

```
C:\Users\63526\AppData\Local\Programs\coopanion     559 MB  → 已删
C:\Users\63526\AppData\Local\coopanion-updater              → 已清
```

删前确认：无进程从该路径运行，开始菜单快捷方式指向 E 盘那份。

---

## 2. 官方形象包格式（读源码确认，不是猜的）

规则来源（0.2.16 安装目录内）：

```
resources/app/node_modules/cortico-world-desktop-pet/src/packs.ts
  readManifest()     清单校验，决定一个包能不能被加载
  figurePacks()      扫描目录
```

### 必需字段

| 字段 | 要求 | ATRI 的值 |
|---|---|---|
| `manifest` | 整数，必须 = 2 | `2` |
| `api` | 整数，必须 = 2 | `2` |
| `id` | 合法标识符，不可为 `coo`（内置保留） | `gpt-atri` |
| `version` | 字符串 | `1.0.0` |
| `name` | 语言→字符串 | `亚托莉 ATRI` |
| **`about`** | 语言→字符串，**不可为空** | 见 §3 |
| `entry` | 包内相对路径 | `figure.js` |
| `export` | 工厂函数名 | `createLayeredBody` |
| `axes` | 数组（可空） | `[]` |
| `presets` | 数组（可空） | `[]` |
| `sounds` | 对象（可空） | `{}` |
| `can` | 对象 | `{"walk": true}` |
| `vocab` | 数组，每个词 `seconds` 必须为正数 | 37 项 |

校验失败的表现是**整包不加载**，且日志只说「figure.json 读不了」，不告诉你是哪个字段——
所以先按上表逐项对齐，比试错省时间。

### 目录层级

```
<dataDir>/figures/<任意目录名>/figure.json
```

即 `E:\MC\gpt\tools\coopanion\app\data\figures\atri-v011\figure.json`。

`figure.json` 允许在压缩包内下探若干层（`PACK_DEPTH`），所以 zip 里带一层目录名是安全的。

---

## 3. 关键发现：`about` 是唯一随形象切换的提示词

源码 `src/world.ts:576`：

```ts
return t.body(modelName(m.name, pack.id, language), nameIn(m.about, language), chosen);
```

而 `model-text.ts` 里：

```ts
body: (name, about, picks) => `${name}, ${about}${picks.length ? `（${picks.join(',')}）` : ''}`
```

这句会变成环境里的一行：

```
[figure] 你现在的样子：亚托莉 ATRI, 仿生人少女亚托莉，浅蓝色长发……
```

**它每次请求都会重发**，所以写成「紧凑肖像」而不是「角色设定集」——长内容要付每轮的 token。

这也是官方格式里**唯一**能把角色身份传给模型的字段。形象包本身**没有 persona 字段**，
`persona` 由 workspace 的 `CONSTITUTION.md` 提供（见 §4）。

---

## 4. 亚托莉人设怎么落地的

两处配合，缺一不可：

### 4.1 形象包的 `about`（随形象切换）

当前值：

```
zh: 仿生人少女亚托莉，浅蓝色长发、红色眼睛、水手服、胸前红色蝴蝶结。性格开朗认真、
    爱逞强、好奇心强，喜欢证明自己有用；说话干脆有精神，常把「我可是高性能的」挂在嘴边，
    被夸会得意，被小看会不服气地再强调一次。
```

四种语言都有：`zh` / `zh-Hant` / `en` / `ja`。

### 4.2 `CONSTITUTION.md`（人设，新 session 注入系统前缀）

```
E:\MC\gpt\tools\coopanion\app\data\home\companion\workspace\CONSTITUTION.md
```

原文件已备份为 `CONSTITUTION.md.before-atri-20261030-2313`。

改动要点：

1. **形象可以换，性格和口癖跟着形象走** —— 新增章节，要求以环境里的
   `[figure] 你现在的样子：…` 为准，不许凭记忆里的旧形象说话。

2. **亚托莉的说话方式**写进去了，含口头禅的实际用法：

   ```
   「这种事，我可是高性能的，交给我。」
   「哼哼，我可是高性能的——下次也找我。」
   「这个我看看……我可是高性能的，没问题。」
   被小看时：「别小看我，我可是高性能的。」
   ```

   并明确：一段话带一次就够，不要变成每句结尾的固定装饰；
   它说出口的字，不放进【】或 <> 里。

3. **原来的「库…」保留给 Coo**，其他形象照自己 `about` 写的来，不硬套。

4. 保留了所有原有功能段（必须开口回应、操作电脑要逐步确认、学习助手约定），
   这些是行为约束，删掉会影响功能。

### 为什么不用 persona 替换接口

`core/seed.ts` 有 `applyPersona()`，但它只接受**内置的人设 id**（coo / forge 等），
传不了自定义形象。所以自定义形象只能走「改 CONSTITUTION.md + about 描述」这条路。

---

## 5. 脚本

新增两个脚本，职责分开（之前它们都写 `name`/`about`，后者把前者覆盖了，
导致亚托莉身份没生效——已修）：

| 脚本 | 职责 |
|---|---|
| `scripts/write-atri-manifest.py` | **唯一**写 `figure.json` 的地方 |
| `scripts/package-atri-pack.py` | 只读 `figure.json` 做校验，然后打包 zip，不改写 |

```bash
# 改完人设描述后
.venv/Scripts/python.exe scripts/write-atri-manifest.py atri-v011
.venv/Scripts/python.exe scripts/package-atri-pack.py atri-v011
```

打包脚本会校验：必需字段、manifest/api=2、id 不占用 coo、路径不越界且文件存在、
entry 真的导出了 `export` 指定的函数、vocab 每项 `seconds` 为正。
**不合规在本地就失败**，不用装上才发现整包被拒。

产物：`delivery/atri-v011-coopanion.zip`（3.7 MB，52 文件，一层目录）。

---

## 6. 当前状态

```
Coopanion      E:\MC\gpt\tools\coopanion\app  →  0.2.16
形象包         data\figures\atri-v011\        →  52 文件 / 41 贴图 / 4.3 MB
清单校验       必需字段全齐，vocab 37 项（19 表情 + 18 动作）
人设           workspace\CONSTITUTION.md      →  75 行，含亚托莉口头禅
zip 备份       delivery\atri-v011-coopanion.zip
```

## 7. 验证方式

打开 Coopanion → **装扮**页 → 应出现「亚托莉 ATRI」卡片 → 选中切换。

切换后桌宠应变成亚托莉形象。此时问它一句，或让它自我介绍，应该听到
「我可是高性能的」这类说法；不再是句末的「库…」。

如果卡片没出现：重启 Coopanion（`figures` 目录只在启动时扫）。
如果切换后说话方式没变：**必须是新开一个会话**——`CONSTITUTION.md` 只在
每次 session 开始时进系统前缀，改完不会立刻影响正在跑的那一轮。

---

## 8. 未完成 / 需要你知道的

1. **启动验证没做成**：我重启 Coopanion 时进程启动后立即退出（`core.log` 末尾是
   `窗口进程退出(退出码 0xFFFFFFFF)`），前台运行也没有报错输出。
   可能是停止进程的方式打断了它的清理流程，或者窗口进程和我杀进程的操作撞上了。
   **这一步需要你手动双击 `Coopanion.exe` 确认一下**，我没法在这个环境里替你做。

2. **LLM 余额不足**：`core.log` 里持续出现
   `LLM API 402: Insufficient Balance`。这跟本次更新和形象包无关（0.2.1 时就存在）。
   形象加载不依赖 LLM，能看能动能切换；但 Coo 要开口说话需要账户有余额，
   或者换一个 provider。

3. **坐姿五官仍是旧抠图素材**：位置已在 v011 修好，画风仍与站立不一致。
   彻底解决要按站立画法重画整套坐姿五官（约 14 张），这件事还没做。
