# -*- coding: utf-8 -*-
"""
闲鱼文案生成器
基于 xianyu-copywriter 模板体系（MIT 协议），支持：
- 实物商品文案（二手数码等）
- 虚拟商品文案（教程/软件）
- 文案优化

参考: https://github.com/Jichi666/xianyu-copywriter
"""

from __future__ import annotations

import datetime
from typing import Optional


# ============================================================
# 实物商品文案模板 (Physical)
# ============================================================

PHYSICAL_TEMPLATE = """\
【{condition}】{name} {highlights}

📦【产品详情】
- 品牌/型号：{name}
- 成色状态：{condition}
{extra_detail}

💡【出闲置原因】
闲置数码产品，买来{usage_period}，一直放着吃灰，出给有缘人。

✅【交易保障】
- 正品保证，支持验货
- 实物拍摄，所见即所得
- {shipping}（偏远地区除外）
- 到货请当面验货，确认无误后签收
- 签收后不支持退货

⚠️【购买须知】
- 本商品为二手闲置，非全新商品
- 二手商品售出后不支持退换货
- 请仔细查看商品图片和描述
- 谨防到手刀、恶意退货
- 完美主义者请绕道

🏷️关键词：{keywords}
"""

VIRTUAL_TEMPLATE = """\
【{name}】划重点！！——
{virtual_warnings}

——【{name}购买须知】——
有一定上手门槛，无法退款买之前考虑好。
{tech_notes}

一. **本品为{product_type}，{delivery_method}。虚拟产品具有可复制性【不支持退款】【有版权禁止二传二改二次盈利倒卖盗卖】请仔细阅读以下详情再决定下单，购买默认您已知悉并同意注意事项！！**

{features_section}

【版权注意】！！！
- {name}受版权保护，严禁对本产品进行反编译、修改、二次开发或上传至公共平台
- 严禁使用本产品进行二次盈利
- 严禁在未授权情况下传播或分享本产品，否则将会依法追究法律责任
- 再次强调**虚拟商品具有可复制性无法退款**，下单默认您已阅读商品详情并知悉以上注意内容！介意勿拍。

🏷️关键词：{keywords}
"""


# ============================================================
# 实物商品文案生成
# ============================================================

def copy_physical(
    name: str,
    condition: str = "95新",
    price: int = 0,
    features: Optional[list[str]] = None,
    location: str = "",
    usage_period: str = "用了没多久",
    extra_detail: str = "",
) -> dict:
    """生成实物商品（二手数码/闲置）的闲鱼文案

    Args:
        name: 商品名称
        condition: 成色 (如 95新, 9成新, 全新未拆封)
        price: 价格
        features: 核心卖点列表
        location: 发货地
        usage_period: 使用时长描述
        extra_detail: 额外描述（可包含使用状况、配件等）

    Returns:
        {"copy": "...", "keywords": [...]}
    """
    features = features or []
    highlights = " · ".join(features[:4]) if features else "正品保障"
    if price:
        highlights += f" · ¥{price}"

    # 从 features 和 name 生成关键词
    keywords = _generate_keywords(name, features, is_physical=True)

    # 配送方式
    shipping = "包邮" if location else "快递包邮"
    if location:
        shipping += f"（{location}发）"

    # 补充详情
    if not extra_detail:
        extra_detail_parts = [f"- 配件齐全（原装）"]
        if features:
            extra_detail_parts.append(f"- 核心卖点：{'、'.join(features[:5])}")
        extra_detail = "\n".join(extra_detail_parts)

    copy = PHYSICAL_TEMPLATE.format(
        condition=condition,
        name=name,
        highlights=highlights,
        extra_detail=extra_detail,
        usage_period=usage_period,
        shipping=shipping,
        price=price,
        keywords=" ".join(keywords),
    )

    return {"copy": copy.strip(), "keywords": keywords}


# ============================================================
# 虚拟商品文案生成
# ============================================================

def copy_virtual(
    name: str,
    price: int = 0,
    features: Optional[list[str]] = None,
    tech_req: str = "",
    product_type: str = "数字产品",
    delivery_method: str = "百度网盘链接发货，请保存到自己的网盘后下载使用",
) -> dict:
    """生成虚拟商品（教程/软件/模板）的闲鱼文案

    Args:
        name: 产品名称
        price: 价格
        features: 产品特点列表
        tech_req: 技术要求
        product_type: 产品类型描述
        delivery_method: 交付方式

    Returns:
        {"copy": "...", "keywords": [...]}
    """
    features = features or []

    # 警告部分
    warnings = []
    if tech_req:
        warnings.append(f"- 对{tech_req}不熟悉请勿购买")
    else:
        warnings.append("- 对电脑和网络操作不熟悉请勿购买")
    warnings.append("- 虚拟商品具有可复制性，购买后无法退款")
    virtual_warnings = "\n".join(warnings)

    # 技术说明
    tech_notes = tech_req if tech_req else "请自备必要的软件/硬件环境，建议具备一定的电脑操作能力。"

    # 产品介绍
    features_section = ""
    if features:
        feature_items = "\n".join(
            f"{i}. {feat}" for i, feat in enumerate(features, 1)
        )
        features_section = f"**产品特点：**\n{feature_items}"

    # 关键词
    keywords = _generate_keywords(name, features, is_physical=False)

    copy = VIRTUAL_TEMPLATE.format(
        name=name,
        price=price,
        virtual_warnings=virtual_warnings,
        tech_notes=tech_notes,
        product_type=product_type,
        delivery_method=delivery_method,
        features_section=features_section,
        keywords=" ".join(keywords),
    )

    return {"copy": copy.strip(), "keywords": keywords}


# ============================================================
# 文案优化
# ============================================================

def copy_optimize(text: str, is_virtual: bool = False) -> dict:
    """优化现有闲鱼文案

    检查：
    1. 是否有明确的风险提示
    2. 虚拟商品是否有"无法退款"声明
    3. 排版是否清晰（使用 emoji 分段）
    4. 是否有关键词标签

    Args:
        text: 现有文案
        is_virtual: 是否为虚拟商品

    Returns:
        {"optimized": "...", "suggestions": [...]}
    """
    suggestions = []

    # 检查缺失的模块
    if "⚠️" not in text and "❗" not in text:
        suggestions.append("缺少风险提示标记，建议使用 ⚠️ emoji 突出警告信息")

    if is_virtual:
        if "无法退款" not in text:
            suggestions.append("虚拟商品必须包含「无法退款」声明")
        if "版权" not in text:
            suggestions.append("缺少版权声明，虚拟商品建议添加版权保护声明")
        if "二传" not in text or "二改" not in text:
            suggestions.append("建议添加禁止二传二改的版权条款")

    if "📦" not in text and "📝" not in text:
        suggestions.append("建议使用 emoji 分段（📦📝✅⚠️）提升可读性")

    if "关键词" not in text.lower() and "🏷️" not in text:
        suggestions.append("缺少关键词标签，建议底部添加搜索关键词")

    # 优化文本
    optimized = text.strip()

    # 如果没有关键词，尝试从文本提取
    if "🏷️" not in optimized:
        words = text.split()
        # 简单提取：前几个有意义的词
        key_terms = [w for w in words if len(w) > 1 and w not in "的了吗我是你在有和"]
        if key_terms:
            keywords_str = " ".join(key_terms[:10])
            optimized += f"\n\n🏷️关键词：{keywords_str}"

    return {"optimized": optimized.strip(), "suggestions": suggestions}


# ============================================================
# 关键词生成
# ============================================================

# 常见数码品牌词
_BRAND_KEYWORDS = {
    "苹果": "iPhone iPad MacBook Apple Watch AirPods 苹果 二手 闲置 正品",
    "华为": "华为 荣耀 Mate P系列 鸿蒙 二手 闲置",
    "小米": "小米 红米 Xiaomi 米家 二手 闲置",
    "三星": "Samsung 三星 Galaxy Note S系列 二手",
    "索尼": "Sony 索尼 WH WF Walkman 二手 闲置",
    "bose": "Bose QC 降噪 蓝牙耳机 音响 二手",
    "airpods": "AirPods Pro 苹果耳机 降噪 真无线 蓝牙耳机 二手 闲置",
    "南卡": "NANK 南卡 骨传导 开放式 蓝牙耳机 运动 耳机 二手",
}


def _generate_keywords(name: str, features: Optional[list[str]] = None, is_physical: bool = True) -> list[str]:
    """根据商品名和特点生成关键词"""
    features = features or []
    keywords = []

    # 品牌关键词
    name_lower = name.lower()
    for brand, kw in _BRAND_KEYWORDS.items():
        if brand.lower() in name_lower:
            keywords.extend(kw.split())

    # 商品名关键词
    keywords.append(name)

    # 特点关键词
    keywords.extend(features)

    # 通用后缀
    if is_physical:
        keywords.extend(["二手", "闲置", "正品", "实物拍摄"])
    else:
        keywords.extend(["虚拟", "自动发货", "正版授权", "数字产品"])

    # 去重并限制数量
    seen = set()
    unique = []
    for kw in keywords:
        k = kw.strip()
        if k and k not in seen:
            seen.add(k)
            unique.append(k)

    return unique[:30]


# ============================================================
# CLI 独立入口
# ============================================================

def main_cli():
    """goofish-copy 独立入口"""
    import sys
    import typer
    from rich.console import Console
    from rich.panel import Panel

    app = typer.Typer(name="goofish-copy", help="闲鱼文案生成器", no_args_is_help=True)
    console = Console()

    @app.command(name="physical")
    def physical_cli(
        name: str = typer.Argument(..., help="商品名称"),
        condition: str = typer.Option("95新", "--condition", "-c"),
        price: int = typer.Option(0, "--price", "-p"),
        features: str = typer.Option("", "--features", "-f"),
        location: str = typer.Option("", "--location", "-l"),
    ):
        result = copy_physical(
            name=name,
            condition=condition,
            price=price,
            features=[f.strip() for f in features.split(",") if f.strip()],
            location=location,
        )
        console.print(Panel(result["copy"], title=f"📝 {name}", border_style="green"))
        console.print(f"\n[dim]关键词: {' '.join(result['keywords'])}[/dim]")

    @app.command(name="virtual")
    def virtual_cli(
        name: str = typer.Argument(..., help="产品名称"),
        price: int = typer.Option(0, "--price", "-p"),
        features: str = typer.Option("", "--features", "-f"),
        tech: str = typer.Option("", "--tech", "-t"),
    ):
        result = copy_virtual(
            name=name,
            price=price,
            features=[f.strip() for f in features.split(",") if f.strip()],
            tech_req=tech,
        )
        console.print(Panel(result["copy"], title=f"📝 {name}", border_style="yellow"))
        console.print(f"\n[dim]关键词: {' '.join(result['keywords'])}[/dim]")

    @app.command(name="optimize")
    def optimize_cli(
        text: str = typer.Argument(..., help="要优化的文案"),
        virtual: bool = typer.Option(False, "--virtual", "-v"),
    ):
        result = copy_optimize(text=text, is_virtual=virtual)
        console.print(Panel(result["optimized"], title="📝 优化后", border_style="blue"))
        if result["suggestions"]:
            console.print("\n[yellow]优化建议:[/yellow]")
            for s in result["suggestions"]:
                console.print(f"  • {s}")

    sys.exit(app())


if __name__ == "__main__":
    main_cli()
