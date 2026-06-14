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
    limit: int = typer.Option(20, "--limit", "-n", help="返回条数"),
    min_price: Optional[int] = typer.Option(None, "--min", "-m", help="最低价筛选"),
    max_price: Optional[int] = typer.Option(None, "--max", "-M", help="最高价筛选"),
    sort_by_price: bool = typer.Option(True, "--sort/--no-sort", help="按价格排序"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON 格式输出"),
):
    """搜索闲鱼商品，按价格排序，展示最低价"""
    result = search_items_cli(query, limit, min_price, max_price, sort_by_price)

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
