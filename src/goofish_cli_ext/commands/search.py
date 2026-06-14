# -*- coding: utf-8 -*-
"""搜索命令 —— 封装 goofish search items，增加价格排序、筛选、格式化"""

from __future__ import annotations

import json
import subprocess
from typing import Optional


def _call_goofish(query: str, limit: int = 20) -> list[dict]:
    """调用 goofish search items 命令获取结果"""
    cmd = [
        "goofish", "search", "items",
        query,
        "--limit", str(limit),
        "--format", "json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"goofish 搜索失败: {result.stderr.strip()}")
        data = json.loads(result.stdout)
        return data.get("items", [])
    except FileNotFoundError:
        raise RuntimeError(
            "未找到 goofish 命令。请先安装: pip install goofish-cli\n"
            "并配置 Cookie: goofish auth login --source <cookies.json>"
        )


def _extract_price(item: dict) -> int:
    """从 item 中提取价格为整数"""
    price_str = item.get("price", "0")
    if isinstance(price_str, (int, float)):
        return int(price_str)
    # 去掉 ¥ 符号
    price_str = price_str.replace("¥", "").replace(",", "").strip()
    try:
        return int(float(price_str))
    except (ValueError, TypeError):
        return 99999


def search_items_cli(
    query: str,
    limit: int = 20,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    sort_by_price: bool = True,
) -> dict:
    """搜索闲鱼商品

    Args:
        query: 搜索关键词
        limit: 返回条数 (max 50)
        min_price: 最低价筛选
        max_price: 最高价筛选
        sort_by_price: 是否按价格排序

    Returns:
        {"items": [...], "total": N, "query": "..."}
    """
    raw_items = _call_goofish(query, min(limit, 50))

    # 提取价格
    for item in raw_items:
        item["price"] = _extract_price(item)

    # 价格筛选
    filtered = raw_items
    if min_price is not None:
        filtered = [i for i in filtered if i["price"] >= min_price]
    if max_price is not None:
        filtered = [i for i in filtered if i["price"] <= max_price]

    # 按价格排序
    if sort_by_price:
        filtered = sorted(filtered, key=lambda x: x["price"])

    # 重排 rank
    for idx, item in enumerate(filtered, 1):
        item["rank"] = idx

    return {
        "items": filtered[:limit],
        "total": len(filtered),
        "query": query,
    }
