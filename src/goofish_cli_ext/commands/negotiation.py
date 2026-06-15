# -*- coding: utf-8 -*-
"""
议价话术模板 — 买家砍价时的应对话术库
"""

from __future__ import annotations

# ============================================================
# 议价场景分类
# ============================================================

NEGOTIATION_SCRIPTS = {
    "小刀": {
        "description": "买家小刀（砍价10%以内）",
        "price_range": "0~10%",
        "strategies": [
            "爽快同意",
            "送小配件",
            "下次优先",
        ],
        "templates": [
            # 爽快同意
            {
                "title": "爽快成交",
                "text": "好的老板，¥{price}就¥{price}吧，爽快人交个朋友。链接直接拍，今天发。",
            },
            {
                "title": "送小配件",
                "text": "¥{price}确实最低了老板，不过我送你个{accessory}，也算是心意了。",
            },
            {
                "title": "下次优惠",
                "text": "行吧，¥{price}给你了。下次还有好东西优先给你看。",
            },
        ],
    },
    "大刀": {
        "description": "买家大刀（砍价20-30%）",
        "price_range": "10~30%",
        "strategies": [
            "坚持底价",
            "对比行情",
            "强调品质",
        ],
        "templates": [
            # 坚持底价
            {
                "title": "坚持底价",
                "text": "不好意思老板，¥{price}真的是最低了。你可以去搜一下同款，我这个成色这个价格绝对是最实惠的。",
            },
            # 对比行情
            {
                "title": "对比行情",
                "text": "老板你可以去闲鱼搜一下同款，我这个价已经是最低的了。同成色的都挂¥{market_price}以上呢。",
            },
            # 强调品质
            {
                "title": "强调品质",
                "text": "这个价确实没法再低了老板。我这个是{condition}，配件齐全，买了绝对不亏。",
            },
        ],
    },
    "屠龙刀": {
        "description": "买家屠龙刀（砍价50%以上）",
        "price_range": "30~50%+",
        "strategies": [
            "礼貌拒绝",
            "推荐低价替代",
            "冷处理",
        ],
        "templates": [
            # 礼貌拒绝
            {
                "title": "礼貌拒绝",
                "text": "感谢关注，但这个价确实出不了哈。你可以看看别的卖家，祝早日买到合适的。",
            },
            # 推荐替代
            {
                "title": "推荐替代",
                "text": "¥{counter_offer}的话我可以考虑，¥{low_price}确实不行。要不你看看我主页其他便宜点的？",
            },
            # 冷处理
            {
                "title": "冷处理",
                "text": "你先看看吧，有需要再联系。",
            },
        ],
    },
    "打包": {
        "description": "买家要多件打包",
        "price_range": "多件折扣",
        "strategies": [
            "给打包价",
            "送配件",
            "包邮优惠",
        ],
        "templates": [
            {
                "title": "打包优惠",
                "text": "两件一起的话，给你便宜¥{discount}，再包个邮。单买确实没法少。",
            },
            {
                "title": "送配件",
                "text": "两件一起的话这个价可以，我再送你个{accessory}。",
            },
        ],
    },
    "面交": {
        "description": "买家要求当面交易",
        "price_range": "面交议价",
        "strategies": [
            "同意面交",
            "强调当面验货",
            "安全提醒",
        ],
        "templates": [
            {
                "title": "同意面交",
                "text": "可以面交，{location}地铁站附近都行。当面验货，没问题再付。",
            },
            {
                "title": "安全提醒",
                "text": "可以面交，到人多的地方，最好带朋友一起来。东西我带着，你看满意了再拿。",
            },
        ],
    },
    "质量问题": {
        "description": "买家质疑质量/成色",
        "strategies": [
            "提供证据",
            "强调质保",
            "接受验货",
        ],
        "templates": [
            {
                "title": "提供证据",
                "text": "我可以给你拍视频，各个角度都拍给你看。保证和我描述的一样。",
            },
            {
                "title": "强调质保",
                "text": "你放心，功能全部正常，我测试过的。如果有问题你找我。",
            },
            {
                "title": "接受验货",
                "text": "你可以找人鉴定，或者当面验货。假一赔十。",
            },
        ],
    },
    "已售": {
        "description": "商品已卖出",
        "strategies": [
            "婉拒",
            "推荐其他",
        ],
        "templates": [
            {
                "title": "已经出了",
                "text": "不好意思，刚出掉了。",
            },
            {
                "title": "推荐其他",
                "text": "这个刚出掉了，不过主页还有个类似的，你可以看看。",
            },
        ],
    },
}


# ============================================================
# 议价模板获取
# ============================================================

def get_negotiation_script(
    scenario: str = "",
    price: int = 0,
    condition: str = "",
    market_price: int = 0,
    counter_offer: int = 0,
    low_price: int = 0,
    discount: int = 0,
    accessory: str = "小配件",
    location: str = "",
) -> dict:
    """获取议价话术模板

    Args:
        scenario: 场景 (小刀/大刀/屠龙刀/打包/面交/质量问题/已售)
        price: 你的标价
        condition: 商品成色
        market_price: 市场均价
        counter_offer: 你能接受的价格
        low_price: 买家出价
        discount: 打包折扣
        accessory: 附送配件
        location: 面交地点

    Returns:
        {"scenario": "...", "description": "...", "templates": [...]}
    """
    # 如果没指定场景，列出所有
    if not scenario:
        categories = list(NEGOTIATION_SCRIPTS.keys())
        return {
            "scenario": "all",
            "description": "所有议价场景",
            "templates": [],
            "available_scenarios": [
                {"key": k, "name": v["description"], "strategies": v["strategies"]}
                for k, v in NEGOTIATION_SCRIPTS.items()
            ],
        }

    script = NEGOTIATION_SCRIPTS.get(scenario)
    if not script:
        return {"error": f"未知场景: {scenario}，可选: {', '.join(NEGOTIATION_SCRIPTS.keys())}"}

    # 填充模板
    filled_templates = []
    for t in script["templates"]:
        text = t["text"].format(
            price=price,
            condition=condition,
            market_price=market_price,
            counter_offer=counter_offer,
            low_price=low_price,
            discount=discount,
            accessory=accessory,
            location=location,
        )
        filled_templates.append({
            "title": t["title"],
            "text": text,
        })

    return {
        "scenario": scenario,
        "description": script["description"],
        "strategies": script["strategies"],
        "templates": filled_templates,
    }


# ============================================================
# 定价不合理的 AI 分析
# ============================================================

def analyze_price_reason(
    buyer_message: str,
) -> dict:
    """分析买家的砍价消息，识别砍价类型

    基于关键词简单判断：
    - "便宜点/少点/优惠" → 小刀
    - "太贵了/贵了/不值" → 大刀
    - "xx出不出/xx卖不卖" → 屠龙刀
    - "两个/一起/打包" → 打包
    - "面交/自提" → 面交
    - "瑕疵/问题/坏了" → 质量问题
    """
    msg = buyer_message.lower()

    if any(kw in msg for kw in ["面交", "自提", "当面"]):
        return {"scenario": "面交", "confidence": "high"}
    if any(kw in msg for kw in ["两个", "一起", "都", "打包"]):
        return {"scenario": "打包", "confidence": "medium"}
    if any(kw in msg for kw in ["瑕疵", "问题", "坏了", "修过"]):
        return {"scenario": "质量问题", "confidence": "high"}
    if any(kw in msg for kw in ["一半", "五折", "对折", "白送"]):
        return {"scenario": "屠龙刀", "confidence": "high"}
    if any(kw in msg for kw in ["太贵", "贵了", "不值"]):
        return {"scenario": "大刀", "confidence": "medium"}
    if any(kw in msg for kw in ["便宜", "少点", "优惠", "好价"]):
        return {"scenario": "小刀", "confidence": "medium"}

    return {"scenario": "小刀", "confidence": "low"}


def smart_negotiate(
    buyer_message: str,
    our_price: int = 0,
    product_name: str = "",
    condition: str = "",
) -> dict:
    """
    智能议价回复生成

    输入买家说的内容 + 你的商品信息，返回最优回复话术。

    Args:
        buyer_message: 买家说了什么
        our_price: 你的标价
        product_name: 商品名称
        condition: 成色

    Returns:
        {
            "smart_reply": True,
            "buyer_message": "...",
            "scenario": "...",
            "description": "...",
            "confidence": "...",
            "templates": [{"title": "...", "text": "..."}, ...],
        }
    """
    # 先分析买家意图
    analysis = analyze_price_reason(buyer_message)
    scenario = analysis["scenario"]

    # 根据买家消息的详细程度生成定制回复
    msg = buyer_message.lower()
    templates = []

    if scenario == "小刀":
        templates.append({
            "title": "爽快成交",
            "text": f"好的，{product_name} {our_price}就{our_price}吧，爽快人交个朋友。链接直接拍，今天发。",
        })
        templates.append({
            "title": "送小配件",
            "text": f"老板，{our_price}确实最低了，不过我送你个原装配件/收纳袋，也算是心意了。",
        })
        templates.append({
            "title": "强调性价比",
            "text": f"这个价真的很划算了。你可以去搜一下同款，我这个{condition}这个价格绝对是最低的之一。",
        })

    elif scenario == "大刀":
        # 买家说贵了，用具体数据反驳
        templates.append({
            "title": "对比行情",
            "text": f"你可以去闲鱼搜一下同款，我这个价已经最低了。同成色的都挂{int(our_price * 1.15)}以上。",
        })
        templates.append({
            "title": "强调品质",
            "text": f"这个价确实没法再低了。{product_name}是{condition}，配件齐全，现货实拍，买了绝对值。",
        })
        templates.append({
            "title": "适当让步",
            "text": f"最多给你便宜{int(our_price * 0.05)}块，再低真的出不了了。",
        })

    elif scenario == "屠龙刀":
        templates.append({
            "title": "礼貌拒绝",
            "text": f"感谢关注，但{our_price}这个价确实出不了哈。你可以看看别的卖家，祝早日买到合适的。",
        })
        counter = max(int(our_price * 0.7), our_price - 50)
        templates.append({
            "title": "还个价",
            "text": f"{our_price}确实不行，{counter}的话我可以考虑，你看看能不能加点。",
        })
        templates.append({
            "title": "冷处理",
            "text": f"你先看看吧，有需要再联系。",
        })

    elif scenario == "面交":
        templates.append({
            "title": "同意面交",
            "text": f"可以面交，地铁站附近都行。当面验货，没问题再付。我给你留到周末。",
        })
        templates.append({
            "title": "安全提醒",
            "text": f"可以面交，到人多的地方最好。东西我带着，你看满意了再拿。支持验货。",
        })

    elif scenario == "打包":
        discount = int(our_price * 0.15)
        templates.append({
            "title": "打包优惠",
            "text": f"两件一起的话，给你便宜{discount}块，再包个邮。单买确实没法少。",
        })

    elif scenario == "质量问题":
        templates.append({
            "title": "提供证据",
            "text": f"我可以给你拍视频，各个角度都拍给你看。保证和我描述的一样，实物实拍。",
        })
        templates.append({
            "title": "接受验货",
            "text": f"你可以找人鉴定，或者当面验货。假一赔十。",
        })

    else:
        # 兜底：判断不出来的时候给通用回复
        templates.append({
            "title": "通用回复",
            "text": f"你好，{product_name} {our_price}，{condition}，实物实拍。感兴趣可以拍，爽快包邮。",
        })

    description_map = {
        "小刀": "买家想小刀砍价（10%以内）",
        "大刀": "买家觉得贵了，大刀砍价（10-30%）",
        "屠龙刀": "买家出了远低于预期的价格",
        "面交": "买家希望当面交易",
        "打包": "买家想要多件打包",
        "质量问题": "买家对商品质量有疑虑",
    }

    return {
        "smart_reply": True,
        "buyer_message": buyer_message,
        "scenario": scenario,
        "description": description_map.get(scenario, "买家来询价"),
        "confidence": analysis["confidence"],
        "templates": templates,
    }


# ============================================================


# ============================================================
# CLI 格式化输出
# ============================================================

def format_negotiation(scenario_data: dict) -> str:
    """格式化议价模板为可读文本"""
    if "error" in scenario_data:
        return f"❌ {scenario_data['error']}"

    if "available_scenarios" in scenario_data:
        lines = ["📋 可用议价场景："]
        for s in scenario_data["available_scenarios"]:
            strategies = "、".join(s["strategies"])
            lines.append(f"  {s['key']:6s} — {s['name']}  [{strategies}]")
        return "\n".join(lines)

    if "smart_reply" in scenario_data:
        # 智能回复模式
        lines = [
            f"💬 买家说: \"{scenario_data.get('buyer_message', '')}\"",
            f"📊 分析: {scenario_data['description']} (置信度: {scenario_data.get('confidence', '中')})",
            "",
        ]
        for t in scenario_data["templates"]:
            lines.append(f"[{t['title']}]")
            lines.append(f"  {t['text']}")
            lines.append("")
        return "\n".join(lines)

    lines = [
        f"📝 {scenario_data['description']}",
        f"策略: {' → '.join(scenario_data['strategies'])}",
        "",
    ]
    for t in scenario_data["templates"]:
        lines.append(f"[{t['title']}]")
        lines.append(f"  {t['text']}")
        lines.append("")

    return "\n".join(lines)
