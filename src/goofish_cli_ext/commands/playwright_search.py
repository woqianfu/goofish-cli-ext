# -*- coding: utf-8 -*-
"""
闲鱼 Playwright 搜索引擎
替代 goofish search items，直接用 Playwright 打开闲鱼搜索页抓取数据。

优势：
1. 不依赖 goofish-cli 子进程
2. 可控制搜索 URL 参数（排序、筛选、位置）
3. 更快的响应速度（省去进程通信开销）
4. 解析失败时有更多的调试信息
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Optional

# ============================================================
# 搜索参数
# ============================================================

# 闲鱼搜索 URL 参数
SORT_MAP = {
    "default": "",        # 综合排序
    "price-asc": "price-asc",  # 价格从低到高
    "price-desc": "price-desc", # 价格从高到低
    "new": "new",          # 最新发布
    "credit": "credit",    # 信用最好
}

CONDITION_MAP = {
    "全新": "new",
    "99新": "new",      # 闲鱼只有全新/二手两档
    "95新": "used",
    "9成新": "used",
    "二手": "used",
    "有瑕疵": "used",
}


# ============================================================
# DOM 提取 JS（与 goofish-cli 对齐）
# ============================================================

_EXTRACT_JS = """
() => {
  const sel = {
    card: 'a[href*="/item?id="]',
    title: '[class*="row1-wrap-title"], [class*="main-title"]',
    attrs: '[class*="row2-wrap-cpv"] span[class*="cpv--"]',
    priceWrap: '[class*="price-wrap"]',
    priceNum: '[class*="number"]',
    priceDec: '[class*="decimal"]',
    priceDesc: '[class*="price-desc"] [title], [class*="price-desc"] [style*="line-through"]',
    sellerWrap: '[class*="row4-wrap-seller"]',
    sellerText: '[class*="seller-text"]',
    badge: '[class*="credit-container"] [title], [class*="credit-container"] span',
  };

  const cards = document.querySelectorAll(sel.card);
  const items = [];
  const bodyText = document.body ? document.body.innerText || '' : '';

  cards.forEach((card, idx) => {
    try {
      const titleEl = card.querySelector(sel.title);
      const title = titleEl ? titleEl.textContent.trim() : '';

      const priceWrap = card.querySelector(sel.priceWrap);
      let price = '';
      if (priceWrap) {
        const num = priceWrap.querySelector(sel.priceNum);
        const dec = priceWrap.querySelector(sel.priceDec);
        price = (num ? num.textContent.trim() : '') + (dec ? '.' + dec.textContent.trim() : '');
      }

      const origEl = card.querySelector(sel.priceDesc);
      const original_price = origEl ? (origEl.textContent || origEl.getAttribute('title') || '').trim() : '';

      const sellerWrap = card.querySelector(sel.sellerWrap);
      let location = '';
      let brand = '';
      if (sellerWrap) {
        const sellerText = sellerWrap.querySelector(sel.sellerText);
        location = sellerText ? sellerText.textContent.trim() : '';
      }

      const badgeEl = card.querySelector(sel.badge);
      const badge = badgeEl ? (badgeEl.textContent || badgeEl.getAttribute('title') || '').trim() : '';

      // 从卡片 DOM 树提取属性标签
      const attrsEl = card.querySelector(sel.attrs);
      let condition = '';
      let extra = '';
      if (attrsEl) {
        const spans = attrsEl.querySelectorAll('span');
        // 通常是 [品牌, 成色, 类型] 或 [品牌, 类型]
        const texts = Array.from(spans).map(s => s.textContent.trim()).filter(Boolean);
        if (texts.length >= 2) {
          brand = texts[0];
          // 第二个可能是成色或是品类
          const secondLower = texts[1].toLowerCase();
          if (/全新|99新|95新|9成新|8成新|几乎全新|有瑕疵/.test(secondLower)) {
            condition = texts[1];
            if (texts.length >= 3) extra = texts.slice(2).join(' ');
          } else {
            extra = texts.slice(1).join(' ');
          }
        }
      }

      const href = card.getAttribute('href') || '';
      const url = href.startsWith('http') ? href : 'https://www.goofish.com' + href;
      const itemId = (url.match(/[?&]id=(\\d+)/) || [])[1] || '';

      items.push({
        rank: idx + 1,
        item_id: itemId,
        title,
        url,
        price: price ? '¥' + price : '',
        original_price,
        condition,
        brand,
        extra,
        location,
        badge,
      });
    } catch (e) {
      // skip failed card
    }
  });

  const requiresAuth = /登录|扫码|请登录/.test(bodyText) && items.length === 0;
  const blocked = /验证码|安全验证|访问异常/.test(bodyText);
  const empty = /暂无相关宝贝|没有找到/.test(bodyText);

  return { requiresAuth, blocked, empty, items, bodyPreview: bodyText.slice(0, 500) };
};
"""


# ============================================================
# Playwright 搜索引擎
# ============================================================

def _build_search_url(
    query: str,
    sort: str = "",
    condition: str = "",
    location: str = "",
) -> str:
    """构建闲鱼搜索 URL

    Args:
        query: 搜索关键词
        sort: 排序方式（price-asc/price-desc/new/credit/default）
        condition: 成色筛选（new/used）
        location: 地理位置筛选
    """
    from urllib.parse import quote

    url = f"https://www.goofish.com/search?q={quote(query)}"

    if sort and sort in SORT_MAP.values():
        url += f"&sort={sort}"

    if condition:
        url += f"&condition={condition}"

    if location:
        url += f"&loc={quote(location)}"

    return url


async def _auto_scroll(page, times: int = 3):
    """自动滚动页面触发懒加载"""
    for i in range(times):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        if i < times - 1:
            await page.wait_for_timeout(1500)


async def _run_search(
    query: str,
    limit: int = 30,
    sort: str = "",
    condition: str = "",
    location: str = "",
) -> list[dict]:
    """用 Playwright 执行闲鱼搜索

    Args:
        query: 搜索关键词
        limit: 最大返回条数
        sort: 排序（price-asc/new/credit）
        condition: 成色筛选（new/used）
        location: 位置筛选

    Returns:
        商品列表
    """
    from playwright.async_api import async_playwright

    search_url = _build_search_url(query, sort=sort, condition=condition, location=location)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )

        # 注入 Cookie（从 goofish-cli 持久化的 cookies）
        cookie_file = os.path.expanduser("~/.goofish-cli/cookies.json")
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file) as f:
                    cookies = json.load(f)
                for c in cookies:
                    try:
                        await context.add_cookies([{
                            "name": c["name"],
                            "value": c["value"],
                            "domain": c.get("domain", ".goofish.com"),
                            "path": "/",
                        }])
                    except Exception:
                        pass
            except Exception:
                pass

        page = await context.new_page()

        # 打开搜索页
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # 等待页面加载
        await page.wait_for_timeout(3000)

        # 如果有排序参数，尝试点击排序按钮
        if sort:
            sort_labels = {
                "price-asc": "价格从低到高",
                "price-desc": "价格从高到低",
                "new": "最新发布",
                "credit": "信用最好",
            }
            label = sort_labels.get(sort, "")
            if label:
                try:
                    # 先点击排序下拉按钮
                    sort_btn = page.locator('[class*="sort"], button:has-text("排序"), [class*="dropdown"]').first
                    if await sort_btn.is_visible(timeout=2000):
                        await sort_btn.click()
                        await page.wait_for_timeout(500)
                        # 选择对应排序项
                        opt = page.locator(f'text="{label}"').first
                        if await opt.is_visible(timeout=2000):
                            await opt.click()
                            await page.wait_for_timeout(2000)  # 等待重新加载
                except Exception:
                    pass  # 找不到排序按钮也没关系，走默认排序

        # 自动滚屏触发懒加载
        await _auto_scroll(page, times=3)

        # 额外等待一下
        await page.wait_for_timeout(1000)

        # 执行 JS 提取商品数据
        result = await page.evaluate(_EXTRACT_JS)

        await browser.close()

        # 错误检测
        if result.get("requiresAuth"):
            raise RuntimeError("闲鱼登录态已过期，请重新获取 Cookie")
        if result.get("blocked"):
            raise RuntimeError("触发闲鱼风控，请稍后重试")

        items = result.get("items", [])
        return items[:limit]


# ============================================================
# 同步入口（给 CLI 调用）
# ============================================================

def search_by_playwright(
    query: str,
    limit: int = 30,
    sort: str = "",
    condition: str = "",
    location: str = "",
) -> list[dict]:
    """同步调用 Playwright 搜索

    Args:
        query: 搜索关键词
        limit: 最大返回条数
        sort: 排序（price-asc=价格从低到高, new=最新发布, credit=信用最好）
        condition: 成色（new=全新, used=二手）
        location: 位置（如"上海"）

    Returns:
        商品列表，每个 item 包含：
        - rank, item_id, title, url, price, original_price
        - condition, brand, extra, location, badge
    """
    import asyncio

    # 规范化参数
    if sort and sort not in SORT_MAP.values():
        sort = SORT_MAP.get(sort, "")

    return asyncio.run(_run_search(
        query=query,
        limit=min(limit, 100),
        sort=sort,
        condition=condition,
        location=location,
    ))


# ============================================================
# 命令行测试入口
# ============================================================

if __name__ == "__main__":
    import time
    query = sys.argv[1] if len(sys.argv) > 1 else "南卡 Clip Super2"
    sort = sys.argv[2] if len(sys.argv) > 2 else ""
    cond = sys.argv[3] if len(sys.argv) > 3 else ""
    loc = sys.argv[4] if len(sys.argv) > 4 else ""

    print(f"搜索: {query}")
    if sort:
        print(f"排序: {sort}")
    if cond:
        print(f"成色: {cond}")
    if loc:
        print(f"位置: {loc}")
    print("-" * 40)

    t0 = time.time()
    items = search_by_playwright(query, limit=10, sort=sort, condition=cond, location=loc)
    elapsed = time.time() - t0

    print(f"共 {len(items)} 条结果，耗时 {elapsed:.1f}s")
    for item in items:
        price = item.get("price", "")
        title = item.get("title", "")[:40]
        loc2 = item.get("location", "")
        cond2 = item.get("condition", "")
        badge = item.get("badge", "")
        print(f"  {price:>6s}  {title:40s}  {loc2:6s}  {cond2:8s}  {badge}")
    print("-" * 40)
