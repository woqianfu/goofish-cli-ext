# -*- coding: utf-8 -*-
"""
闲鱼终极低价搜索组合器

原理：闲鱼对每个搜索词独立返回前 ~250 条结果。
通过穷举「关键词 × 排序 × 价格暗示 × 城市 × 成色」的笛卡尔积组合，
可以覆盖远超 250 条的结果集。

穷举策略树：
┌─ 关键词变体（25种）
│   ├─ 原词 / 去空格 / 小写 / 品牌切换
│   ├─ +品质后缀: 全新/二手/自用/正品/包邮/闲置/急出/降价/好价/超值
│   ├─ +卖家身份: 个人/学生/自用/公司/商家
│   └─ 品类词: 耳机/数码/配件/蓝牙
├─ 排序方式（5种）
│   ├─ 默认综合 / price-asc / price-desc / new / credit
├─ 价格暗示词（5档）
│   ├─ 50元以内 / 100元以内 / 200以内 / 300以内 / 500以内
│   └─ 低至XX / 只要XX / XX出
├─ 城市（5个热门）
└─ 成色（全新/二手/全部）

组合数 = 25×5×5×5×3 = 9,375 次搜索 → 理论上限 ~2,343,750 条
实战推荐 = 25×2×3×1×1 = 150 次搜索 → 理论 ~37,500 条
"""

from __future__ import annotations

import json
import re
import subprocess
import time
import random
from collections import Counter
from typing import Optional


# ============================================================
# 底层：goofish-cli 搜索调用
# ============================================================

def _search_goofish(query: str, limit: int = 50) -> list[dict]:
    """调用 goofish search items（浏览器路径，抗风控）"""
    cmd = ["goofish", "search", "items", query, "--limit", str(limit), "--format", "json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if r.returncode != 0:
            return []
        data = json.loads(r.stdout)
        return data.get("items", [])
    except Exception:
        return []


def _search_playwright(query: str, limit: int = 50) -> list[dict]:
    """尝试 Playwright 搜索"""
    try:
        from goofish_cli_ext.commands.playwright_search import search_by_playwright
        return search_by_playwright(query=query, limit=limit)
    except Exception:
        return []


# ============================================================
# 穷举维度定义
# ============================================================

# 关键词后缀：每个后缀对应一个独立的搜索结果池
_KEYWORD_SUFFIXES = [
    "",          # 原词
    "全新", "二手", "自用", "正品", "包邮",
    "闲置", "急出", "降价", "好价", "超值",
    "个人", "学生", "实用",
    "便宜", "低价", "白菜价", "清仓",
    "微瑕", "拆封", "仅拆", "试用",
]

_KEYWORD_PREFIXES = [
    "",          # 无前缀
    "出", "卖",
]

_SORT_MAP = {
    "default": "",
    "price-asc": "price-asc",
    "new": "new",
    "credit": "credit",
}

_CITIES = ["", "上海", "北京", "深圳", "广州", "杭州", "成都"]

_CONDITIONS = ["", "new", "used"]

# 价格暗示词（在关键词中加价格范围，闲鱼搜索会语义理解）
_PRICE_HINTS = [
    "",
    "50以内", "100以内", "200以内",
    "300以内", "500以内",
    "1000以内",
]


def build_keyword_pool(query: str) -> list[str]:
    """
    构建关键词池（穷举所有变体）

    Args:
        query: 原搜索词

    Returns:
        去重后的关键词列表
    """
    pool = []
    q = query.strip()

    # 原词
    pool.append(q)

    # 去空格
    ns = q.replace(" ", "").replace("　", "")
    if ns != q:
        pool.append(ns)

    # 小写
    low = q.lower()
    if low != q and low not in pool:
        pool.append(low)

    # 品牌替换
    brand_map = {
        "南卡": ["NANK"],
        "苹果": ["Apple", "iPhone"],
        "华为": ["Huawei"],
        "小米": ["Xiaomi"],
        "索尼": ["Sony"],
        "三星": ["Samsung"],
    }
    for cn, ens in brand_map.items():
        if cn in q:
            for en in ens:
                alt = q.replace(cn, en)
                if alt not in pool:
                    pool.append(alt)

    # 核心词（取前两个词作为基准）
    words = q.split()
    core = " ".join(words[:2]) if len(words) >= 2 else q

    # 品类词
    for cat in ["耳机", "蓝牙耳机", "数码", "配件"]:
        kw = f"{core} {cat}"
        if kw not in pool:
            pool.append(kw)

    # 后缀扩展（只保留最有价值的品质词，避免引入无关商品）
    quality_suffixes = [
        "全新", "二手", "自用", "闲置", "包邮",
    ]
    for suffix in quality_suffixes:
        kw = f"{core} {suffix}"
        if kw not in pool:
            pool.append(kw)

    # 品牌替换
    for cn, ens in brand_map.items():
        if cn in q:
            for en in ens:
                alt = q.replace(cn, en)
                if alt not in pool:
                    pool.append(alt)

    return pool


def generate_search_tasks(
    query: str,
    max_keywords: int = 20,
    sorts: list[str] | None = None,
    cities: list[str] | None = None,
    conditions: list[str] | None = None,
) -> list[dict]:
    """
    生成穷举搜索任务列表

    Args:
        query: 搜索关键词
        max_keywords: 最多使用多少个关键词变体
        sorts: 排序方式列表 (默认 ["price-asc", "default"])
        cities: 城市列表 (默认 [""] 只全国)
        conditions: 成色条件 (默认 [""] 全部)

    Returns:
        [{"query": "...", "sort": "...", "city": "...", "condition": "..."}, ...]
    """
    sorts = sorts or ["price-asc", "default"]
    cities = cities or [""]
    conditions = conditions or [""]

    keywords = build_keyword_pool(query)[:max_keywords]

    tasks = []
    for kw in keywords:
        for sort in sorts:
            for city in cities:
                for cond in conditions:
                    tasks.append({
                        "query": kw,
                        "sort": sort,
                        "city": city,
                        "condition": cond,
                    })

    # 随机打乱，避免连续同类型请求触发风控
    random.shuffle(tasks)
    return tasks


# ============================================================
# 核心：穷举搜索执行器
# ============================================================

def exhaustive_search(
    query: str,
    limit: int = 50,
    max_keywords: int = 20,
    sorts: list[str] | None = None,
    cities: list[str] | None = None,
    aggressive: bool = False,
) -> dict:
    """
    穷举搜索——用最全策略找到最低价

    Args:
        query: 搜索关键词
        limit: 每个关键词返回条数
        max_keywords: 关键词变体数量 (10=标准, 20=深度, 30=穷举)
        sorts: 排序方式 [默认 price-asc + default]
        cities: 城市列表
        aggressive: 是否启用激进模式（更多关键词+更多排序+城市交叉）

    Returns:
        {"items": [...], "total": N, "stats": {...}, "coverage": {...}}
    """
    if aggressive:
        max_keywords = max(max_keywords, 30)
        sorts = sorts or ["price-asc", "default", "new"]
        cities = cities or _CITIES[:4]
    else:
        sorts = sorts or ["price-asc"]
        cities = cities or [""]

    tasks = generate_search_tasks(
            query=query,
            max_keywords=10 if not aggressive else 20,
            sorts=sorts,
            cities=cities,
        )

    all_items = []
    engines_used = set()
    errors = []
    task_count = len(tasks)
    t0 = time.time()
    time_budget = 55  # 最大执行 55 秒，留 5 秒给后续处理

    for i, task in enumerate(tasks):
        kw = task["query"]
        sort = task["sort"]
        city = task["city"]
        cond = task["condition"]

        # 构建搜索词
        search_query = kw
        if city:
            search_query += f" {city}"
        if cond == "new":
            search_query += " 全新"
        elif cond == "used":
            search_query += " 二手"

        # 间隔请求避免风控（5个一组，组间间隔更长）
        if i > 0:
            if i % 5 == 0:
                time.sleep(random.uniform(1.5, 2.5))
            else:
                time.sleep(random.uniform(0.3, 0.6))

        # 超时控制：总执行时间接近限制时停止
        elapsed = time.time() - t0
        if elapsed > time_budget:
            break

        # 用 goofish-cli 搜索（浏览器路径，抗风控）
        try:
            items = _search_goofish(search_query, limit=min(limit, 50))
            if items:
                for item in items:
                    item["_search_task"] = f"kw:{kw[:15]}|sort:{sort}|city:{city}"
                all_items.extend(items)
                engines_used.add("goofish-cli")
        except Exception as e:
            errors.append(f"[{i}] {kw}: {str(e)[:60]}")

        # 进度提示
        if (i + 1) % 10 == 0 or i == task_count - 1:
            pass  # 搜索中

    # 兜底：如果 goofish-cli 不可用，尝试 Playwright
    if not all_items:
        try:
            pw_items = _search_playwright(query, limit=limit)
            if pw_items:
                all_items.extend(pw_items)
                engines_used.add("playwright")
        except Exception as e:
            errors.append(f"playwright: {str(e)[:60]}")

    # ========== 数据清洗 ==========

    # 去重
    seen_ids = set()
    unique = []
    for item in all_items:
        iid = item.get("item_id", "")
        if iid and iid not in seen_ids:
            seen_ids.add(iid)
            unique.append(item)
    all_items = unique

    # 提取价格
    for item in all_items:
        item["price"] = _extract_price(item)

    # 标题相关性过滤
    # 从搜索词提取核心匹配词（取前 3 个有意义的词，排除通用后缀）
    query_lower = query.lower()
    stop_words = {"全新","二手","自用","闲置","包邮","正品","的","了","是","在","有","和","就","不","人","都","一","一","个","上","也","很","到","说","要","去","你","会","着","没","看","好","自","己"}
    core_terms = set()
    for w in query_lower.split():
        w = w.strip()
        if w and w not in stop_words:
            core_terms.add(w)
    # 补充 ab 连写词的各部分
    if "clipsuper2" in query_lower:
        core_terms.update(["clip", "super2", "clipsuper2"])
    relevant = []
    for item in all_items:
        title = item.get("title", "").lower()
        # 标题包含至少一个核心词就算相关
        if any(term in title for term in core_terms if len(term) >= 2):
            relevant.append(item)
    all_items = relevant if relevant else all_items

    # 过滤虚假低价
    real = [i for i in all_items if not _is_fake_low_price(i)]
    fake_count = len(all_items) - len(real)

    # 按价格排序
    real.sort(key=lambda x: x["price"])

    # 排名
    for idx, item in enumerate(real, 1):
        item["rank"] = idx

    # 品质分组
    groups = _group_items(real)

    # 统计
    prices = [i["price"] for i in real]
    stats = {
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0,
        "avg_price": sum(prices) // len(prices) if prices else 0,
        "total": len(real),
        "removed_fake": fake_count,
        "tasks_attempted": task_count,
    }

    coverage = {
        "tasks_attempted": task_count,
        "tasks_succeeded": task_count - len(errors),
        "unique_items": len(real),
        "engines": list(engines_used) or ["none"],
        "errors": errors[:5],  # 只显示前 5 个错误
    }

    return {
        "items": real[:limit],
        "total": len(real),
        "query": query,
        "stats": stats,
        "recommended": groups,
        "engine": "+".join(sorted(engines_used)) if engines_used else "none",
        "coverage": coverage,
    }


# ============================================================
# 价格提取 & 虚标检测
# ============================================================

def _extract_price(item: dict) -> int:
    ps = item.get("price", "0")
    if isinstance(ps, (int, float)):
        return int(ps)
    ps = ps.replace("¥", "").replace(",", "").strip()
    try:
        return int(float(ps))
    except (ValueError, TypeError):
        return 99999


def _is_fake_low_price(item: dict) -> bool:
    price = _extract_price(item)
    if price <= 5:
        return True
    title = item.get("title", "").lower()
    if any(kw in title for kw in ["定价随机", "标价随机", "看简介定价"]):
        return True
    orig = item.get("original_price", "")
    if orig:
        try:
            o = int(re.sub(r"[^\d]", "", orig))
            if o > 0 and price > 0 and o / price > 10:
                return True
        except: pass
    return False


# ============================================================
# 品质评分 & 分组
# ============================================================

def _quality_score(item: dict, all_prices: list[int] | None = None) -> dict:
    """多维品质评分"""
    r = {"total": 0, "price_advantage": 0, "seller_trust": 0,
         "condition_score": 0, "freshness": 0, "description_score": 0,
         "is_personal_seller": False, "is_steal": False}

    price = item.get("price", 99999)
    title = item.get("title", "")
    badge = item.get("badge", "") or ""
    condition = (item.get("condition") or "").lower()

    # 价格优势 (0-30)
    if all_prices and len(all_prices) >= 3:
        mp = sorted(all_prices)[len(all_prices) // 2]
        if mp > 0 and price > 0:
            ratio = (mp - price) / mp
            if ratio > 0.3:
                r["price_advantage"] = 30
                r["is_steal"] = True
            elif ratio > 0.15: r["price_advantage"] = 25
            elif ratio > 0.05: r["price_advantage"] = 20
            elif ratio > -0.05: r["price_advantage"] = 15
            else: r["price_advantage"] = 5
    else:
        r["price_advantage"] = 20 if price < 100 else (15 if price < 500 else 10)

    # 卖家可信度 (0-25)
    if "百分百好评" in badge: r["seller_trust"] += 15
    elif "信用极好" in badge: r["seller_trust"] += 12
    elif "信用优秀" in badge: r["seller_trust"] += 8
    else: r["seller_trust"] += 3
    r["is_personal_seller"] = _is_personal(item)
    if r["is_personal_seller"]: r["seller_trust"] += 10
    r["seller_trust"] = min(r["seller_trust"], 25)

    # 成色 (0-20)
    if "全新" in condition: r["condition_score"] = 20
    elif "99" in condition: r["condition_score"] = 18
    elif "95" in condition or "几乎" in condition: r["condition_score"] = 15
    elif "9成" in condition: r["condition_score"] = 12
    elif "8成" in condition: r["condition_score"] = 8
    elif "瑕疵" in condition or "磕碰" in condition: r["condition_score"] = 4
    else: r["condition_score"] = 10

    # 新鲜度 (0-10)
    fh = 5
    if any(k in title for k in ["刚买", "刚到", "昨天", "今天"]): fh = 10
    elif any(k in title for k in ["最近", "上个月"]): fh = 8
    elif any(k in title for k in ["买来没", "没用过"]): fh = 7
    elif any(k in title for k in ["用了半年", "用了几个"]): fh = 3
    r["freshness"] = fh

    # 描述 (0-15)
    tl = len(title)
    ds = 15 if tl > 150 else (12 if tl > 100 else (8 if tl > 60 else (5 if tl > 30 else 2)))
    for mk in ["购买", "发票", "配件", "包装", "盒说", "箱说", "正常", "无修", "无拆", "功能", "成色", "实拍"]:
        if mk in title: ds += 2; break
    r["description_score"] = min(ds, 15)

    r["total"] = r["price_advantage"] + r["seller_trust"] + r["condition_score"] + r["freshness"] + r["description_score"]
    return r


def _is_personal(item: dict) -> bool:
    title = item.get("title", "")
    tl = title.lower()
    ps = sum(1 for s in ["搬家","老婆","老公","朋友送","年会","奖品","中奖","用不上","换了","升级了","闲置","买多了","吃灰","断舍离","买来没用"] if s in title)
    ms = sum(1 for s in ["正品保障","假一赔十","支持验货","全国联保","七天无理由","厂家直销"] if s in tl)
    if ms >= 2: return False
    if ps >= 1: return True
    if len(title) > 200: return False
    return True


def _group_items(items: list[dict]) -> dict:
    prices = [i["price"] for i in items]
    if not prices:
        return {"steals": [], "best": [], "personal_deals": [], "cheapest": []}
    mp = sorted(prices)[len(prices) // 2]

    steals, best, personal, cheap = [], [], [], []
    for item in items:
        p = item["price"]
        sd = _quality_score(item, prices)
        ts = sd["total"]
        item["_score"] = ts
        item["_score_detail"] = sd
        if sd["is_steal"]: steals.append(item)
        elif ts >= 60 and p <= mp: best.append(item)
        elif sd["is_personal_seller"] and p <= mp: personal.append(item)
        elif p <= mp * 0.7: cheap.append(item)

    for g in [steals, best, personal, cheap]:
        g.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return {"steals": steals[:8], "best": best[:8], "personal_deals": personal[:5], "cheapest": cheap[:5]}


# ============================================================
# 兼容原有 search_items_cli 接口
# ============================================================

def search_items_cli(
    query: str,
    limit: int = 50,
    min_price: int | None = None,
    max_price: int | None = None,
    sort_by_price: bool = True,
    deep_search: bool = True,
    sort: str = "price-asc",
    condition: str = "",
    location: str = "",
    aggressive: bool = False,
) -> dict:
    """
    闲鱼终极低价搜索

    自动在后台穷举所有搜索策略组合，返回最全面的低价结果。
    """
    result = exhaustive_search(
        query=query,
        limit=limit * 2,  # 内部多搜一些，方便后续筛选
        max_keywords=25 if deep_search else 5,
        sorts=[sort] if not aggressive else ["price-asc", "default", "new"],
        cities=[location] if location else [""],
        aggressive=aggressive,
    )

    # 价格筛选
    items = result["items"]
    if min_price is not None:
        items = [i for i in items if i["price"] >= min_price]
    if max_price is not None:
        items = [i for i in items if i["price"] <= max_price]

    result["items"] = items[:limit]
    result["total"] = len(items)

    # 统计
    prices = [i["price"] for i in items]
    result["stats"] = {
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0,
        "avg_price": sum(prices) // len(prices) if prices else 0,
        "total": len(items),
    }

    return result
