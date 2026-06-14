# -*- coding: utf-8 -*-
"""
多平台文案互转 — 闲鱼 ↔ 转转 ↔ 拍拍

每个平台有固定的文案风格差异：
- 闲鱼：emoji 分段 + 风险前置 + 关键词标签
- 转转：强调验机/质检报告，简洁描述
- 拍拍：京东二手，正规格式 + 质保说明
"""

from __future__ import annotations

import re

PLATFORMS = {
    "闲鱼": {
        "name": "闲鱼",
        "desc": "阿里巴巴旗下二手平台",
        "style": "emoji分段 + 风险前置 + 关键词标签",
        "features": ["7模块结构", "⚠️警告前置", "🏷️关键词堆叠"],
    },
    "转转": {
        "name": "转转",
        "desc": "58同城旗下二手平台",
        "style": "简洁明了 + 强调质检 + 验机报告",
        "features": ["质检报告", "验机保障", "30天质保"],
    },
    "拍拍": {
        "name": "拍拍",
        "desc": "京东旗下二手平台",
        "style": "正规格式 + 质保说明 + 京东物流",
        "features": ["成色评级", "7天无理由", "京东物流"],
    },
}


def convert_copy(text: str, from_platform: str = "", to_platform: str = "") -> dict:
    """在平台间转换文案格式

    Args:
        text: 原文案
        from_platform: 来源平台（留空自动检测）
        to_platform: 目标平台

    Returns:
        {
            "converted": "...",
            "from_platform": "...",
            "to_platform": "...",
            "changes": [...],
        }
    """
    # 自动检测来源平台
    if not from_platform:
        from_platform = _detect_platform(text)

    if not to_platform or from_platform == to_platform:
        return {
            "converted": text,
            "from_platform": from_platform,
            "to_platform": from_platform,
            "changes": ["无需转换"],
        }

    text = text.strip()
    changes = []

    # 目标平台转换
    if to_platform == "转转":
        text, c = _to_zhuanzhuan(text)
        changes.extend(c)
    elif to_platform == "拍拍":
        text, c = _to_paipai(text)
        changes.extend(c)
    elif to_platform == "闲鱼":
        text, c = _to_xianyu(text)
        changes.extend(c)

    return {
        "converted": text.strip(),
        "from_platform": from_platform,
        "to_platform": to_platform,
        "changes": changes or ["格式已适配"],
    }


def _detect_platform(text: str) -> str:
    """检测文案来源平台"""
    text_lower = text.lower()

    # 转转特征
    if any(kw in text_lower for kw in ["转转", "质检", "验机", "验机报告"]):
        return "转转"

    # 拍拍特征
    if any(kw in text_lower for kw in ["拍拍", "京东二手", "7天无理由", "成色评级"]):
        return "拍拍"

    # 闲鱼特征
    if any(kw in text for kw in ["🏷️", "⚠️", "📦", "🔒"]):
        return "闲鱼"

    return "闲鱼"  # 默认


def _to_zhuanzhuan(text: str) -> tuple[str, list[str]]:
    """转为转转文案格式"""
    changes = []
    lines = text.split("\n")
    new_lines = []
    has_quality = False

    for line in lines:
        # 移除闲鱼 emoji 标签
        line = re.sub(r"[⚠️💰📦🔒✅🏷️💡📎]", "", line)
        # 移除关键词标签行
        if "🏷️" in line or "关键词" in line:
            continue
        # 缩短闲置原因
        if "吃灰" in line or "闲置" in line:
            line = line.replace("闲置数码产品，买来用了没多久，一直放着吃灰", "个人闲置")
        # 添加质检提示
        if "功能正常" in line or "测试" in line:
            has_quality = True
        if line.strip():
            new_lines.append(line)

    # 转转尾部添加质检说明
    footer = "\n\n✅【转转质检】支持转转验机服务，30天质保"
    new_text = "\n".join(new_lines) + footer

    changes = [
        "移除闲鱼 emoji 标签",
        "简化出闲置原因",
        "添加转转质检 + 30天质保说明",
        "移除关键词标签堆叠",
    ]
    return new_text, changes


def _to_paipai(text: str) -> tuple[str, list[str]]:
    """转为拍拍文案格式"""
    changes = []
    lines = text.split("\n")
    new_lines = []
    has_rating = False

    for line in lines:
        # 移除闲鱼 emoji
        line = re.sub(r"[⚠️💰📦🔒✅🏷️💡📎]", "", line)
        if "🏷️" in line or "关键词" in line:
            continue
        # 添加成色评级
        if "成色" in line or "95新" in line or "全新" in line:
            has_rating = True
        if line.strip():
            new_lines.append(line)

    # 拍拍尾部
    if not has_rating:
        new_lines.append("\n【成色评级】95新（轻微使用痕迹）")

    footer = "\n【售后保障】7天无理由退货 | 京东物流发货 | 正规发票"
    new_text = "\n".join(new_lines) + footer

    changes = [
        "移除 emoji 标签",
        "添加拍拍成色评级",
        "添加7天无理由 + 京东物流说明",
    ]
    return new_text, changes


def _to_xianyu(text: str) -> tuple[str, list[str]]:
    """转为闲鱼文案格式"""
    changes = []
    lines = text.split("\n")
    new_lines = []

    # 检查是否已有关键词标签
    has_keywords = any("🏷️" in l or "关键词" in l and "：" in l for l in lines)

    for line in lines:
        # 替换转转/拍拍特有标识
        line = line.replace("【转转质检】", "✅【交易保障】")
        line = line.replace("【成色评级】", "📦【成色状态】")
        line = line.replace("【售后保障】", "⚠️【购买须知】")
        line = line.replace("30天质保", "包邮 不退不换")
        line = line.replace("7天无理由退货", "二手商品售出不退不换")
        if line.strip():
            new_lines.append(line)

    # 添加闲鱼特有的风险提示
    if not any("完美主义" in l for l in lines):
        new_lines.append("\n⚠️ 完美主义者请绕道，二手商品售出不退不换")

    # 添加关键词标签
    if not has_keywords:
        new_lines.append("\n🏷️关键词：二手 闲置 正品")

    changes = [
        "替换平台特有标识",
        "添加闲鱼风险提示",
        "添加关键词标签",
    ]
    return "\n".join(new_lines), changes


# ============================================================
# CLI 帮助
# ============================================================

AVAILABLE_PLATFORMS = list(PLATFORMS.keys())
