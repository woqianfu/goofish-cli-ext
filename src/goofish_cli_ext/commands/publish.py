# -*- coding: utf-8 -*-
"""商品发布模块 —— 调用 goofish item publish 发布商品"""

from __future__ import annotations

import json
import subprocess
from typing import Optional


def publish_item(
    name: str,
    price: int,
    images: str = "",
    desc: str = "",
    keywords: Optional[list[str]] = None,
) -> dict:
    """发布商品到闲鱼

    先上传图片到闲鱼 CDN，再调用发布接口。

    Args:
        name: 商品标题
        price: 价格（元）
        images: 图片路径列表，逗号分隔 或 "a.png,b.png"
        desc: 商品描述（即生成的文案）
        keywords: 关键词列表

    Returns:
        {"ok": true, "itemId": "...", "status": "published"}
    """
    keywords = keywords or []

    # 1. 上传图片（如果有）
    image_urls = []
    if images:
        for img_path in images.split(","):
            img_path = img_path.strip()
            if not img_path:
                continue
            try:
                upload_cmd = ["goofish", "media", "upload", img_path, "--format", "json"]
                upload_result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=30)
                if upload_result.returncode == 0:
                    upload_data = json.loads(upload_result.stdout)
                    image_urls.append(upload_data.get("url", ""))
            except Exception as e:
                print(f"⚠️ 图片上传失败 {img_path}: {e}")

    # 2. 构建描述（文案 + 关键词）
    full_desc = desc.strip()
    if keywords:
        full_desc += f"\n\n🏷️关键词：{' '.join(keywords)}"

    # 3. 发布
    publish_cmd = [
        "goofish", "item", "publish",
        "--title", name,
        "--desc", full_desc,
        "--price", str(price),
        "--format", "json",
    ]

    # 如果是远程图片 URL
    if image_urls:
        publish_cmd.extend(["--images", ",".join(image_urls)])

    try:
        result = subprocess.run(publish_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            # 检查是否有风控
            stderr = result.stderr.strip()
            if "RGV587" in stderr:
                raise RuntimeError("触发风控熔断（RGV587），建议等待几分钟后重试")
            raise RuntimeError(f"发布失败: {stderr[:200]}")

        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("未找到 goofish 命令，请先安装 goofish-cli")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析发布结果失败: {e}")
