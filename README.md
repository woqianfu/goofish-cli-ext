# goofish-cli-ext

**闲鱼全能工具箱** — 搜索比价 + AI 文案生成 + 商品发布 + IM 管理

基于 [goofish-cli](https://github.com/fancyboi999/goofish-cli) 的 MCP 能力扩展，同时吸收了 [xianyu-copywriter](https://github.com/Jichi666/xianyu-copywriter) 的文案模板体系。

## 安装

```bash
pip install goofish-cli-ext
# 依赖 goofish-cli，需要先配置好闲鱼 Cookie
goofish auth login --source ~/goofish-cookies.json
```

## 命令一览

| 命令 | 说明 |
|------|------|
| `goofish-x search <关键词>` | 搜索商品，按价格排序，输出最低价 |
| `goofish-x copy-physical` | 生成实物商品文案（闲置数码产品） |
| `goofish-x copy-virtual` | 生成虚拟商品文案（软件/教程） |
| `goofish-x copy-optimize <文案>` | 优化现有文案 |
| `goofish-x publish` | 交互式发布商品（先写文案再发布） |
| `goofish-x price <关键词>` | 查看闲鱼行情：最低价/均价/趋势 |
| `goofish-x item <id>` | 查看商品详情 |

### 文案生成子命令 `goofish-copy`

```bash
goofish-copy physical "AirPods Pro 2" --condition "95新" --price 999 --features "降噪好,续航长,正品"
goofish-copy virtual "Python教程" --price 99 --features "50节课,实战项目"
goofish-copy optimize "卖一个耳机..."
```

## 功能

### 1. 搜索比价
- 搜商品 + 自动按价格排序
- 输出表格：排名 / 价格 / 标题 / 地点 / 信用
- `--min` / `--max` 价格区间筛选

### 2. AI 文案生成
基于 xianyu-copywriter 模板体系，分两大品类：

**实物商品（如闲置数码）：**
- 商品标题 + 核心卖点
- 产品详情（成色、使用状况、配件）
- 出闲置原因
- 交易保障
- 发货信息
- 购买须知
- 关键词标签

**虚拟商品（如软件教程）：**
- 开头重点警告
- 版权声明
- 购买须知
- 产品介绍（编号分段）
- 版权注意
- 关键词标签

### 3. 发布流程
`search → copy → publish` 一条龙：
1. 搜同类商品看行情
2. 生成文案
3. 上传图片
4. 一键发布

### 4. MCP 支持
继承 goofish-cli 的 MCP 入口，可作为 Hermes Agent / Claude Code 的工具。

## 配置

依赖 `~/.goofish-cli/cookies.json`（由 `goofish auth login` 生成）。
