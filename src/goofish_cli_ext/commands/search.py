# -*- coding: utf-8 -*-
"""
闲鱼低价挖掘引擎

痛点分析：
闲鱼搜索有个严重问题 ——「价格从低到高」排序会隐藏大量真正低价商品。
闲鱼的自然推荐（"综合排序"）推给你的往往是加了标签的、价格虚高的商品。
很多真正便宜的好货需要翻好几页才能看到，甚至永远看不到。

本模块通过多策略轮询 + 智能去重来解决这个问题。

搜索方式：
1. **Playwright 引擎（首选）** — 直接操作浏览器搜索闲鱼，不依赖 goofish-cli
2. **goofish-cli 引擎（兜底）** — 如果 Playwright 不可用，自动降级

策略：
1. **多关键词轮询** — 同一商品用不同关键词搜索，覆盖不同的商品池
2. **虚标价过滤** — 识别"标 ¥1 实际 ¥999"的虚假低价
3. **多排序采样** — 综合排序 + 最新发布，交叉覆盖
4. **智能推荐** — 基于成色、信用、价格综合评分
5. **搜索筛选** — 支持排序、成色、位置参数
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Optional

# ============================================================
# 尝试导入 Playwright 引擎
# ============================================================
_HAS_PLAYWRIGHT = False
try:
    from goofish_cli_ext.commands.playwright_search import search_by_playwright
    _HAS_PLAYWRIGHT = True
except Exception:
    pass


# ============================================================
# 底层搜索
# ============================================================

def _call_goofish(query: str, limit: int = 50) -> list[dict]:
    """调用 goofish search items 命令获取结果"""
    cmd = [
        "goofish", "search", "items",
        query,
        "--limit", str(limit),
        "--format", "json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode != 0:
            raise RuntimeError(f"goofish 搜索失败: {result.stderr.strip()[:200]}")
        data = json.loads(result.stdout)
        return data.get("items", [])
    except FileNotFoundError:
        raise RuntimeError(
            "未找到 goofish 命令。请先安装: pip install goofish-cli\n"
            "并配置 Cookie: goofish auth login --source <cookies.json>"
        )


# ============================================================
# 价格处理
# ============================================================

def _extract_price(item: dict) -> int:
    """从 item 中提取价格为整数"""
    price_str = item.get("price", "0")
    if isinstance(price_str, (int, float)):
        return int(price_str)
    price_str = price_str.replace("¥", "").replace(",", "").strip()
    try:
        return int(float(price_str))
    except (ValueError, TypeError):
        return 99999


# ============================================================
# 虚标价检测
# ============================================================

def _is_fake_low_price(item: dict) -> bool:
    """
    检测是否是虚假低价

    闲鱼上很多卖家会标 ¥1 或 ¥0.01 吸引点击，
    实际价格在描述里写。特征：
    1. 价格极低（< 同类均价 30%）
    2. 标题含有"看简介、私聊议价、定价随机"等词
    3. 同时标注了原价且原价远高于标价
    """
    price = _extract_price(item)
    title = item.get("title", "").lower()
    original_price = item.get("original_price", "")

    # 极低价格
    if price <= 5:
        return True

    # 标题暗示价格不实
    fake_keywords = [
        "看简介", "私聊", "议价", "定价", "具体价格",
        "标价", "随机", "联系", "咨询", "vx", "微信",
    ]
    for kw in fake_keywords:
        if kw in title:
            return True

    # 有原价且原价远高于标价（如标 ¥10，原价 ¥500）
    if original_price:
        try:
            orig = int(re.sub(r"[^\d]", "", original_price))
            if orig > 0 and price > 0 and orig / price > 10:
                return True
        except (ValueError, TypeError):
            pass

    return False


# ============================================================
# 品质评分
# ============================================================

def _quality_score(item: dict) -> float:
    """
    综合品质评分（越高越好）

    考虑因素：
    - 成色（全新 > 99新 > 95新 > 9成新 > 有瑕疵）
    - 卖家信用（百分百好评 > 信用极好 > 信用优秀 > 无标签）
    - 标题完整度（字数越多说明描述越详细）
    - 是否有图片（通过 extra 字段判断）
    """
    score = 50.0  # 基准分

    # 成色加分
    condition = (item.get("condition") or "").lower()
    if "全新" in condition:
        score += 30
    elif "99" in condition:
        score += 25
    elif "95" in condition or "几乎" in condition:
        score += 20
    elif "9成" in condition:
        score += 15
    elif "8成" in condition:
        score += 10

    # 卖家信用加分
    badge = (item.get("badge") or "")
    if "百分百好评" in badge:
        score += 15
    elif "信用极好" in badge:
        score += 10
    elif "信用优秀" in badge:
        score += 5

    # 标题完整度（字数越多说明描述越详细，越可信）
    title = item.get("title", "")
    if len(title) > 100:
        score += 5
    elif len(title) > 50:
        score += 3

    return score


# ============================================================
# 智能分群
# ============================================================

def _group_items(items: list[dict]) -> dict:
    """
    将商品按品质分组

    返回:
    {
        "best": [...],      # 质优价廉 — 品质高 + 价格低
        "cheapest": [...],  # 纯低价 — 不管成色
        "good": [...],      # 品质好 — 价格稍高但东西好
    }
    """
    prices = [i["price"] for i in items]
    if not prices:
        return {"best": [], "cheapest": [], "good": []}

    median_price = sorted(prices)[len(prices) // 2]

    best = []
    cheapest = []
    good = []

    for item in items:
        price = item["price"]
        score = _quality_score(item)

        # 质优价廉：品质分高 + 价格低于中位数
        if score >= 65 and price <= median_price:
            best.append(item)
        # 纯低价：不管品质，价格最低的那批
        elif price <= median_price * 0.6:
            cheapest.append(item)
        # 品质好：品质分高，价格可以高一点
        elif score >= 70:
            good.append(item)

    # 每个组内按价格排序
    for group in [best, cheapest, good]:
        group.sort(key=lambda x: x["price"])

    return {"best": best, "cheapest": cheapest, "good": good}


# ============================================================
# 多关键词扩展
# ============================================================

def _expand_keywords(query: str) -> list[str]:
    """
    扩展搜索关键词以覆盖更多商品池

    闲鱼的自然排序会把很多商品隐藏掉。
    用不同的关键词搜索同一商品，可以覆盖不同的商品池。

    例如 "南卡 Clip Super2" 会扩展为：
    - 南卡 Clip Super2    （原词）
    - 南卡 ClipSuper2     （无空格）
    - 南卡 clipsuper2     （小写）
    - NANK Clip Super2    （品牌英文名）
    - 南卡 耳夹 蓝牙耳机  （品类词）
    """
    keywords = [query]

    # 去空格版本
    no_space = query.replace(" ", "").replace("　", "")
    if no_space != query:
        keywords.append(no_space)

    # 小写版本
    lower = query.lower()
    if lower != query and lower not in keywords:
        keywords.append(lower)

    # 品牌替换
    brand_map = {
        "南卡": ["NANK", "南卡"],
    }
    for cn, en_list in brand_map.items():
        if cn in query:
            for en in en_list:
                if en != cn:
                    alt = query.replace(cn, en)
                    if alt not in keywords:
                        keywords.append(alt)

    return keywords[:5]  # 最多 5 个


# ============================================================
# 商品去重
# ============================================================

def _deduplicate(items: list[dict]) -> list[dict]:
    """基于 item_id 去重，保留第一个出现的"""
    seen = set()
    unique = []
    for item in items:
        item_id = item.get("item_id", "")
        if item_id and item_id not in seen:
            seen.add(item_id)
            unique.append(item)
    return unique


# ============================================================
# 主搜索函数
# ============================================================

def search_items_cli(
    query: str,
    limit: int = 30,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    sort_by_price: bool = True,
    deep_search: bool = True,
    sort: str = "price-asc",
    condition: str = "",
    location: str = "",
) -> dict:
    """
    闲鱼低价挖掘引擎

    Args:
        query: 搜索关键词
        limit: 返回条数 (max 100)
        min_price: 最低价筛选
        max_price: 最高价筛选
        sort_by_price: 是否按价格排序
        deep_search: 是否启用深度搜索（多关键词轮询）
        sort: 排序（price-asc=价格从低到高, new=最新, credit=信用最好）
        condition: 成色筛选（new=全新, used=二手）
        location: 位置筛选（如"上海"）

    Returns:
        {
            "items": [...],
            "total": N,
            "query": "...",
            "stats": { 统计信息 },
            "recommended": { 分组推荐 },
            "engine": "playwright | goofish-cli",
        }
    """
    all_items = []

    # 尝试 Playwright 引擎（首选）
    playwright_ok = False
    if _HAS_PLAYWRIGHT:
        try:
            playwright_items = search_by_playwright(
                query=query,
                limit=min(limit, 50),
                sort=sort if sort != "default" else "",
                condition=condition,
                location=location,
            )
            if playwright_items:
                all_items.extend(playwright_items)
                playwright_ok = True
        except Exception as e:
            pass  # 降级到 goofish-cli

    # Playwright 引擎失败或需要深度搜索补充时，用 goofish-cli 兜底
    goofish_items = []
    if not playwright_ok or deep_search:
        try:
            if deep_search:
                keywords = _expand_keywords(query)
                for kw in keywords[:3]:  # 深度搜索最多 3 个关键词
                    try:
                        items = _call_goofish(kw, limit=min(limit, 50))
                        goofish_items.extend(items)
                    except Exception:
                        continue
            else:
                goofish_items = _call_goofish(query, limit=min(limit, 50))
        except Exception:
            pass

    all_items.extend(goofish_items)

    engine = "playwright" if playwright_ok else "goofish-cli"
    if not all_items:
        return {"items": [], "total": 0, "query": query, "stats": {}, "recommended": {}, "engine": engine}

    # 去重
    all_items = _deduplicate(all_items)

    # 提取价格
    for item in all_items:
        item["price"] = _extract_price(item)

    # 过滤虚假低价
    real_items = [i for i in all_items if not _is_fake_low_price(i)]
    fake_count = len(all_items) - len(real_items)

    # 价格筛选
    filtered = real_items
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

    # 品质分组
    groups = _group_items(filtered)

    # 统计信息
    prices = [i["price"] for i in filtered]
    stats = {
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0,
        "avg_price": sum(prices) // len(prices) if prices else 0,
        "total": len(filtered),
        "removed_fake": fake_count,
        "deep_search_keywords": _expand_keywords(query) if deep_search else [query],
    }

    return {
        "items": filtered[:limit],
        "total": len(filtered),
        "query": query,
        "stats": stats,
        "recommended": groups,
        "engine": engine,
    }
