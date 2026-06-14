
<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-Apache--2.0-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.11%2B-orange" alt="Python">
  <img src="https://img.shields.io/badge/status-alpha-yellow" alt="Status">
</p>

<h1 align="center">🦑 goofish-cli-ext</h1>
<p align="center"><b>闲鱼全能工具箱 — 搜索比价 · AI 文案生成 · 商品发布 · 行情监控</b></p>
<p align="center">
  终端里的闲鱼，比 App 快 10 倍<br>
  基于 <a href="https://github.com/fancyboi999/goofish-cli">goofish-cli</a> 扩展 · 吸收 <a href="https://github.com/Jichi666/xianyu-copywriter">xianyu-copywriter</a> 文案模板
</p>

---

## 🚀 两行命令，干掉闲鱼 App

```bash
pip install git+https://github.com/woqianfu/goofish-cli-ext.git
goofish-x search "AirPods Pro 2" --min 500 --max 1500
```

**输出：实时闲鱼行情 + 可点击购买链接 + 价格排序表格**

不需要打开 App，不需要手动翻页，不需要一个个点开看价格。

---

## ✨ 十大亮点

### 1️⃣ 🔍 极速搜索比价 · 秒出最低价

```bash
goofish-x price "南卡 Clip Super2"
```

```
╭─────────────────── 闲鱼行情速览 ───────────────────╮
│ 📊 南卡 Clip Super2                                 │
│ 在售数量: 30 件                                      │
│ ┌ 最低价    平均价    最高价     ┐                   │
│ │ ¥    228  ¥    275  ¥    310  │                   │
│ └───────────────────────────────┘                   │
│ 热门地区: 广东, 河南, 上海, 贵州, 四川                │
╰──────────────────────────────────────────────────────╯
```

**3 秒看懂整个市场**：不用一个个翻，最低价、均价、最高价、在售数量、热门地区一览无余。

比打开闲鱼 App 搜索 → 点价格排序 → 手动算均价 → 至少快 10 倍。

### 2️⃣ 🔗 结果自带可点击购买链接

搜索结果的 **每行都有一个「打开」按钮**，底部更有完整的 **可点击链接列表**：

```
📎 点击链接直接购买：
  # 1  ¥228  https://www.goofish.com/item?id=1058631237269
  # 2  ¥245  https://www.goofish.com/item?id=1058950217367
  # 3  ¥248  https://www.goofish.com/item?id=1058906397116
```

看到低价商品，**直接点击链接跳转网页版购买**，无需在 App 里重新搜索。

### 3️⃣ 🛡️ 智能风控 · 安全稳定

- **浏览器真实渲染**：搜索通过 Playwright 浏览器路径，不是被屏蔽的 API 接口
- **令牌桶限流**：写操作（发布/发送消息）自动限流 1 次/分钟
- **RGV587 熔断器**：触发风控后自动熔断，`goofish auth reset-guard` 一键恢复
- **非侵入式**：只读操作不影响闲鱼账号安全

### 4️⃣ 🤖 AI 文案生成 · 复制即用

```bash
goofish-x copy-physical "南卡 Clip Super2" --price 248 \
  --features "耳夹式,蓝牙6.0,AI翻译,30小时续航" \
  --condition "95新" --location "上海"
```

一键生成专业闲鱼文案，**自动复制到剪贴板**：

- ✅ 完整的 7 模块结构：成色标题 → 产品详情 → 闲置原因 → 交易保障 → 发货信息 → 购买须知 → 关键词
- ✅ 零售后纠纷：风险提示前置，完美主义者绕道
- ✅ 15-30 个 SEO 关键词：自动匹配品牌词、品类词
- ✅ macOS 自动复制：生成的文案直接粘贴到闲鱼

### 5️⃣ 🏗️ 模板体系 · 行业最佳实践

来自专业闲鱼卖家总结的文案结构，覆盖两大品类：

| 品类 | 模块数 | 核心策略 |
|------|--------|----------|
| **实物**（数码/服装/家电） | 7 模块 | 成色开头 · 实物拍摄 · 当面验货 |
| **虚拟**（教程/软件/模板） | 6 模块 | ⚠️ 警告前置 · "无法退款"出现 3 次 · 版权保护 |

### 6️⃣ 📋 文案优化器 · 一键查漏补缺

```bash
goofish-x copy-optimize "卖一个耳机，九成新，包装齐全，248包邮"
```

```
📝 优化后文案
卖一个耳机，九成新...

优化建议:
  • 缺少风险提示标记，建议使用 ⚠️ emoji 突出警告信息
  • 建议使用 emoji 分段（📦📝✅⚠️）提升可读性
  • 缺少关键词标签，建议底部添加搜索关键词
```

**AI 审计你的文案**：补全缺失的模块，防范售后纠纷。

### 7️⃣ 📊 价格筛选 · 精准定位

```bash
# 只看 200-300 之间的结果
goofish-x search "南卡 Clip Super2" --min 200 --max 300 --limit 50

# 只看前 5 条最低价
goofish-x search "索尼 WH-1000XM5" --limit 5
```

### 8️⃣ 🔄 JSON 输出 · AI Agent 友好

```bash
goofish-x search "南卡 Clip Super2" --limit 3 --json
```

输出纯 JSON，可被 Hermes Agent / Claude Code / 其他 AI Agent 直接消费，**无需解析终端输出**。

配合 Hermes 的 MCP 能力，在聊天气泡里直接问：
> "帮我搜闲鱼上 AirPods Pro 2 最低价"
>
> → 自动调用 goofish search，返回行情数据

### 9️⃣ 🛒 一条龙发布 · 文案到上架

```bash
goofish-x publish
```

交互式流程：
1. 输入商品名称、价格、成色
2. 自动生成文案
3. 预览确认
4. 上传图片 → 一键发布到闲鱼

**从写好文案到商品上架，全程不离开终端。**

### 🔟 🎯 商品详情查询 · 不打开 App

```bash
goofish-x item 1058631237269
```

直接在终端看商品详情：标题、价格、成色、链接。

---

## 📦 快速安装

### 前置条件

已安装 [goofish-cli](https://github.com/fancyboi999/goofish-cli) 并配置好闲鱼 Cookie：

```bash
pip install goofish-cli
goofish auth login --source ~/Desktop/goofish-cookies.json
goofish auth status  # → "valid": true
```

### 安装 goofish-cli-ext

```bash
pip install git+https://github.com/woqianfu/goofish-cli-ext.git
```

安装后立即可用：

```bash
goofish-x --help
goofish-copy --help
```

---

## 📖 命令大全

### `goofish-x` — 全能工具箱

| 命令 | 功能 | 示例 |
|------|------|------|
| `search <关键词>` | 搜索 + 价格排序 + 点击链接 | `goofish-x search "AirPods Pro 2" --min 500` |
| `price <关键词>` | 行情速览（最低/平均/最高） | `goofish-x price "南卡 Clip Super2"` |
| `copy-physical <名称>` | 生成实物商品文案 | `goofish-x copy-physical "Switch" --price 1500` |
| `copy-virtual <名称>` | 生成虚拟商品文案 | `goofish-x copy-virtual "Python教程" --price 99` |
| `copy-optimize <文案>` | 优化现有文案 | `goofish-x copy-optimize "卖一个耳机..."` |
| `item <商品ID>` | 查看商品详情 | `goofish-x item 1058631237269` |
| `publish` | 交互式发布商品 | `goofish-x publish` |
| `version` | 打印版本号 | `goofish-x version` |

### `goofish-copy` — 独立文案生成器

| 命令 | 功能 | 示例 |
|------|------|------|
| `physical <名称>` | 生成实物文案 | `goofish-copy physical "iPhone 15" --price 4500` |
| `virtual <名称>` | 生成虚拟文案 | `goofish-copy virtual "设计模板" --price 29` |
| `optimize <文案>` | 文案优化 | `goofish-copy optimize "..." --virtual` |

---

## 🎬 用法场景

### 场景 1：想买二手耳机，先看行情

```bash
$ goofish-x price "南卡 Clip Super2"

╭──── 闲鱼行情速览 ────╮
│ 在售: 30 件          │
│ 最低 ¥228  平均 ¥275  │
│ 最高 ¥310            │
│ 热门: 广东 河南 上海   │
╰──────────────────────╯

$ goofish-x search "南卡 Clip Super2" --max 250

📎 点击链接直接购买：
  # 1  ¥228  https://goofish.com/...  ← 最低价，点它！
  # 2  ¥230  https://goofish.com/...
  # 3  ¥245  https://goofish.com/...
```

### 场景 2：卖出闲置，写文案 + 发布

```bash
$ goofish-x copy-physical "南卡 Clip Super2" \
    --price 248 \
    --features "耳夹式,蓝牙6.0,AI翻译,30小时续航" \
    --condition "95新" --location "上海"

✅ 文案已复制到剪贴板

# 直接粘贴到闲鱼发布
$ goofish-x publish --name "南卡 Clip Super2" --price 248
```

### 场景 3：AI Agent 自动比价

在 Hermes Agent 中：
```
> 帮我搜闲鱼上索尼 WH-1000XM5 的最低价
→ 自动调用 goofish search，返回表格 + 链接
```

---

## 🏗️ 项目架构

```
goofish-cli-ext/
├── src/goofish_cli_ext/
│   ├── cli.py                 # 🏠 goofish-x 主入口（8 个子命令）
│   ├── commands/
│   │   ├── search.py          # 🔍 搜索比价引擎
│   │   ├── copywriter.py      # 📝 AI 文案工厂（模板引擎）
│   │   ├── item.py            # 🔎 商品详情查询
│   │   └── publish.py         # 🚀 商品发布流水线
│   └── __init__.py
├── pyproject.toml             # 📦 打包配置
└── README.md                  # 📖 本文档
```

### 依赖关系

```
goofish-cli-ext
  ├── goofish-cli    → 搜索 / 发布 / IM / Cookie 管理（底层引擎）
  ├── typer          → CLI 框架
  ├── rich           → 表格 / 面板 / 彩色输出
  └── pyyaml         → 配置解析
```

---

## ⚡ Hermes Agent 集成

goofish-cli 已配置为 Hermes 的 MCP 服务，goofish-cli-ext 作为 Skill 安装：

```bash
# 查看 MCP 服务状态
hermes mcp list
# 输出: goofish  ✓ enabled  (15 tools)

# 加载 Skill
hermes skills load goofish-cli-ext
# 在聊天中直接：帮我搜闲鱼上...
```

---

## 🧑‍💻 技术架构 (给极客看)

```
用户请求
     │
     ▼
┌─────────────────────────────────────┐
│  goofish-x CLI (typer)              │
│  ├── search / price                 │
│  ├── copy-physical / copy-virtual   │
│  ├── copy-optimize                  │
│  ├── item                           │
│  └── publish                        │
└──────────┬──────────────────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐ ┌──────────────┐
│goofish   │ │AI 文案引擎   │
│search    │ │(模板填充)    │
│publish   │ │              │
│item API  │ │实物模板      │
│          │ │虚拟模板      │
│Cookie Mgr│ │优化审计      │
└──────────┘ └──────────────┘
     │
     ▼
┌──────────┐
│Playwright│
│浏览器    │
│(抗风控)  │
└──────────┘
```

### 三个关键设计决策

1. **搜索不走 API** → 闲鱼没有开放搜索 API，通过 Playwright 浏览器渲染 + DOM 解析实现
2. **文案不走 LLM** → 基于模板引擎填充，稳定可控，零 API 成本
3. **JSON 输出优先** → 所有命令支持 `--json`，方便 AI Agent 和脚本消费

---

## 🤝 致谢

- [fancyboi999/goofish-cli](https://github.com/fancyboi999/goofish-cli) — 闲鱼 CLI + MCP 基础设施
- [Jichi666/xianyu-copywriter](https://github.com/Jichi666/xianyu-copywriter) — 闲鱼文案模板体系（MIT 协议）

---

<p align="center">
  Made with ❤️ for 闲鱼玩家<br>
  觉得有用？给个 ⭐
</p>
