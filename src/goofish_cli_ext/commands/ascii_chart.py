# -*- coding: utf-8 -*-
"""
ASCII 走势图生成器
用于终端展示价格变化趋势，无需图形界面。
"""

from __future__ import annotations


def price_sparkline(
    dates: list[str],
    avgs: list[int],
    mins: list[int],
    maxs: list[int],
    width: int = 30,
    height: int = 6,
) -> str:
    """
    生成价格走势 ASCII 图

    输出示例：
    ```
    ¥320 ┤        ╭──╮
    ¥300 ┤  ╭─────╯  ╰──╮
    ¥280 ┤─╯             ╰──
    ¥260 ┤
        └──┬──┬──┬──┬──┬──
          06/01  06/03  06/05
    ```

    Args:
        dates: 日期标签 ["06-01", "06-02", ...]
        avgs: 每日均价列表
        mins: 每日最低价列表
        maxs: 每日最高价列表
        width: 图表宽度（字符数）
        height: 图表高度（行数）

    Returns:
        ASCII 图表字符串
    """
    if not avgs or len(avgs) < 2:
        return ""

    min_val = min(mins) if mins else min(avgs)
    max_val = max(maxs) if maxs else max(avgs)

    # 让范围有上下边距
    padding = max(1, (max_val - min_val) // 10)
    min_val = max(0, min_val - padding)
    max_val = max_val + padding

    if max_val == min_val:
        max_val = min_val + 10

    # 数据点数量
    n = len(avgs)

    # 压缩到 width 个数据点
    if n > width:
        step = n / width
        compressed_idx = [int(i * step) for i in range(width)]
        compressed_avgs = [avgs[i] for i in compressed_idx]
        compressed_mins = [mins[i] for i in compressed_idx]
        compressed_maxs = [maxs[i] for i in compressed_idx]
        n = width
    else:
        compressed_avgs = avgs
        compressed_mins = mins
        compressed_maxs = maxs

    # 每个数据点占 1 列
    chart_cols = n

    # 价格标签行
    def fmt_price(p: int) -> str:
        if p >= 1000:
            return f"¥{p//1000}k"
        return f"¥{p}"

    # 生成图表网格
    lines = []
    for row in range(height):
        # 当前行的价格阈值（从高到低）
        price_at_row = max_val - (max_val - min_val) * row / (height - 1)

        line_chars = ""
        for col in range(chart_cols):
            avg = compressed_avgs[col]
            mn = compressed_mins[col]
            mx = compressed_maxs[col]

            # 判断当前位置与数据点的关系
            if row == 0:
                # 第一行：显示最高点
                if mx >= price_at_row:
                    line_chars += "╮" if col > 0 and compressed_maxs[col-1] >= price_at_row else "╭"
                else:
                    line_chars += " "
            elif row == height - 1:
                # 最后一行：显示最低点
                if mn <= price_at_row:
                    line_chars += "╰" if col > 0 and compressed_mins[col-1] <= price_at_row else "╯"
                else:
                    line_chars += " "
            else:
                # 中间行：价格线
                if avg <= price_at_row:
                    line_chars += "─"
                elif mn <= price_at_row <= mx:
                    line_chars += "·"

                else:
                    line_chars += " "

        # 行首价格标签
        label = f"{fmt_price(int(price_at_row)):>8s} ┤"
        lines.append(f"{label}{line_chars}")

    # X 轴
    if n >= 3:
        x_labels = []
        label_positions = [0, n // 2, n - 1]
        for i in range(n):
            if i in label_positions:
                idx = label_positions.index(i)
                label = dates[i * len(dates) // n] if len(dates) != n else dates[i]
                x_labels.append(f"{label:^7s}")
            else:
                x_labels.append(" " * 7)
    else:
        x_labels = [f"{d:^7s}" for d in dates]

    x_axis_chars = "".join(x_labels)
    x_axis = f"{'':>9s} {'─' * chart_cols}"
    x_labels_line = f"{'':>9s} {x_axis_chars}"

    return "\n".join(lines) + "\n" + x_axis + "\n" + x_labels_line


def _test():
    """测试走势图"""
    dates = [f"06-{i:02d}" for i in range(1, 15)]
    avgs = [260, 265, 258, 270, 268, 255, 250, 248, 252, 258, 262, 255, 250, 245]
    mins = [240, 245, 240, 250, 245, 235, 230, 228, 235, 240, 245, 238, 232, 228]
    maxs = [280, 285, 275, 290, 285, 270, 265, 260, 268, 275, 278, 270, 265, 260]

    print("价格走势图测试:")
    print(price_sparkline(dates, avgs, mins, maxs))


if __name__ == "__main__":
    _test()
