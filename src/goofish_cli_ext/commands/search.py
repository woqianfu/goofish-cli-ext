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

    # 标题暗示价格不实（缩窄范围，避免误杀正常商品）
    fake_keywords = [
        "定价随机", "标价随机", "看简介定价",
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

def _quality_score(item: dict, all_prices: Optional[list[int]] = None) -> dict:
    """
    多维品质评分（返回评分解构）
    
    从多个维度综合评价一个商品是否「质优价廉」：
    - 价格优势度：相对同类商品的价格便宜程度（0-30分）
    - 卖家可信度：信用、个人/职业判断（0-25分）
    - 商品成色：全新到有瑕疵（0-20分）
    - 上架新鲜度：刚发布 vs 挂了很久（0-10分）
    - 描述详尽度：标题长度、真实性（0-15分）
    
    Returns:
        {"total": N, "price_advantage": N, "seller_trust": N,
         "condition_score": N, "freshness": N, "description_score": N,
         "is_personal_seller": bool, "is_steal": bool}
    """
    result = {
        "total": 0.0,
        "price_advantage": 0,
        "seller_trust": 0,
        "condition_score": 0,
        "freshness": 0,
        "description_score": 0,
        "is_personal_seller": False,
        "is_steal": False,
    }
    
    price = item.get("price", 99999)
    title = item.get("title", "")
    badge = item.get("badge", "") or ""
    condition = (item.get("condition") or "").lower()
    
    # ========== 1. 价格优势度 (0-30分) ==========
    if all_prices and len(all_prices) >= 3:
        sorted_prices = sorted(all_prices)
        median_price = sorted_prices[len(sorted_prices) // 2]
        if median_price > 0 and price > 0:
            ratio = (median_price - price) / median_price
            # 比中位数便宜越多分越高
            if ratio > 0.3:
                result["price_advantage"] = 30  # 便宜30%以上 = 捡漏级
                result["is_steal"] = True
            elif ratio > 0.15:
                result["price_advantage"] = 25
            elif ratio > 0.05:
                result["price_advantage"] = 20
            elif ratio > -0.05:
                result["price_advantage"] = 15  # 接近中位数
            else:
                result["price_advantage"] = 5   # 比中位数还贵
        else:
            result["price_advantage"] = 10
    else:
        # 没有参考价格时，低价本身就有优势
        if price < 100:
            result["price_advantage"] = 20
        elif price < 500:
            result["price_advantage"] = 15
        else:
            result["price_advantage"] = 10
    
    # ========== 2. 卖家可信度 (0-25分) ==========
    if "百分百好评" in badge:
        result["seller_trust"] += 15
    elif "信用极好" in badge:
        result["seller_trust"] += 12
    elif "信用优秀" in badge:
        result["seller_trust"] += 8
    elif "信用良好" in badge:
        result["seller_trust"] += 5
    else:
        result["seller_trust"] += 3  # 无标签依然有基础分
    
    # 个人卖家识别
    is_personal = _is_personal_seller(item)
    result["is_personal_seller"] = is_personal
    if is_personal:
        result["seller_trust"] += 10  # 个人卖家信用奖励
    else:
        # 疑似商家不扣分，只是不加奖励分
        pass
    
    result["seller_trust"] = min(result["seller_trust"], 25)
    
    # ========== 3. 商品成色 (0-20分) ==========
    if "全新" in condition:
        result["condition_score"] = 20
    elif "99新" in condition or "99" in condition:
        result["condition_score"] = 18
    elif "95新" in condition or "几乎全新" in condition or "几乎" in condition:
        result["condition_score"] = 15
    elif "9成" in condition:
        result["condition_score"] = 12
    elif "8成" in condition:
        result["condition_score"] = 8
    elif "瑕疵" in condition or "磕碰" in condition or "划痕" in condition:
        result["condition_score"] = 4
    else:
        result["condition_score"] = 10  # 未知成色给中间分
    
    # ========== 4. 上架新鲜度 (0-10分) ==========
    # 通过标题中的时间线索判断
    title_lower = title.lower()
    freshness = 5  # 默认中等
    if any(kw in title for kw in ["刚买", "刚到", "全新刚", "昨天", "今天", "刚刚"]):
        freshness = 10
    elif any(kw in title for kw in ["最近", "上个月", "月初"]):
        freshness = 8
    elif any(kw in title for kw in ["买来用了没", "买来没", "没用过"]):
        freshness = 7
    elif any(kw in title for kw in ["买来用了", "用了几个月", "用了半年"]):
        freshness = 3
    result["freshness"] = freshness
    
    # ========== 5. 描述详尽度 (0-15分) ==========
    desc_score = 0
    title_len = len(title)
    if title_len > 150:
        desc_score = 15
    elif title_len > 100:
        desc_score = 12
    elif title_len > 60:
        desc_score = 8
    elif title_len > 30:
        desc_score = 5
    else:
        desc_score = 2
    
    # 标题包含真实描述信息加分
    detail_markers = ["购买", "发票", "配件", "包装", "盒说", "箱说",
                     "正常", "无修", "无拆", "功能", "测试",
                     "成色", "如图", "实拍", "实物"]
    for marker in detail_markers:
        if marker in title:
            desc_score += 2
            break
    result["description_score"] = min(desc_score, 15)
    
    result["total"] = (result["price_advantage"] + result["seller_trust"] +
                      result["condition_score"] + result["freshness"] +
                      result["description_score"])
    
    return result


def _is_personal_seller(item: dict) -> bool:
    """
    判断是否为真实个人卖家（非职业商家）
    
    个人卖家的特征：
    - 标题含有人情味用语："搬家出"、"老婆不让"、"朋友送的"、"年会奖品"
    - 有个人故事感，不是干巴巴的商品参数列表
    - 定价是整数（不像职业卖家定 99.9、199）
    - 没有"正品保障、假一赔十、支持验货"等商家话术
    - 标题简短不堆砌（职业卖家堆关键词）
    """
    title = item.get("title", "")
    title_lower = title.lower()
    
    # 个人卖家正面信号
    personal_signals = [
        "搬家", "老婆", "老公", "朋友送", "年会", "奖品",
        "中奖", "用不上", "换了", "升级了", "闲置",
        "买多了", "不适合", "冲动消费", "回血",
        "女朋友", "男友", "家里", "放着", "吃灰",
        "断舍离", "清仓", "不用了", "买来没用",
    ]
    
    # 职业卖家信号
    merchant_signals = [
        "正品保障", "假一赔十", "支持验货", "专柜",
        "官方正品", "全国联保", "七天无理由",
        "粉丝福利", "特价清仓", "限量",
        "专业代购", "实体店", "厂家直销",
    ]
    
    personal_count = sum(1 for s in personal_signals if s in title)
    merchant_count = sum(1 for s in merchant_signals if s in title_lower)
    
    # 综合判断
    if merchant_count >= 2:
        return False  # 职业卖家
    if personal_count >= 1:
        return True   # 个人卖家
    
    # 标题长度判断：太长的多半是职业卖家堆关键词
    if len(title) > 200:
        return False
    
    # 默认不确定时，倾向于认为是个人卖家
    return True


# ============================================================
# 智能分群
# ============================================================

def _group_items(items: list[dict]) -> dict:
    """
    将商品按品质分组（基于新评分体系）

    返回:
    {
        "steals": [...],       # ⭐ 捡漏推荐 — 价格低于中位数30%+
        "best": [...],         # 🏆 质优价廉 — 综合评分高 + 价格低于中位数
        "personal_deals": [...], # 👤 个人卖家好价
        "cheapest": [...],     # 💰 纯低价 — 不管成色
    }
    """
    prices = [i["price"] for i in items]
    if not prices:
        return {"steals": [], "best": [], "personal_deals": [], "cheapest": []}

    median_price = sorted(prices)[len(prices) // 2]

    steals = []
    best = []
    personal_deals = []
    cheapest = []

    for item in items:
        price = item["price"]
        score_data = _quality_score(item, all_prices=prices)
        total_score = score_data["total"]

        # 捡漏：价格低于中位数30%+
        if score_data["is_steal"]:
            item["_score"] = total_score
            item["_score_detail"] = score_data
            steals.append(item)
            continue

        # 质优价廉：综合评分 >= 60 且价格 <= 中位数
        if total_score >= 60 and price <= median_price:
            item["_score"] = total_score
            item["_score_detail"] = score_data
            best.append(item)
            continue

        # 个人卖家好价：个人卖家且价格 <= 中位数
        if score_data["is_personal_seller"] and price <= median_price:
            item["_score"] = total_score
            item["_score_detail"] = score_data
            personal_deals.append(item)
            continue

        # 纯低价：同价格最低的那批
        if price <= median_price * 0.7:
            item["_score"] = total_score
            item["_score_detail"] = score_data
            cheapest.append(item)
            continue

    # 每个组内按综合评分排序
    for group in [steals, best, personal_deals, cheapest]:
        group.sort(key=lambda x: x.get("_score", 0), reverse=True)

    return {
        "steals": steals[:8],
        "best": best[:8],
        "personal_deals": personal_deals[:5],
        "cheapest": cheapest[:5],
    }


# ============================================================
# 多关键词扩展
# ============================================================

def _expand_keywords(query: str) -> list[str]:
    """
    长尾关键词扩展引擎
    
    闲鱼对每个搜索词独立返回前 ~250 条结果。
    通过生成长尾关键词列表，可以突破单关键词的结果限制。
    
    例如 "南卡 Clip Super2" 会扩展为 15+ 个关键词：
    - 原词变体：南卡 Clip Super2, 南卡ClipSuper2, NANK Clip Super2
    - 品质后缀：+ 全新, + 二手, + 自用, + 正品, + 包邮, + 实用
    - 情感后缀：+ 闲置, + 急出, + 搬家出, + 断舍离, + 降价
    - 品类词：南卡 耳机, 南卡 蓝牙, NANK 耳夹
    """
    keywords = [query]
    q = query.strip()

    # 1. 变体
    no_space = q.replace(" ", "").replace("　", "")
    if no_space != q and no_space not in keywords:
        keywords.append(no_space)
    lower = q.lower()
    if lower != q and lower not in keywords:
        keywords.append(lower)

    # 2. 品牌替换（可扩展的品牌映射表）
    brand_map = {
        "南卡": ["NANK", "南卡"],
        "苹果": ["Apple", "苹果", "iphone"],
        "华为": ["Huawei", "华为"],
        "小米": ["Xiaomi", "小米"],
        "索尼": ["Sony", "索尼"],
        "三星": ["Samsung", "三星"],
    }
    for cn, en_list in brand_map.items():
        if cn in q:
            for en in en_list:
                if en != cn:
                    alt = q.replace(cn, en)
                    if alt not in keywords:
                        keywords.append(alt)

    # 3. 品质后缀（最重要的扩展！每个后缀对应不同的搜索意图，覆盖不同商品池）
    suffixes = [
        "全新", "二手", "自用", "正品",
        "包邮", "实用", "便宜",
        "闲置", "急出", "降价",
        "正品", "好价", "超值",
    ]
    for suffix in suffixes:
        kw = f"{q} {suffix}"
        if kw not in keywords:
            keywords.append(kw)

    # 4. 品类词（提取核心名词+品类）
    core_words = q.split()
    if len(core_words) >= 2:
        # 取前两个核心词 + 常见品类后缀
        core = " ".join(core_words[:2])
        for cat in ["耳机", "数码", "配件", "蓝牙"]:
            cat_kw = f"{core} {cat}"
            if cat_kw not in keywords:
                keywords.append(cat_kw)

    return keywords[:25]  # 最多 25 个关键词（足够覆盖 250x25 = 6250 条原始数据）


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

    # 试 Playwright 引擎（首选）
    playwright_ok = False
    playwright_error = ""
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
                for item in playwright_items:
                    item["_source"] = "playwright"
                all_items.extend(playwright_items)
                playwright_ok = True
        except Exception as e:
            playwright_error = str(e)[:100]

    # goofish-cli 引擎补充（深度搜索或 Playwright 失败时）
    goofish_items = []
    goofish_error = ""
    need_goofish = not playwright_ok or deep_search
    if need_goofish:
        try:
            if deep_search:
                keywords = _expand_keywords(query)
                for kw in keywords[:10]:  # 取前 10 个关键词 = 覆盖 10x 结果
                    try:
                        items = _call_goofish(kw, limit=min(limit, 50))
                        goofish_items.extend(items)
                    except Exception as e:
                        goofish_error += f"[{kw}:{str(e)[:50]}]"
                        continue
            else:
                goofish_items = _call_goofish(query, limit=min(limit, 50))
        except Exception as e:
            goofish_error = str(e)[:100]

    all_items.extend(goofish_items)

    # engine 标签：准确反映数据来源
    pw_count = sum(1 for x in all_items if x.get("_source") == "playwright")
    goo_count = len(all_items) - pw_count
    if pw_count > 0 and goo_count > 0:
        engine = "playwright+goofish-cli"
    elif pw_count > 0:
        engine = "playwright"
    else:
        engine = "goofish-cli"

    # 记录错误信息供返回
    errors = []
    if playwright_error:
        errors.append(f"Playwright引擎: {playwright_error}")
    if goofish_error:
        errors.append(f"goofish-cli引擎: {goofish_error}")
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

    # 品质分组（此时价格已经是 int，确保安全）
    groups = _group_items([dict(i) for i in filtered])  # 深拷贝避免副作用

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
