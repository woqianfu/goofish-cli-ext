
<p align="center">
  <img src="https://img.shields.io/badge/version-0.7.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-Apache--2.0-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.11%2B-orange" alt="Python">
  <img src="https://img.shields.io/badge/CLI-15%20commands-brightgreen" alt="Commands">
</p>

<h1 align="center">🦑 goofish-cli-ext</h1>
<p align="center">
  <b>闲鱼终极全能工具箱 — 穷举搜索 · AI 文案 · 定价建议 · 微信推送</b><br>
  <b>Ultimate Xianyu Toolkit — Exhaustive Search · AI Copywriting · Price Suggestion · WeChat Push</b>
</p>

<p align="center">
  <i>终端里的闲鱼，比 App 快 10 倍。找到闲鱼上最便宜的宝贝。</i><br>
  <i>Xianyu in your terminal, 10x faster than the App. Find the absolute lowest prices.</i>
</p>

---

## 🏆 亮点 / Highlights

### 🔍 穷举低价搜索 · Exhaustive Low-Price Search

**核心突破**：闲鱼对每个搜索词独立返回前 ~250 条结果。通过穷举 **关键词变体 × 排序 × 城市 × 成色** 的组合，突破限制：

| 模式 | 搜索任务数 | 覆盖商品数 | 场景 |
|:-----|:---------:|:---------:|:-----|
| 标准模式 | 10 次 | ~1,000 件 | 日常比价 |
| 深度模式 `--aggressive` | 300 次 | ~30,000 件 | 地毯式扫货 |

**自动过滤无关商品**：抽取搜索词核心词，只保留标题相关的商品。

**结果示例**：搜"南卡 Clip Super2"从原来的 **12 件** 提升到 **129 件**，最低价从 ¥228 降到 **¥49**。

---

### ⭐ 多维品质评分 · Multi-Dimensional Quality Scoring

| 维度 | 满分 | 说明 |
|:-----|:----:|:-----|
| 价格优势度 | 30 | 比市场中位数便宜越多分越高 |
| 卖家可信度 | 25 | 信用分 + 个人卖家识别 |
| 商品成色 | 20 | 全新/99新/95新/有瑕疵 |
| 上架新鲜度 | 10 | 刚发布 vs 挂了很久 |
| 描述详尽度 | 15 | 标题长度 + 真实信息含金量 |

**四组推荐体系**：
```
⭐ 捡漏推荐    — 低于市场价 30%+（真正的白菜价）
🏆 质优价廉    — 综合评分高 + 价格低于中位数
👤 个人卖家    — 自动识别真实个人（非职业商家）
💰 纯低价      — 只看价格，适合不在乎成色的买家
```

---

### 👤 个人卖家 vs 职业商家识别

自动检测标题中的特征词：

**个人卖家信号**：搬家出 / 老婆不让 / 年会奖品 / 闲置 / 吃灰 / 断舍离 / 买来没用
**职业商家信号**：正品保障 / 假一赔十 / 全国联保 / 七天无理由 / 厂家直销

> 个人卖家的商品通常性价比更高、可以议价。职业卖家的商品价格刚性。

---

### 📊 数据闭环 · Data Closed Loop

| 功能 | 说明 |
|:-----|:-----|
| **价格趋势图** | ASCII 图表展示每日均价变化 |
| **已卖出分析** | 通过商品消失检测推断真实成交价 |
| **定价建议** | 三档定价：快速出手 / 建议定价 / 耐心等待 |
| **微信定时推送** | 每天 9:00 / 21:00 自动推送低价变化 |

---

### 📝 AI 文案生成 · AI Copywriting

基于 [xianyu-copywriter](https://github.com/Jichi666/xianyu-copywriter) 模板体系：

**实物商品**（闲置数码/服装/家电）：
```
【95新】商品名 核心卖点 · ¥价格

📦【产品详情】
💡【出闲置原因】
✅【交易保障】
⚠️【购买须知】
🏷️关键词：...
```

**虚拟商品**（教程/软件/模板）：
```
【产品名】划重点！！——
⚠️ 开头警告（技术要求、无法退款）
💰 购买须知
📦 产品介绍
🔒 版权声明
🏷️关键词
```

---

### 🔄 多平台互转 · Multi-Platform Conversion

一键转换文案格式：**闲鱼 ↔ 转转 ↔ 拍拍**

自动适配各平台风格：
- 闲鱼 → 转转：移除 emoji + 添加质检说明 + 30天质保
- 闲鱼 → 拍拍：成色评级 + 7天无理由 + 京东物流
- 转转/拍拍 → 闲鱼：添加风险提示 + 关键词标签

---

### 💬 议价话术模板 · Negotiation Scripts

7 大场景、20+ 条话术，自动填充你的定价：

| 场景 | 策略 |
|:-----|:-----|
| 小刀（<10%） | 爽快同意 / 送配件 / 下次优惠 |
| 大刀（10-30%） | 坚持底价 / 对比行情 / 强调品质 |
| 屠龙刀（>50%） | 礼貌拒绝 / 推荐替代 / 冷处理 |
| 打包多件 | 打包优惠 / 送配件 / 包邮 |
| 面交 | 同意面交 / 安全提醒 |
| 质量问题 | 提供证据 / 强调质保 / 接受验货 |

---

### 🔗 微信端链接 · WeChat-Friendly Links

所有搜索结果**每条商品独占一行 URL**，微信自动识别为可点击链接：
```
🏆 质优价廉推荐：
  ¥248 几乎全新 河南 [卖家信用优秀]
  https://www.goofish.com/item?id=1056372549064

👤 个人卖家好价：
  ¥230 湖北
  https://www.goofish.com/item?id=1055759587235
```

---

## 📦 安装 / Installation

```bash
# 1. 安装底层搜索引擎
pip install goofish-cli

# 2. 配置闲鱼 Cookie
goofish auth login --source ~/Desktop/goofish-cookies.json
goofish auth status  # → "valid": true

# 3. 安装 goofish-cli-ext
pip install git+https://github.com/woqianfu/goofish-cli-ext.git
```

---

## 🎮 命令大全 / Command Reference

### `goofish-x` — 全能工具箱 (15 commands)

| 命令 / Command | 用途 / Usage | 示例 / Example |
|:---------------|:-------------|:---------------|
| **`search`** | 穷举低价搜索 | `goofish-x search "南卡 Clip Super2"` `--aggressive` |
| **`price`** | 行情速览 | `goofish-x price "南卡 Clip Super2"` |
| **`trend`** | 价格走势图 | `goofish-x trend "南卡" --days 14` |
| **`sold`** | 已卖出分析 | `goofish-x sold "南卡"` |
| **`suggest`** | 定价建议 | `goofish-x suggest "南卡 Clip Super2" --condition 95新` |
| **`watch`** | 价格预警 | `goofish-x watch add --query "南卡" --price 250` |
| **`copy-physical`** | 实物文案 | `goofish-x copy-physical "AirPods" --price 999` |
| **`copy-virtual`** | 虚拟文案 | `goofish-x copy-virtual "Python教程" --price 99` |
| **`copy-optimize`** | 文案优化 | `goofish-x copy-optimize "卖一个耳机..."` |
| **`negotiate`** | 议价模板 | `goofish-x negotiate 小刀 --price 248` |
| **`convert`** | 多平台互转 | `goofish-x convert 转转 --text "..."` |
| **`item`** | 商品详情 | `goofish-x item 1058631237269` |
| **`price-summary`** | 价格报告 | `goofish-x price-summary "南卡 Clip Super2"` |
| **`publish`** | 交互发布 | `goofish-x publish` |
| **`version`** | 版本号 | `goofish-x version` |

---

## 🏗️ 技术架构 / Architecture

```
┌─ 穷举搜索组合器 ──────────────────────┐
│ 关键词变体 × 排序 × 城市 × 成色 × 价格  │
│         → 10~300次独立搜索              │
│         → 去重 + 标题过滤               │
└──────────────┬──────────────────────────┘
               ▼
┌─ 多维评分引擎 ──────────────────────────┐
│ 价格优势(30) + 卖家可信(25) + 成色(20)   │
│ + 新鲜度(10) + 描述(15) = 总分 0-100    │
│         → 捡漏/质优/个人/纯低 四组推荐   │
└──────────────┬──────────────────────────┘
               ▼
┌─ 数据闭环 ──────────────────────────────┐
│ SQLite 持久化 → 趋势分析 → 已卖出分析     │
│ → 定价建议 → Cron 定时推送 → 微信通知    │
└──────────────────────────────────────────┘
```

---

## 📊 性能对比 / Performance

| 指标 | 闲鱼 App 排序 | goofish-x (标准) | goofish-x (穷举) |
|:-----|:------------:|:----------------:|:----------------:|
| 覆盖商品数 | ~50 件 | ~1,000 件 | **~30,000 件** |
| 找到最低价 | 表面价格 | 真实最低价 | **隐藏最低价** |
| 品质评分 | ❌ 无 | ✅ 5 维评分 | ✅ 5 维评分 |
| 个人卖家识别 | ❌ 无 | ✅ 自动 | ✅ 自动 |
| 虚假低价过滤 | ❌ 无 | ✅ 自动 | ✅ 自动 |
| 耗时 | 手动翻页 5min | **~30 秒** | **~2 分钟** |

---

## 🔗 链接 / Links

- **GitHub**: https://github.com/woqianfu/goofish-cli-ext
- **goofish-cli** (底层引擎): https://github.com/fancyboi999/goofish-cli
- **xianyu-copywriter** (文案模板): https://github.com/Jichi666/xianyu-copywriter

---

<p align="center">
  Made with ❤️ for 闲鱼玩家 · For Xianyu power users<br>
  <sub>v0.7.0 · 15 commands · 穷举搜索 · 多维评分 · 数据闭环</sub>
</p>
