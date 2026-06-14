#!/usr/bin/env python3
"""
闲鱼价格监控 cron 脚本
用于 Hermes cron job 定时执行，实现定时比价 + 微信推送。

安装为 cron job（每日执行）：
    hermes cron create "0 9,21 * * *" \\
        --name "闲鱼比价监控" \\
        --script ~/.hermes/scripts/goofish-price-watch.sh \\
        --no-agent \\
        --deliver weixin

脚本会：
1. 搜索所有设置了预警的关键词
2. 检查是否有低于目标价的新商品
3. 如果有，生成推送文本
4. 如果都没有（无变化），输出空字符串（触发器静默）
"""

import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.expanduser("~/projects/goofish-cli-ext/src"))
os.chdir(os.path.expanduser("~/projects/goofish-cli-ext"))

from goofish_cli_ext.commands.price_watch import (
    list_price_alerts,
    save_snapshot,
    format_price_summary,
)
from goofish_cli_ext.commands.search import search_items_cli


def run():
    """执行一次价格监控"""
    alerts = list_price_alerts()

    if not alerts:
        print("❌ 没有设置价格预警。使用以下命令设置：")
        print("   goofish-x watch add '南卡 Clip Super2' 250")
        print("   goofish-x watch list")
        return

    output_parts = []
    has_alert = False

    for alert in alerts:
        query = alert["query"]
        target = alert["target_price"]

        try:
            # 搜索
            result = search_items_cli(
                query=query,
                limit=20,
                deep_search=True,
                sort="price-asc",
            )
            items = result.get("items", [])

            # 保存快照
            if items:
                save_snapshot(query, items)

            # 检查是否低于目标价
            prices = [i["price"] for i in items if i.get("price", 99999) < 99999]
            if prices:
                min_price = min(prices)
                if min_price <= target:
                    has_alert = True
                    output_parts.append(f"🔔 {query} 低于预警价 ¥{target}！当前最低 ¥{min_price}")
                    # 列出低价商品
                    low_items = [i for i in items if i["price"] <= target][:3]
                    for item in low_items:
                        output_parts.append(f"  ¥{item['price']} {item['title'][:30]}")
                        output_parts.append(f"  {item.get('url', '')}")
                    output_parts.append("")

            # 汇总摘要
            summary = format_price_summary(query)
            output_parts.append(summary)
            output_parts.append("---")

        except Exception as e:
            output_parts.append(f"⚠️ {query} 查询失败: {e}")

    # 输出结果
    print("\n".join(output_parts))

    # no_agent=True 模式：
    # - 非空 stdout → 推送
    # - 空 stdout → 静默（无变化时不打扰）


if __name__ == "__main__":
    run()
