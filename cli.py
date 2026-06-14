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