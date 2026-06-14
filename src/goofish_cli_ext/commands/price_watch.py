# -*- coding: utf-8 -*-
"""
闲鱼价格监控模块
持久化存储+价格跟踪+趋势+已售分析

功能：
1. 记录每次搜索的价格数据到 SQLite
2. 跟踪同关键词的价格变化趋势
3. 新增低价商品检测
4. 已卖出/下架商品分析（通过商品消失检测）
5. 定价建议（基于历史均价+成色分布）

数据文件：~/.goofish-cli-ext/price_watch.db
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


# ============================================================
# 数据库路径
# ============================================================

_DB_DIR = os.path.expanduser("~/.goofish-cli-ext")
_DB_PATH = os.path.join(_DB_DIR, "price_watch.db")


def _ensure_db():
    """确保数据库目录和表存在"""
    os.makedirs(_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            item_id TEXT NOT NULL,
            title TEXT,
            price INTEGER NOT NULL,
            condition TEXT,
            location TEXT,
            badge TEXT,
            url TEXT,
            snapshot_at INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_query_snapshot
        ON price_snapshots(query, snapshot_at)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_item_id
        ON price_snapshots(item_id)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL UNIQUE,
            target_price INTEGER NOT NULL,
            notify_on_new INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL,
            last_notified_at INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ============================================================
# 保存搜索结果快照
# ============================================================

def save_snapshot(query: str, items: list[dict]):
    """保存一次搜索结果的快照到数据库"""
    _ensure_db()
    now = int(time.time())
    conn = sqlite3.connect(_DB_PATH)

    # 标记该查询之前的活跃商品为可能已下架
    conn.execute(
        "UPDATE price_snapshots SET is_active=0 WHERE query=? AND snapshot_at < ?",
        (query, now - 86400)  # 超过1天的标记为不活跃
    )

    for item in items:
        item_id = item.get("item_id", "")
        if not item_id:
            continue
        price = item.get("price", 0)
        if isinstance(price, str):
            price = int(price.replace("¥", "").replace(",", "").strip() or "0")

        conn.execute(
            """INSERT INTO price_snapshots
               (query, item_id, title, price, condition, location, badge, url, snapshot_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                query,
                item_id,
                item.get("title", "")[:200],
                price,
                item.get("condition", ""),
                item.get("location", ""),
                item.get("badge", ""),
                item.get("url", ""),
                now,
            ),
        )
    conn.commit()
    conn.close()


# ============================================================
# 价格趋势分析
# ============================================================

def get_price_trend(query: str, days: int = 14) -> dict:
    """获取指定关键词的价格趋势

    Returns:
        {
            "query": "...",
            "days": N,
            "snapshots": N,          # 快照次数
            "current_min": N,
            "current_avg": N,
            "current_max": N,
            "min_overall": N,        # 历史最低价
            "trend": "down|up|stable", # 趋势方向
            "daily_prices": [        # 每日均价
                {"date": "2026-06-01", "min": N, "avg": N, "max": N, "count": N},
                ...
            ],
            "new_low_items": [...],   # 新出现的低价商品
            "disappeared_items": [...], # 下架/消失的商品
        }
    """
    _ensure_db()
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row

    cutoff = int(time.time()) - days * 86400

    # 所有快照
    rows = conn.execute(
        """SELECT * FROM price_snapshots
           WHERE query=? AND snapshot_at >= ?
           ORDER BY snapshot_at DESC""",
        (query, cutoff),
    ).fetchall()

    conn.close()

    if not rows:
        return {"query": query, "days": days, "snapshots": 0}

    # 按天分组
    daily = defaultdict(list)
    for row in rows:
        day = datetime.fromtimestamp(row["snapshot_at"]).strftime("%Y-%m-%d")
        daily[day].append(row["price"])

    daily_prices = []
    for day in sorted(daily.keys()):
        prices = daily[day]
        daily_prices.append({
            "date": day,
            "min": min(prices),
            "avg": sum(prices) // len(prices),
            "max": max(prices),
            "count": len(prices),
        })

    # 最新一天的数据
    latest = daily_prices[-1] if daily_prices else {}
    all_prices = [r["price"] for r in rows]

    # 趋势判断
    trend = "stable"
    if len(daily_prices) >= 3:
        first_avg = daily_prices[0]["avg"]
        last_avg = daily_prices[-1]["avg"]
        if last_avg < first_avg * 0.95:
            trend = "down"
        elif last_avg > first_avg * 1.05:
            trend = "up"

    # 检测新出现的低价商品（上次未出现、这次出现的低价商品）
    latest_items = [r for r in rows if r["snapshot_at"] >= cutoff + (days - 1) * 86400]
    older_items = [r for r in rows if r["snapshot_at"] < cutoff + (days - 1) * 86400]
    older_ids = set(r["item_id"] for r in older_items)
    new_low_items = [
        {"item_id": r["item_id"], "title": r["title"], "price": r["price"],
         "url": r["url"], "condition": r["condition"], "location": r["location"]}
        for r in latest_items
        if r["item_id"] not in older_ids and r["price"] <= (latest.get("min", 99999) * 1.1)
    ][:5]

    return {
        "query": query,
        "days": days,
        "snapshots": len(rows),
        "current_min": latest.get("min", 0),
        "current_avg": latest.get("avg", 0),
        "current_max": latest.get("max", 0),
        "min_overall": min(all_prices),
        "max_overall": max(all_prices),
        "avg_overall": sum(all_prices) // len(all_prices),
        "trend": trend,
        "daily_prices": daily_prices,
        "new_low_items": new_low_items,
    }


# ============================================================
# 已卖出价格分析 (#13)
# ============================================================

def analyze_sold_prices(query: str) -> dict:
    """
    分析可能已卖出的商品价格

    策略：如果一个商品 ID 在之前的快照中出现过，
    但在最近一次快照中消失了，它可能已卖出（或下架）。
    这些"消失的商品"的成交价更有参考价值。

    Returns:
        {
            "query": "...",
            "sold_items": [
                {"item_id": "...", "title": "...", "price": N,
                 "last_seen": "2026-06-10", "condition": "...",
                 "days_listed": N},
            ],
            "sold_count": N,
            "sold_avg_price": N,
            "sold_price_range": [min, max],
            "listing_avg_price": N,  # 当前在售均价（对比用）
        }
    """
    _ensure_db()
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row

    cutoff = int(time.time()) - 30 * 86400

    # 获取所有出现过的商品 ID 和价格
    rows = conn.execute(
        """SELECT item_id, title, price, condition, location, badge,
                  MAX(snapshot_at) as last_seen,
                  MIN(snapshot_at) as first_seen,
                  COUNT(*) as appearances
           FROM price_snapshots
           WHERE query=? AND snapshot_at >= ?
           GROUP BY item_id
           ORDER BY last_seen DESC""",
        (query, cutoff),
    ).fetchall()

    # 获取最近一次快照时间
    last_snapshot = conn.execute(
        "SELECT MAX(snapshot_at) as ts FROM price_snapshots WHERE query=?",
        (query,),
    ).fetchone()
    last_snapshot_ts = last_snapshot["ts"] if last_snapshot else 0

    # 当前在售商品 ID
    active_ids = set(
        r["item_id"] for r in rows
        if r["last_seen"] >= last_snapshot_ts - 3600  # 最近1小时内出现的
    )

    conn.close()

    # 可能已卖出的：出现过但最近不在活跃列表中
    sold = []
    listing_prices = []
    sold_prices = []

    for r in rows:
        if r["item_id"] in active_ids:
            listing_prices.append(r["price"])
        else:
            # 连续多次出现后消失 → 更可能是已卖出
            if r["appearances"] >= 2 or (r["last_seen"] > cutoff + 7 * 86400):
                sold.append({
                    "item_id": r["item_id"],
                    "title": r["title"],
                    "price": r["price"],
                    "condition": r["condition"],
                    "location": r["location"],
                    "last_seen": datetime.fromtimestamp(r["last_seen"]).strftime("%Y-%m-%d"),
                    "first_seen": datetime.fromtimestamp(r["first_seen"]).strftime("%Y-%m-%d"),
                    "days_listed": (r["last_seen"] - r["first_seen"]) // 86400,
                    "appearances": r["appearances"],
                })
                sold_prices.append(r["price"])

    return {
        "query": query,
        "sold_count": len(sold),
        "sold_items": sorted(sold, key=lambda x: x["price"])[:20],
        "sold_avg_price": sum(sold_prices) // len(sold_prices) if sold_prices else 0,
        "sold_min_price": min(sold_prices) if sold_prices else 0,
        "sold_max_price": max(sold_prices) if sold_prices else 0,
        "listing_count": len(listing_prices),
        "listing_avg_price": sum(listing_prices) // len(listing_prices) if listing_prices else 0,
    }


# ============================================================
# 定价建议 (#7)
# ============================================================

def suggest_price(
    query: str,
    condition: str = "",
    location: str = "",
) -> dict:
    """
    基于历史数据和当前行情给出定价建议

    Args:
        query: 商品关键词
        condition: 成色（如"95新"、"全新"）
        location: 地区

    Returns:
        {
            "query": "...",
            "suggested_price": N,          # 建议定价
            "fast_sell_price": N,          # 快速出手价
            "patient_price": N,            # 耐心等高价
            "confidence": "high|medium|low",
            "price_range": [min, max],
            "avg_listing_price": N,        # 当前在售均价
            "avg_sold_price": N,           # 已卖出均价（有数据的话）
            "condition_adjustment": N,     # 成色调整
            "location_adjustment": N,      # 地区调整
            "recommended_tier": "fast|balanced|patient",
            "reason": "...",
        }
    """
    # 获取已卖出分析（如果有数据）
    sold = analyze_sold_prices(query)
    sold_avg = sold.get("sold_avg_price", 0)

    # 获取当前行情
    _ensure_db()
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    now = int(time.time())

    # 最近7天的快照
    rows = conn.execute(
        """SELECT DISTINCT item_id, price, condition, location
           FROM price_snapshots
           WHERE query=? AND snapshot_at >= ?
           ORDER BY snapshot_at DESC""",
        (query, now - 7 * 86400),
    ).fetchall()
    conn.close()

    if not rows:
        return {"query": query, "confidence": "low", "reason": "数据不足，建议先搜索几次积累数据"}

    # 去重统计
    seen_ids = set()
    prices = []
    for r in rows:
        if r["item_id"] not in seen_ids:
            seen_ids.add(r["item_id"])
            prices.append(r["price"])

    prices.sort()
    avg_price = sum(prices) // len(prices)
    median_price = prices[len(prices) // 2]

    # 成色调整
    cond_multiplier = 1.0
    condition_lower = condition.lower()
    if "全新" in condition_lower:
        cond_multiplier = 1.15  # 全新比均价高15%
    elif "99" in condition_lower:
        cond_multiplier = 1.08
    elif "95" in condition_lower or "几乎" in condition_lower:
        cond_multiplier = 1.0
    elif "9成" in condition_lower:
        cond_multiplier = 0.90
    elif "8成" in condition_lower:
        cond_multiplier = 0.75
    elif "瑕疵" in condition_lower or "磕碰" in condition_lower:
        cond_multiplier = 0.60

    # 已卖出数据调整（如果真实卖出价比均价低，说明当前标价偏高）
    sold_adjustment = 1.0
    if sold_avg > 0 and avg_price > 0:
        ratio = sold_avg / avg_price
        if ratio < 0.85:
            sold_adjustment = 0.90  # 真实成交价远低于标价，建议压低

    suggested = int(median_price * cond_multiplier * sold_adjustment)
    fast_sell = int(suggested * 0.90)    # 快速出手打9折
    patient = int(suggested * 1.08)      # 耐心等高价加8%

    # 置信度
    confidence = "high"
    if sold_avg == 0:
        confidence = "medium"
    if len(prices) < 3:
        confidence = "low"

    # 推荐策略
    recommended_tier = "balanced"
    reason_parts = []

    if sold_avg > 0:
        reason_parts.append(f"历史成交均价¥{sold_avg}")

    if cond_multiplier != 1.0:
        diff = int((cond_multiplier - 1.0) * 100)
        sign = "+" if diff > 0 else ""
        reason_parts.append(f"成色调整{sign}{diff}%")

    if sold_adjustment < 1.0:
        reason_parts.append("标价偏高已做下调")
        recommended_tier = "fast"

    reason_parts.append(f"在售{len(prices)}件均价¥{avg_price}")

    return {
        "query": query,
        "suggested_price": suggested,
        "fast_sell_price": fast_sell,
        "patient_price": patient,
        "confidence": confidence,
        "price_range": [prices[0], prices[-1]],
        "avg_listing_price": avg_price,
        "median_listing_price": median_price,
        "avg_sold_price": sold_avg,
        "condition_adjustment": int((cond_multiplier - 1.0) * 100),
        "location_adjustment": 0,
        "recommended_tier": recommended_tier,
        "reason": "，".join(reason_parts),
    }


# ============================================================
# 价格预警管理
# ============================================================

def set_price_alert(query: str, target_price: int) -> dict:
    """设置价格预警"""
    _ensure_db()
    conn = sqlite3.connect(_DB_PATH)
    now = int(time.time())
    conn.execute(
        """INSERT OR REPLACE INTO price_thresholds
           (query, target_price, notify_on_new, created_at)
           VALUES (?, ?, 1, ?)""",
        (query, target_price, now),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "query": query, "target_price": target_price}


def list_price_alerts() -> list[dict]:
    """列出所有价格预警"""
    _ensure_db()
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM price_thresholds ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        {
            "query": r["query"],
            "target_price": r["target_price"],
            "created_at": datetime.fromtimestamp(r["created_at"]).strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]


def remove_price_alert(query: str) -> dict:
    """删除价格预警"""
    _ensure_db()
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("DELETE FROM price_thresholds WHERE query=?", (query,))
    conn.commit()
    conn.close()
    return {"ok": True, "query": query}


def check_price_alerts(alerts: list[dict], items: list[dict]) -> list[dict]:
    """检查是否有商品触发价格预警

    Args:
        alerts: 预警列表 [{"query": "...", "target_price": N}, ...]
        items: 当前搜索到的商品列表

    Returns:
        触发的预警列表 [{"query": "...", "target_price": N,
                        "current_min": N, "matched_items": [...]}, ...]
    """
    triggered = []
    if not alerts:
        return triggered

    item_prices = {}
    for item in items:
        q = item.get("query", "")
        price = item.get("price", 99999)
        if q not in item_prices or price < item_prices[q].get("price", 99999):
            item_prices[q] = item

    for alert in alerts:
        q = alert["query"]
        if q in item_prices:
            item = item_prices[q]
            if item["price"] <= alert["target_price"]:
                triggered.append({
                    "query": q,
                    "target_price": alert["target_price"],
                    "current_min": item["price"],
                    "matched_items": [item],
                })

    return triggered


# ============================================================
# 价格监控 CLI
# ============================================================

def format_price_summary(query: str) -> str:
    """生成价格监控摘要（文本，适合微信推送）"""
    trend = get_price_trend(query, days=14)
    sold = analyze_sold_prices(query)
    pricing = suggest_price(query)

    lines = []
    lines.append(f"📊 {query} 价格监控")
    lines.append("")

    if trend["snapshots"] > 0:
        lines.append(f"当前行情: ¥{trend['current_min']} ~ ¥{trend['current_avg']} ~ ¥{trend['current_max']}")
        lines.append(f"历史最低: ¥{trend['min_overall']}  |  趋势: {'📉' if trend['trend'] == 'down' else '📈' if trend['trend'] == 'up' else '➡️'}{trend['trend']}")
        lines.append(f"采样天数: {trend['days']}天 / {trend['snapshots']}条数据")
        lines.append("")

    if sold["sold_count"] > 0:
        lines.append(f"📈 已卖出分析:")
        lines.append(f"  成交均价 ¥{sold['sold_avg_price']}  (当前在售均价 ¥{sold['listing_avg_price']})")
        lines.append(f"  已卖出 {sold['sold_count']} 件")
        lines.append("")

    if pricing.get("confidence") != "low":
        lines.append(f"💰 定价建议 ({pricing['confidence']}):")
        lines.append(f"  快速出手: ¥{pricing['fast_sell_price']}")
        lines.append(f"  建议定价: ¥{pricing['suggested_price']} ← 推荐")
        lines.append(f"  耐心等待: ¥{pricing['patient_price']}")
        lines.append(f"  理由: {pricing['reason']}")
    else:
        lines.append(f"💡 {pricing['reason']}")

    return "\n".join(lines)
