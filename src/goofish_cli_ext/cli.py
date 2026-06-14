# -*- coding: utf-8 -*-
"""
goofish-cli-ext 主入口
闲鱼全能工具箱 — 搜索比价 + 文案生成 + 商品发布 + IM
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from goofish_cli_ext.commands.search import search_items_cli
from goofish_cli_ext.commands.copywriter import copy_physical, copy_virtual, copy_optimize
from goofish_cli_ext.commands.publish import publish_item
from goofish_cli_ext.commands.item import get_item

app = typer.Typer(
    name="goofish-x",
    help="闲鱼全能工具箱 — 搜索比价 · AI文案生成 · 商品发布 · IM",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

# ============================================================
# search — 搜索比价
# ============================================================
@app.command(name="search")
def search_cmd(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(30, "--limit", "-n", help="返回条数"),
    min_price: Optional[int] = typer.Option(None, "--min", "-m", help="最低价筛选"),
    max_price: Optional[int] = typer.Option(None, "--max", "-M", help="最高价筛选"),
    sort_by_price: bool = typer.Option(True, "--sort/--no-sort", help="按价格排序"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON 格式输出"),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="深度搜索（多关键词轮询，覆盖更多低价商品）"),
    recommend: bool = typer.Option(True, "--reco/--no-reco", help="展示品质推荐分组"),
    sort: str = typer.Option("price-asc", "--sort-by", help="排序方式: price-asc(低价优先) / new(最新) / credit(信用)"),
    condition: str = typer.Option("", "--condition", "-c", help="成色筛选: new(全新) / used(二手)"),
    location: str = typer.Option("", "--loc", "-l", help="地区筛选: 如'上海'"),
    wechat: bool = typer.Option(False, "--wechat", "-w", help="微信端输出格式（纯文本 + 独占行链接）"),
    aggressive: bool = typer.Option(False, "--aggressive", "-a", help="激进模式：25关键词×3排序×4城市=300任务穷举搜索"),
):
    """闲鱼终极低价搜索 — 穷举所有策略组合找最低价

    原理：闲鱼每个搜索词独立返回前~250条结果。
    通过穷举「关键词变体 × 排序 × 价格暗示 × 城市 × 成色」的组合，
    突破单次搜索只能看到 250 条的限制。

    默认模式：20 个关键词 × price-asc 排序 = 20 次搜索
    激进模式 (--aggressive)：25 关键词 × 3 排序 × 4 城市 = 300 次搜索

    推荐分组：
    ⭐ 捡漏 — 低于市场价 30%+
    🏆 质优价廉 — 高评分 + 低价
    👤 个人卖家 — 识别真实个人卖家
    💰 纯低价 — 只看价格
    """
    # 构建搜索描述字符串
    search_desc = query
    if condition:
        cond_label = {"new": "全新", "used": "二手"}.get(condition, condition)
        search_desc += f" [{cond_label}]"
    if location:
        search_desc += f" [{location}]"
    if sort:
        sort_label = {"price-asc": "价格↑", "new": "最新", "credit": "信用"}.get(sort, sort)
        search_desc += f" [{sort_label}]"

    result = search_items_cli(
        query, limit, min_price, max_price, sort_by_price,
        deep_search=deep,
        sort=sort,
        condition=condition,
        location=location,
        aggressive=aggressive,
    )

    if json_output:
        console.print_json(json.dumps(result, ensure_ascii=False))
        return

    items = result["items"]
    if not items:
        console.print("[yellow]未搜索到结果[/yellow]")
        return

    # 统计信息
    prices = [i["price"] for i in items]
    min_p = min(prices)
    max_p = max(prices)
    avg_p = sum(prices) // len(prices)

    console.print(Panel(
        f"[bold cyan]🔍 {query}[/bold cyan]  |  "
        f"共 [bold]{result['total']}[/bold] 条  |  "
        f"最低 [bold green]¥{min_p}[/bold green]  |  "
        f"平均 [bold]¥{avg_p}[/bold]  |  "
        f"最高 [bold]¥{max_p}[/bold]",
        title="闲鱼行情"
    ))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim")
    table.add_column("价格", style="bold green", justify="right")
    table.add_column("标题", max_width=40)
    table.add_column("地点")
    table.add_column("信用")

    for i in items[:20]:
        price_str = f"¥{i['price']}" if isinstance(i['price'], int) else i['price']
        table.add_row(
            str(i["rank"]),
            price_str,
            i["title"][:38],
            i.get("location", ""),
            i.get("badge", ""),
        )

    console.print(table)

    # 微信端纯文本格式
    if wechat:
        console.print()  # 换行
        rec = result.get("recommended", {})

        wechat_lines = [f"🔍 {search_desc} | 共{result['total']}件 | ¥{min_p}~¥{max_p} | 均价¥{avg_p}"]
        wechat_lines.append("")

        # 1. ⭐ 捡漏推荐（最优先展示）
        if rec.get("steals"):
            wechat_lines.append("⭐ 捡漏推荐（低于市场价30%+）：")
            for i in rec["steals"][:5]:
                badge = f" [{i.get('badge','')}]" if i.get('badge') else ""
                cond2 = i.get("condition", "")
                loc2 = i.get("location", "")
                score = i.get("_score_detail", {})
                ps = " 👤个人" if score.get("is_personal_seller") else ""
                wechat_lines.append(f"  ¥{i['price']} {cond2} {loc2}{badge}{ps}")
                wechat_lines.append(f"  {i.get('url', '')}")
            wechat_lines.append("")

        # 2. 🏆 质优价廉
        if rec.get("best"):
            wechat_lines.append("🏆 质优价廉：")
            for i in rec["best"][:5]:
                badge = f" [{i.get('badge','')}]" if i.get('badge') else ""
                cond2 = i.get("condition", "")
                loc2 = i.get("location", "")
                wechat_lines.append(f"  #{i['rank']} ¥{i['price']} {cond2} {loc2}{badge}")
                wechat_lines.append(f"  {i.get('url', '')}")
            wechat_lines.append("")

        # 3. 👤 个人卖家好价
        if rec.get("personal_deals"):
            wechat_lines.append("👤 个人卖家好价：")
            for i in rec["personal_deals"][:3]:
                wechat_lines.append(f"  ¥{i['price']} {i['title'][:25]}")
                wechat_lines.append(f"  {i.get('url', '')}")
            wechat_lines.append("")

        # 4. 💰 纯低价
        if rec.get("cheapest"):
            wechat_lines.append("💰 纯低价：")
            for i in rec["cheapest"][:3]:
                wechat_lines.append(f"  ¥{i['price']} {i['title'][:25]}")
                wechat_lines.append(f"  {i.get('url', '')}")
            wechat_lines.append("")

        wechat_lines.append("📎 链接可直接点击打开")
        cov = result.get("coverage", {})
        tasks = cov.get("tasks_attempted", 0)
        items = cov.get("unique_items", 0)
        wechat_lines.append(f"💡 穷举搜索: {tasks}任务→{items}件 | ⭐捡漏 👤个人卖家")
        console.print("\n".join(wechat_lines))
        return

    # 推荐分组（终端格式）
    if recommend and result.get("recommended"):
        rec = result["recommended"]

        # 1. ⭐ 捡漏推荐
        if rec.get("steals"):
            console.print("\n[bold red]⭐ 捡漏推荐（低于市场价30%+）：[/bold red]")
            for i in rec["steals"][:5]:
                badge = f" [{i.get('badge','')}]" if i.get('badge') else ""
                score = i.get("_score_detail", {})
                ps = " 👤个人卖家" if score.get("is_personal_seller") else ""
                console.print(f"  ¥{i['price']:>4d}  {i['title'][:45]}  {badge}{ps}")
                console.print(f"       {i.get('url', '')}")

        # 2. 🏆 质优价廉
        if rec.get("best"):
            console.print("\n[bold green]🏆 质优价廉（品质好 + 价格低）：[/bold green]")
            for i in rec["best"][:5]:
                badge = f" [{i.get('badge','')}]" if i.get('badge') else ""
                console.print(f"  #{i['rank']:2d}  ¥{i['price']:>3d}  {i['title'][:50]}  {badge}")
                console.print(f"       {i.get('url', '')}")

        # 3. 👤 个人卖家好价
        if rec.get("personal_deals"):
            console.print("\n[bold cyan]👤 个人卖家好价：[/bold cyan]")
            for i in rec["personal_deals"][:3]:
                console.print(f"  #{i['rank']:2d}  ¥{i['price']:>3d}  {i['title'][:50]}")
                console.print(f"       {i.get('url', '')}")

        if rec.get("cheapest"):
            console.print("\n[bold yellow]💰 纯低价：[/bold yellow]")
            for i in rec["cheapest"][:3]:
                console.print(f"  #{i['rank']:2d}  ¥{i['price']:>3d}  {i['title'][:50]}")
                console.print(f"       {i.get('url', '')}")

    # 结果底部输出链接列表（复制到浏览器打开）
    console.print("\n[bold]📎 复制链接到浏览器打开：[/bold]")
    for i in items[:10]:
        url = i.get("url", "")
        if url:
            console.print(f"  #{i['rank']:2d}  ¥{i['price']:>3d}  {url}")
        else:
            console.print(f"  #{i['rank']:2d}  ¥{i['price']:>3d}")

    # 终端提示：Cmd+点击链接（iTerm2）或直接复制链接
    console.print("[dim]💡 提示：选中链接后 Cmd+C 复制，粘贴到浏览器打开。iTerm2 支持 Cmd+点击打开。[/dim]")

    if len(items) > 20:
        console.print(f"[dim]... 还有 {len(items) - 20} 条，加 --limit {limit} 查看更多[/dim]")


# ============================================================
# price — 价格行情速览
# ============================================================
@app.command(name="price")
def price_cmd(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(30, "--limit", "-n", help="采样条数"),
):
    """快速查看闲鱼行情：最低价/均价/数量"""
    result = search_items_cli(query, limit, min_price=None, max_price=None, sort_by_price=True)
    items = result["items"]

    # 保存快照到价格监控数据库
    try:
        from goofish_cli_ext.commands.price_watch import save_snapshot
        save_snapshot(query, items)
    except Exception:
        pass

    if not items:
        console.print("[yellow]未搜索到结果[/yellow]")
        return

    prices = [i["price"] for i in items]
    from collections import Counter
    loc_counter = Counter(i.get("location", "") for i in items)

    console.print(Panel(
        f"[bold cyan]📊 {query}[/bold cyan]\n"
        f"在售数量: [bold]{len(items)}[/bold] 件\n"
        f"┌ {'最低价':<10} {'平均价':<10} {'最高价':<10} ┐\n"
        f"│ [green]¥{min(prices):>7}[/green]  [yellow]¥{sum(prices)//len(prices):>7}[/yellow]  [red]¥{max(prices):>7}[/red] │\n"
        f"└{'─'*34}┘\n"
        f"热门地区: {', '.join(loc for loc, _ in loc_counter.most_common(5))}",
        title="闲鱼行情速览"
    ))


# ============================================================
# copy-physical — 实物商品文案
# ============================================================
@app.command(name="copy-physical")
def copy_physical_cmd(
    name: str = typer.Argument(..., help="商品名称（如 AirPods Pro 2）"),
    condition: str = typer.Option("95新", "--condition", "-c", help="成色"),
    price: int = typer.Option(..., "--price", "-p", help="价格"),
    features: str = typer.Option("", "--features", "-f", help="核心卖点，逗号分隔"),
    location: str = typer.Option("", "--location", "-l", help="发货地"),
):
    """生成实物商品（闲置数码/二手产品）的闲鱼文案"""
    feat_list = [f.strip() for f in features.split(",") if f.strip()]
    result = copy_physical(name=name, condition=condition, price=price, features=feat_list, location=location)
    console.print(Panel(result["copy"], title=f"📝 {name} — 闲鱼文案", border_style="green"))
    console.print(f"\n[dim]关键词: {' '.join(result['keywords'])}[/dim]")
    copy_to_clipboard(result["copy"])


# ============================================================
# copy-virtual — 虚拟商品文案
# ============================================================
@app.command(name="copy-virtual")
def copy_virtual_cmd(
    name: str = typer.Argument(..., help="产品名称（如 Python教程）"),
    price: int = typer.Option(..., "--price", "-p", help="价格"),
    features: str = typer.Option("", "--features", "-f", help="产品特点，逗号分隔"),
    tech_req: str = typer.Option("", "--tech", "-t", help="技术要求"),
):
    """生成虚拟商品（软件/教程/模板）的闲鱼文案"""
    feat_list = [f.strip() for f in features.split(",") if f.strip()]
    result = copy_virtual(name=name, price=price, features=feat_list, tech_req=tech_req)
    console.print(Panel(result["copy"], title=f"📝 {name} — 闲鱼虚拟商品文案", border_style="yellow"))
    console.print(f"\n[dim]关键词: {' '.join(result['keywords'])}[/dim]")
    copy_to_clipboard(result["copy"])


# ============================================================
# copy-optimize — 文案优化
# ============================================================
@app.command(name="copy-optimize")
def copy_optimize_cmd(
    text: str = typer.Argument(..., help="要优化的文案"),
    is_virtual: bool = typer.Option(False, "--virtual", "-v", help="是否为虚拟商品"),
):
    """优化现有闲鱼文案"""
    result = copy_optimize(text=text, is_virtual=is_virtual)
    console.print(Panel(result["optimized"], title="📝 优化后文案", border_style="blue"))
    if result.get("suggestions"):
        console.print("\n[yellow]优化建议:[/yellow]")
        for s in result["suggestions"]:
            console.print(f"  • {s}")
    copy_to_clipboard(result["optimized"])


# ============================================================
# item — 商品详情
# ============================================================
@app.command(name="item")
def item_cmd(
    item_id: str = typer.Argument(..., help="商品 ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="输出原始 JSON"),
):
    """查看闲鱼商品详情"""
    result = get_item(item_id)
    if raw:
        console.print_json(json.dumps(result, ensure_ascii=False))
        return

    item = result.get("item", result)
    console.print(Panel(
        f"[bold]{item.get('title', 'N/A')}[/bold]\n"
        f"价格: [bold green]¥{item.get('price', '?')}[/bold green]\n"
        f"成色: {item.get('condition', '?')}\n"
        f"地点: {item.get('location', '?')}\n"
        f"链接: [blue]{item.get('url', '')}[/blue]"
    ))


# ============================================================
# publish — 交互式发布
# ============================================================
@app.command(name="publish")
def publish_cmd(
    name: str = typer.Option("", "--name", "-n", help="商品名称"),
    price: int = typer.Option(0, "--price", "-p", help="价格"),
    images: str = typer.Option("", "--images", "-i", help="图片路径，逗号分隔"),
):
    """交互式发布商品到闲鱼（复制文案 → 上传图片 → 发布）"""
    # 交互式收集信息
    if not name:
        name = Prompt.ask("[bold]商品名称[/bold]")
    if not price:
        price = int(Prompt.ask("[bold]价格[/bold]", default="0"))

    condition = Prompt.ask("[bold]成色状态[/bold]", default="95新")
    features = Prompt.ask("[bold]核心卖点（逗号分隔）[/bold]", default="")
    location = Prompt.ask("[bold]发货地[/bold]", default="")

    # 生成文案
    feat_list = [f.strip() for f in features.split(",") if f.strip()]
    copy_result = copy_physical(name=name, condition=condition, price=price, features=feat_list, location=location)

    console.print("\n[bold cyan]📝 生成文案如下：[/bold cyan]")
    console.print(Panel(copy_result["copy"], border_style="green"))

    if Confirm.ask("确认发布？"):
        try:
            result = publish_item(name=name, price=price, images=images, desc=copy_result["copy"], keywords=copy_result["keywords"])
            console.print(f"[green]✅ 发布成功！商品 ID: {result.get('itemId', '?')}[/green]")
        except Exception as e:
            console.print(f"[red]❌ 发布失败: {e}[/red]")
    else:
        console.print("[yellow]已取消发布[/yellow]")


# ============================================================
# watch — 价格预警管理
# ============================================================
@app.command(name="watch")
def watch_cmd(
    action: str = typer.Argument("list", help="操作: add / list / remove"),
    query: str = typer.Option("", "--query", "-q", help="关键词"),
    target_price: int = typer.Option(0, "--price", "-p", help="目标价"),
):
    """管理闲鱼价格预警"""
    from goofish_cli_ext.commands.price_watch import (
        set_price_alert, list_price_alerts, remove_price_alert,
    )

    if action == "add":
        if not query or target_price <= 0:
            console.print("[red]请指定 --query 和 --price[/red]")
            return
        result = set_price_alert(query, target_price)
        console.print(f"[green]✅ 预警已设置：当「{query}」低于 ¥{target_price} 时通知[/green]")

    elif action == "remove":
        if not query:
            console.print("[red]请指定 --query[/red]")
            return
        remove_price_alert(query)
        console.print(f"[yellow]🗑️ 已删除「{query}」的预警[/yellow]")

    else:  # list
        alerts = list_price_alerts()
        if not alerts:
            console.print("[yellow]没有设置价格预警[/yellow]")
            console.print("[dim]添加预警：goofish-x watch add --query '南卡 Clip Super2' --price 250[/dim]")
            return
        console.print("[bold]📋 价格预警列表：[/bold]")
        for a in alerts:
            console.print(f"  🔔 {a['query']} → 低于 ¥{a['target_price']} 时通知")


# ============================================================
# price-summary — 价格汇总报告
# ============================================================
@app.command(name="price-summary")
def price_summary_cmd(
    query: str = typer.Argument(..., help="关键词"),
):
    """查看价格监控汇总：行情 + 已卖出分析 + 定价建议"""
    from goofish_cli_ext.commands.price_watch import format_price_summary
    summary = format_price_summary(query)
    console.print(Panel(summary, title=f"📊 {query} 价格报告", border_style="cyan"))


# ============================================================
# trend — 价格趋势
# ============================================================
@app.command(name="trend")
def trend_cmd(
    query: str = typer.Argument(..., help="关键词"),
    days: int = typer.Option(14, "--days", "-d", help="回溯天数"),
):
    """查看价格走势（含 ASCII 图表）"""
    from goofish_cli_ext.commands.price_watch import get_price_trend
    from goofish_cli_ext.commands.ascii_chart import price_sparkline
    trend = get_price_trend(query, days=days)

    if trend["snapshots"] == 0:
        console.print(f"[yellow]「{query}」暂无历史数据。搜索几次后趋势会自动生成。[/yellow]")
        return

    # 生成 ASCII 走势图
    chart_lines = ""
    if len(trend["daily_prices"]) >= 2:
        dates = [d["date"][5:] for d in trend["daily_prices"]]  # MM-DD
        avgs = [d["avg"] for d in trend["daily_prices"]]
        mins = [d["min"] for d in trend["daily_prices"]]
        maxs = [d["max"] for d in trend["daily_prices"]]
        chart_lines = price_sparkline(dates, avgs, mins, maxs)

    trend_icon = "📉" if trend["trend"] == "down" else "📈" if trend["trend"] == "up" else "➡️"
    trend_label = "下跌" if trend["trend"] == "down" else "上涨" if trend["trend"] == "up" else "平稳"

    console.print(Panel(
        f"[bold]{query}[/bold]\n"
        f"采样: {trend['snapshots']} 条数据 / {len(trend['daily_prices'])} 天\n"
        f"当前: ¥{trend['current_min']} ~ ¥{trend['current_avg']} ~ ¥{trend['current_max']}\n"
        f"历史: ¥{trend['min_overall']} ~ ¥{trend['avg_overall']} ~ ¥{trend['max_overall']}\n"
        f"趋势: {trend_icon} {trend_label}\n\n"
        f"{chart_lines}",
        title="📈 价格趋势",
        border_style="cyan",
    ))

    if trend.get("new_low_items"):
        console.print("\n[green]🆕 新出现的低价商品：[/green]")
        for item in trend["new_low_items"]:
            console.print(f"  ¥{item['price']} {item.get('title','')[:30]}")
            console.print(f"  {item.get('url', '')}")


# ============================================================
# sold — 已卖出分析
# ============================================================
@app.command(name="sold")
def sold_cmd(
    query: str = typer.Argument(..., help="关键词"),
):
    """分析可能已卖出的商品价格（成交价参考）"""
    from goofish_cli_ext.commands.price_watch import analyze_sold_prices
    sold = analyze_sold_prices(query)

    if sold["sold_count"] == 0:
        console.print(f"[yellow]「{query}」暂无已卖出数据。持续搜索后会积累数据。[/yellow]")
        return

    console.print(Panel(
        f"[bold]{query}[/bold]\n"
        f"已卖出: [bold]{sold['sold_count']}[/bold] 件\n"
        f"成交均价: [green]¥{sold['sold_avg_price']}[/green]  "
        f"(¥{sold['sold_min_price']} ~ ¥{sold['sold_max_price']})\n"
        f"当前在售均价: ¥{sold['listing_avg_price']} ({sold['listing_count']}件)",
        title="📈 已卖出价格分析",
        border_style="green",
    ))

    console.print("\n[bold]出售记录（按价格排序）：[/bold]")
    for item in sold["sold_items"][:10]:
        console.print(f"  ¥{item['price']:>4d}  {item.get('title','')[:40]}  [{item.get('condition','')}]")
        if item.get("last_seen"):
            console.print(f"       最后出现: {item['last_seen']}  (上架{item['days_listed']}天)")


# ============================================================
# suggest — 定价建议
# ============================================================
@app.command(name="suggest")
def suggest_cmd(
    query: str = typer.Argument(..., help="关键词"),
    condition: str = typer.Option("95新", "--condition", "-c", help="你的商品成色"),
    location: str = typer.Option("", "--location", "-l", help="地区"),
):
    """基于行情+成色给出定价建议"""
    from goofish_cli_ext.commands.price_watch import suggest_price
    result = suggest_price(query, condition=condition, location=location)

    if result["confidence"] == "low" and "数据不足" in result.get("reason", ""):
        console.print(f"[yellow]{result['reason']}[/yellow]")
        return

    # 推荐策略
    tier_colors = {"fast": "yellow", "balanced": "green", "patient": "blue"}
    tier_icons = {"fast": "⚡", "balanced": "🎯", "patient": "🧘"}
    tier = result.get("recommended_tier", "balanced")
    color = tier_colors.get(tier, "green")
    icon = tier_icons.get(tier, "🎯")

    console.print(Panel(
        f"[bold]{query}[/bold]  (成色: {condition})\n\n"
        f"[bold {color}]{icon} 推荐策略: {tier}[/bold {color}]\n"
        f"  [bold green]建议定价: ¥{result['suggested_price']}[/bold green] ← 推荐\n"
        f"  ⚡快速出手: ¥{result['fast_sell_price']}  (打9折快速卖出)\n"
        f"  🧘耐心等待: ¥{result['patient_price']}  (加8%挂高价)\n\n"
        f"📊 参考数据:\n"
        f"  在售均价: ¥{result['avg_listing_price']}  |  中位数: ¥{result['median_listing_price']}\n"
        f"  价格区间: ¥{result['price_range'][0]} ~ ¥{result['price_range'][-1]}\n"
        f"  已卖出均价: ¥{result['avg_sold_price'] if result['avg_sold_price'] else '暂无数据'}\n\n"
        f"💡 {result['reason']}",
        title="💰 定价建议",
        border_style=color,
    ))


# ============================================================
# negotiate — 议价话术模板
# ============================================================
@app.command(name="negotiate")
def negotiate_cmd(
    scenario: str = typer.Argument("", help="场景: 小刀/大刀/屠龙刀/打包/面交/质量问题"),
    price: int = typer.Option(0, "--price", "-p", help="你的标价"),
    condition: str = typer.Option("95新", "--condition", "-c", help="成色"),
    market_price: int = typer.Option(0, "--market", "-m", help="市场均价"),
    counter_offer: int = typer.Option(0, "--counter", "-o", help="你能接受的价格"),
    low_price: int = typer.Option(0, "--low", "-l", help="买家出价"),
    accessory: str = typer.Option("小配件", "--accessory", "-a", help="附送配件"),
    location: str = typer.Option("", "--location", "-L", help="面交地点"),
):
    """议价话术模板 — 买家砍价时的应对话术库"""
    from goofish_cli_ext.commands.negotiation import get_negotiation_script, format_negotiation

    if not scenario:
        # 列出所有场景
        result = get_negotiation_script()
        console.print(Panel(format_negotiation(result), title="📋 议价场景", border_style="yellow"))
        console.print("\n[dim]使用: goofish-x negotiate 小刀 --price 248[/dim]")
        return

    result = get_negotiation_script(
        scenario=scenario,
        price=price,
        condition=condition,
        market_price=market_price or int(price * 1.1) if price else 0,
        counter_offer=counter_offer or int(price * 0.85) if price else 0,
        low_price=low_price or int(price * 0.5) if price else 0,
        discount=int(price * 0.1) if price else 0,
        accessory=accessory,
        location=location,
    )

    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return

    console.print(Panel(format_negotiation(result), title=f"💬 {scenario} — {result['description']}", border_style="yellow"))
    copy_to_clipboard(result.get("templates", [{}])[0].get("text", "") if result.get("templates") else "")


# ============================================================
# convert — 多平台文案互转
# ============================================================
@app.command(name="convert")
def convert_cmd(
    to: str = typer.Argument(..., help="目标平台: 转转/拍拍/闲鱼"),
    text: str = typer.Option("", "--text", "-t", help="要转换的文案（留空从剪贴板读取）"),
    from_platform: str = typer.Option("", "--from", "-f", help="来源平台（留空自动检测）"),
):
    """多平台文案互转 — 闲鱼 ↔ 转转 ↔ 拍拍"""
    from goofish_cli_ext.commands.platform_convert import convert_copy, PLATFORMS

    if to not in PLATFORMS:
        console.print(f"[red]目标平台必须是: {', '.join(PLATFORMS.keys())}[/red]")
        return

    # 如果没提供文案，尝试从剪贴板读
    if not text:
        try:
            import subprocess
            text = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout.strip()
            if text:
                console.print("[dim]从剪贴板读取文案[/dim]")
        except Exception:
            pass

    if not text:
        console.print("[yellow]请提供文案: --text '你的文案' 或先复制到剪贴板[/yellow]")
        return

    result = convert_copy(text, from_platform=from_platform, to_platform=to)

    console.print(Panel(
        result["converted"],
        title=f"🔄 {result['from_platform']} → {result['to_platform']}",
        border_style="green",
    ))

    console.print("\n[dim]改动:[/dim]")
    for c in result["changes"]:
        console.print(f"  • {c}")

    copy_to_clipboard(result["converted"])


# ============================================================
# version
# ============================================================
@app.command(name="version")
def version_cmd():
    """打印版本号"""
    try:
        from goofish_cli_ext import __version__
        print(f"goofish-cli-ext {__version__}")
    except ImportError:
        print("goofish-cli-ext 0.1.0")


# ============================================================
# util: copy to clipboard
# ============================================================
def copy_to_clipboard(text: str):
    """尝试复制到剪贴板，macOS 用 pbcopy"""
    try:
        import subprocess
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"))
        console.print("[dim]✅ 文案已复制到剪贴板[/dim]")
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(app())
