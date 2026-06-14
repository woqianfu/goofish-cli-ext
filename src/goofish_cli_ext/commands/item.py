# -*- coding: utf-8 -*-
"""商品详情查询"""

from __future__ import annotations

import json
import subprocess


def get_item(item_id: str) -> dict:
    """查询闲鱼商品详情

    Args:
        item_id: 商品 ID

    Returns:
        {"title": "...", "price": ..., "condition": "...", "location": "...", ...}
    """
    cmd = ["goofish", "item", "get", item_id, "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"查询失败: {result.stderr.strip()[:200]}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("未找到 goofish 命令，请先安装 goofish-cli")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析响应失败: {e}")


def get_item_with_view(item_id: str) -> dict:
    """用浏览器视角查看商品详情（字段更全，抗风控）

    Args:
        item_id: 商品 ID

    Returns:
        更完整的商品信息 dict
    """
    cmd = ["goofish", "item", "view", item_id, "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"查看详情失败: {result.stderr.strip()[:200]}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("未找到 goofish 命令，请先安装 goofish-cli")
