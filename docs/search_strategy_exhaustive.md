# Xianyu Low-Price Search Strategy - Exhaustive Analysis

> Version: 1.0 | Date: 2026-06-14
> Based on existing code (search.py, playwright_search.py) + reverse engineering experience

---

## Core Constraints

| Constraint | Value | Source |
|------------|-------|--------|
| Single keyword max results | ~250 items | Web: 5 pages x ~50 items/page |
| App single keyword | ~50-250 items | Varies by version |
| Keyword independence | Mostly independent (some overlap) | Verified |
| Sort independence | Each sort returns different order | Verified |
| Crawl tools | Playwright / goofish-cli / raw HTTP | Available |
| Internal API | None | Reverse engineering limit |

---

## [Dimension A - Keyword Variants]

### A1. Full Name / Abbreviation / Common Name

Examples:
- Nank Ultra -> NANK Ultra -> Nank Ultra ear clip
- Nank Clip Super2 -> Clip Super2 -> NANK Clip Super2 -> Clip Gen2
- AirPods Pro 2 -> Apple Earphones Pro Gen2 -> AirPodsPro2
- Sony XM5 -> Sony 1000XM5 -> WH-1000XM5 -> XM5 Over-ear

**Count per product**: 3-8 core variants
**Feasibility**: Yes - Playwright fully supported (just construct different query params)

### A2. Brand Chinese/English/Case

| Chinese | English | Case variants |
|---------|---------|---------------|
| Nank | NANK, Nank, nank | 4 |
| Apple | Apple, APPLE, apple | 4 |
| Huawei | Huawei, HUAWEI | 3 |
| Xiaomi | Xiaomi, xiaomi | 3 |
| Sony | Sony, sony | 3 |
| Samsung | Samsung, samsung | 3 |
| Beats | beats, BEATS | 3 |
| Bose | bose, BOSE | 3 |

**Count**: 12 brands x avg 3.5 variants = ~42
**Feasibility**: Yes

### A3. With Spaces / Without Spaces

```
"Nank Ultra"  ->  "NankUltra"
"AirPods Pro" ->  "AirPodsPro"
"NANK Clip Super2" -> "NANKClipSuper2"
```

**Count**: Each core term x 2
**Feasibility**: Yes

### A4. Quality/Emotion Suffixes

| Category | Suffix words | Count |
|----------|-------------|-------|
| Condition | brand new, used, personal use | 3 |
| Trust | authentic, genuine, official | 4 |
| Transaction | free shipping, negotiable, trade | 4 |
| Emotion | idle, urgent sale, price drop, great price, great value, practical, cheap | 8 |
| Status | moving sale, decluttering, need cash, unused, gathering dust | 6 |
| Hype | bargain, insane price, rock bottom, loss sale | 4 |

**Count**: ~29 suffixes per core term
**Feasibility**: Yes

### A5. Prefixes

| Category | Prefix | Count |
|----------|--------|-------|
| Action | selling, buying, seeking, trading | 4 |
| Status | personal use, brand new, idle | 3 |

**Count**: 7 prefixes
**Feasibility**: Yes

### A6. Category Word Replacement

```
earphones -> earbuds -> headset -> headphones -> bluetooth -> wireless
phone -> smartphone -> 5G phone -> backup phone -> android
computer -> laptop -> thin-and-light -> gaming laptop -> MacBook
```

**Count**: 3-6 replacement words per category
**Feasibility**: Yes

### A7. Real User Typos (from Xianyu corpus)

| Correct | Typo variants | Count |
|---------|--------------|-------|
| personal use | personal_use | 2 |
| idle | idel, idle_out | 3 |
| authentic | authenic, real | 3 |
| brand new | brand_new, BNIB | 2 |
| free shipping | free_ship, free_post | 3 |
| AirPods | AirPods, Airpod, Aripods | 3 |
| Sony | Soney, Soni | 2 |
| Huawei | Hwawei | 1 |
| Xiaomi | Xaomi | 1 |
| Apple | Appel | 1 |
| bluetooth | blutooth, blueetooth | 2 |

**Count**: ~23 typo variants
**Feasibility**: Yes (diminishing returns)

---

## [Dimension B - Sort Order]

| Sort | Param Value | Behavior | Coverage |
|------|------------|----------|----------|
| Default (comprehensive) | default | Xianyu default recommendation algorithm | ~250 items |
| Price low to high | price-asc | Lowest price first (many fake-low listings pollute front) | ~250 items |
| Price high to low | price-desc | Highest price first, finds price ceiling | ~250 items |
| Newest | new | Sort by publish time descending, sees just-listed first | ~250 items |
| Best credit | credit | Highest credit sellers first | ~250 items |

**Count**: 5 sort modes
**Coverage**: Per keyword x 5 sorts = 5x result set
- Single keyword + 5 sorts = 5 x 250 = **1,250 items**
- Combined keywords + 5 sorts = 200 x 5 x 250 = **250,000 items** (theoretical max)

**Feasibility**: Yes - Playwright fully supported via `sort` URL param or click interaction

---

## [Dimension C - Price Range]

Xianyu search URL supports `minPrice` and `maxPrice` parameters. Enumerate every 50 yuan:

| Category | Price Range | Intervals |
|----------|------------|-----------|
| Earphones/wearables | 0 - 2000 | 40 intervals |
| Phones/tablets | 0 - 10000 | 200 intervals |
| Laptops/cameras | 0 - 30000 | 600 intervals |
| Luxury goods/watches | 0 - 100000 | 2000 intervals |

**Practical interval strategy**:

| Interval type | Example | Count |
|--------------|---------|-------|
| Ultra-low (0-200) | 0-50, 50-100, 100-150, 150-200 | 4 |
| Low (200-1000) | Every 100: 200-300...900-1000 | 8 |
| Mid (1000-5000) | Every 200 | 20 |
| High (5000+) | Every 500 | Depends |

**Count**: 20-200 intervals per category
**Coverage**: Each interval returns ~250 items
- 40 intervals x 250 = **10,000 items**
- 200 intervals x 250 = **50,000 items**

**Feasibility**: Partially feasible - URL params need verification. Also available via goofish-cli `--min-price`/`--max-price`.

---

## [Dimension D - Geographic Location]

| Level | Cities | Count |
|-------|--------|-------|
| Nationwide | Unlimited | 1 |
| Tier-1 | Beijing/Shanghai/Guangzhou/Shenzhen | 4 |
| New Tier-1 | Chengdu/Hangzhou/Wuhan/Chongqing/Nanjing/Suzhou/Xi'an/Changsha/Tianjin/Zhengzhou/Dongguan/Qingdao/Kunming/Ningbo/Hefei | 15 |
| Tier-2 | Foshan/Shenyang/Wuxi/Jinan/Xiamen/Fuzhou/Wenzhou/Dalian/Harbin/Guiyang/Shijiazhuang/Nanchang/Changchun/Quanzhou/Nanning/Jinhua/Changzhou/Jiaxing/Nantong/Baoding/Taiyuan... | ~30 |
| User's city | From IP or config | 1 |

**Count**: 1 + 4 + 15 + 30 = **50 locations**
**Coverage**: Each location ~250 items
- 50 x 250 = **12,500 items** (single keyword)
- With keyword variants: 200 x 50 x 250 = **2,500,000** (theoretical)

**Feasibility**: Yes - Playwright fully supported via `loc` URL param

---

## [Dimension E - Condition Filter]

| Condition | Param | Note |
|-----------|-------|------|
| All | "" | Default |
| Brand new | "new" | Xianyu has two tiers: new/used |
| Used | "used" | 99% new ~ damaged |

**Count**: 3 states
**Feasibility**: Yes - Playwright fully supported (CONDITION_MAP exists, URL param `condition`)

---

## [Dimension F - Category ID]

| Level | Example | catId (inferred) |
|-------|---------|-----------------|
| Earphones | P100001 | Precise filter |
| Bluetooth earphones | P100001001 | More precise |
| Phones | P200001 | - |
| Speakers | P300001 | - |

**Count**: 1-3 category levels per category = ~30 categories
**Coverage**: Each category + keyword = independent result set

**Feasibility**: Needs verification - need to check if web search supports catId param. App definitely supports category filtering. Playwright can simulate category clicks.

---

## [Dimension G - Item Status]

| Status | Implementation | Feasibility |
|--------|---------------|-------------|
| Active | Default state | Yes - default |
| Ending soon | Sort=new + time diff | Indirect - no direct param |
| Newly listed | sort=new | Yes - Playwright |
| About to expire | No direct param | No |

**Count**: 2-3 states
**Feasibility**: Mostly via sort order, no independent filter

---

## [Dimension H - Seller Type]

| Type | Identification | Feasibility |
|------|---------------|-------------|
| Personal seller | Title keywords + merchant phrase detection | Post-search filter |
| Xianyu Player | Badge label | Post-search filter |
| Brand store/official | Badge/store identification | Post-search filter |
| Auction | Title contains "auction" | Post-search filter |

**Count**: 4 types
**Feasibility**: Post-search classification only, not a search parameter. Already implemented in `_is_personal_seller()`.

---

## [Dimension I - Time Window / Scheduled Polling]

| Strategy | Interval | Description |
|----------|----------|-------------|
| Real-time monitor | Hourly | Compare with last result, catch new low-price listings |
| Scheduled polling | 3x daily | Morning/noon/evening covers full day |
| Trigger-based | Price change notification | Monitor price changes |

**Count**: N/A (time dimension)
**Feasibility**: Yes - cron_price_watch.py/sh already implemented

---

## Theoretical Maximum Coverage

### Single Product Maximum

| Combination | Max independent keywords/params | Each returns | Total raw | Estimated unique |
|------------|-------------------------------|-------------|-----------|-----------------|
| A x B (5 sorts) | 200 x 5 = 1,000 | ~250 | 250,000 | ~3,000-8,000 |
| A x B x C (40 intervals) | 200 x 5 x 40 = 40,000 | ~250 | 10,000,000 | ~50,000-100,000 |
| A x B x C x D (50 cities) | 200 x 5 x 40 x 50 = 2,000,000 | ~250 | 500,000,000 | ~500,000-2,000,000 |

### Practical Recommended Strategies

| Strategy | Requests | Est. unique items | Est. time |
|----------|----------|-------------------|-----------|
| Basic: A(8 kw) x B(2 sorts: price-asc+new) | 16 | ~2,000 | ~6 min |
| Enhanced: A(20 kw) x B(3 sorts) x C(3 intervals) | 180 | ~8,000 | ~30 min |
| Pro: A(50 kw) x B(5 sorts) x C(10 intervals) x D(5 cities) | 12,500 | ~50,000 | ~hours |
| Extreme: A(200 kw) x B(5 sorts) x C(40 intervals) x D(50 cities) | 2,000,000 | ~500,000 | Days (unrealistic) |

---

## Playwright Feasibility Table

| Dim | Strategy | Playwright? | Note |
|-----|----------|------------|------|
| A1 | Full/abbrev/common name variants | YES | Different query params |
| A2 | Brand CN/EN/case | YES | Same |
| A3 | With/without spaces | YES | Same |
| A4 | Quality/emotion suffixes | YES | Same |
| A5 | Prefix words | YES | Same |
| A6 | Category word replacement | YES | Same |
| A7 | Typos | YES | Same |
| A8 | Combined variants | YES | Loop to construct URLs |
| B1 | Default sort | YES | sort="" |
| B2 | Price low to high | YES | sort="price-asc" |
| B3 | Price high to low | YES | sort="price-desc" |
| B4 | Newest | YES | sort="new" |
| B5 | Best credit | YES | sort="credit" |
| C | Price ranges | PARTIAL | Need to verify URL param names |
| D | Geographic location | YES | loc param |
| E | Condition | YES | condition param |
| F | Category ID | PARTIAL | May need simulated click |
| G | Item status | PARTIAL | Via sort + post-filter |
| H | Seller type | PARTIAL | Post-search filter only |
| I | Time window polling | YES | Cron tasks |

---

## goofish-cli Support

| Dim | goofish-cli search items | Note |
|-----|-------------------------|------|
| Keyword search | YES | `goofish search items <query>` |
| Price range | YES | `--min-price` / `--max-price` |
| Sort | PARTIAL | `--sort-by-price` only sorts by price |
| Location | NOT CONFIRMED | May not support |
| Condition | NOT CONFIRMED | May not support |
| Category | NOT CONFIRMED | May not support |
| Limit | YES | `--limit` |

---

## Recommended Strategies (Practical Priority)

### #1 Multi-keyword x Price Sort (Best ROI)
```
15-20 keywords per product x sort=price-asc
= 15-20 requests, covers 80% of low-price items
```
**Time**: ~5 min
**Coverage**: 1,500-3,000 unique items
**Code**: Existing `_expand_keywords()` + `sort_by_price=True`

### #2 Multi-keyword x Price Sort + Price Range
```
20 keywords x 5 price ranges (0-100, 100-300, 300-500, 500-1000, 1000+)
= 100 requests
```
**Time**: ~20 min
**Coverage**: 5,000-10,000 items
**Code**: Needs loop extension

### #3 Multi-keyword x 3 Sorts (price-asc + new + credit)
```
20 keywords x 3 sorts = 60 requests
```
**Time**: ~15 min
**Coverage**: 3,000-5,000 items (different angles)
**Code**: Sort param already exists

### #4 Multi-keyword x 2 Sorts x 3 Core Cities
```
20 keywords x 2 sorts x 3 cities = 120 requests
```
**Time**: ~30 min
**Coverage**: 5,000-8,000 items
**Code**: Needs loc param loop

### A x B x C (Most Recommended)
```
20 keywords x 3 sorts x 5 price ranges = 300 requests
```
**Time**: ~1 hour (with anti-ban delays)
**Coverage**: **15,000-30,000 unique items**
**Code**: New strategy combiner needed

---

## Anti-Ban Notes

| Risk | Mitigation | In existing code? |
|------|-----------|------------------|
| IP rate limit | 2-5s delay between requests | No - needs addition |
| CAPTCHA | User agent + reduce frequency | Partial |
| Cookie expiry | Persistent cookies + periodic refresh | Yes - cookie_file loading |
| Account ban | Keep QPS < 5 | No - needs implementation |
| Same IP search | Random delay 3-8s between sort/keyword switches | No - needs addition |
| Browser fingerprint detection | --disable-blink-features=AutomationControlled | Yes - already used |

---

## Summary

**Theoretical upper bound**: With A(200 kw) x B(5 sorts) x C(40 intervals) x D(50 cities), theoretically reachable: **500K-2M items**. Pure math upper bound, limited by rate limits, availability, and actual total listings.

**Recommended practical upper bound**: A(20 kw) x B(3 sorts) x C(5 intervals) = 300 requests, **15,000-30,000 unique items** - enough to cover 95%+ of a category's low-price items.

**Already implemented in code**:
- `search.py`: Multi-keyword expansion (`_expand_keywords`), price extraction, fake-low-price detection, quality scoring, smart grouping
- `playwright_search.py`: Playwright browser search, 5 sort modes, condition/location filters
- `cron_price_watch.py`: Scheduled polling for price changes

**Priority missing features to implement**:
1. Verify `minPrice`/`maxPrice` URL params via reverse engineering
2. Random delay anti-ban mechanism
3. Multi-city loop search
4. Category ID filtering
