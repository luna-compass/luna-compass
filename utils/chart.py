# utils/chart.py
# ホロスコープ円形チャート描画（v3：ラベル完全外出し＋凡例方式）

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def plot_horoscope(natal_longitudes, houses, transit_longitudes=None):

    SIGN_LABELS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    PLANET_ORDER = ["太陽", "月", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]

    PLANET_LABELS = {
        "太陽": "☉Sun", "月": "☽Moon", "水星": "☿Me", "金星": "♀Ve", "火星": "♂Ma",
        "木星": "♃Jup", "土星": "♄Sat", "天王星": "♅Ur", "海王星": "♆Ne", "冥王星": "♇Pl"
    }

    PLANET_COLORS = {
        "太陽": "#e53e3e",
        "月":   "#6b7280",
        "水星": "#2563eb",
        "金星": "#16a34a",
        "火星": "#dc2626",
        "木星": "#9333ea",
        "土星": "#92400e",
        "天王星": "#0891b2",
        "海王星": "#1d4ed8",
        "冥王星": "#374151",
    }

    # 天体番号（チャート上に表示する番号）
    PLANET_NUM = {name: str(i + 1) for i, name in enumerate(PLANET_ORDER)}

    asc = houses[0]

    def to_rad(deg):
        return np.deg2rad((asc - deg) % 360)

    def polar_to_xy(th, r):
        x = r * np.cos(th - np.pi / 2)
        y = r * np.sin(th - np.pi / 2)
        return x, y

    # figureサイズを大きめに（下に凡例スペース確保）
    fig = plt.figure(figsize=(8, 10))
    fig.patch.set_facecolor("#f5f3ff")

    # チャートエリア（上部）
    ax = fig.add_axes([0.05, 0.22, 0.90, 0.75])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_facecolor("#f5f3ff")

    def draw_circle(r, color, lw=1.0):
        c = plt.Circle((0, 0), r, color=color, fill=False, linewidth=lw)
        ax.add_patch(c)

    # ===== 円 =====
    draw_circle(0.98, "#4c1d95", lw=1.2)
    draw_circle(0.92, "#7c3aed", lw=1.0)
    draw_circle(0.72, "#a78bfa", lw=1.0)
    draw_circle(0.60, "#c4b5fd", lw=0.7)

    # ===== サイン帯 =====
    for i, label in enumerate(SIGN_LABELS):
        thetas = np.linspace(to_rad(i * 30), to_rad((i + 1) * 30), 50)
        xs_o = 0.92 * np.cos(thetas - np.pi / 2)
        ys_o = 0.92 * np.sin(thetas - np.pi / 2)
        xs_i = 0.72 * np.cos(thetas - np.pi / 2)
        ys_i = 0.72 * np.sin(thetas - np.pi / 2)
        xs = np.concatenate([xs_o, xs_i[::-1]])
        ys = np.concatenate([ys_o, ys_i[::-1]])
        color = "#ede9fe" if i % 2 == 0 else "#ddd6fe"
        ax.fill(xs, ys, color=color, alpha=0.9)

        mid_th = to_rad(i * 30 + 15)
        lx, ly = polar_to_xy(mid_th, 0.82)
        ax.text(lx, ly, label, ha="center", va="center",
                fontsize=6.5, color="#4c1d95", fontweight="bold")

    # ===== ハウス線 =====
    for i, cusp in enumerate(houses):
        th = to_rad(cusp)
        x0, y0 = polar_to_xy(th, 0.0)
        x1, y1 = polar_to_xy(th, 0.72)
        lw  = 1.5 if i == 0 else 0.6
        col = "#4c1d95" if i == 0 else "#9ca3af"
        ax.plot([x0, x1], [y0, y1], color=col, linewidth=lw)

        next_cusp = houses[(i + 1) % 12]
        mid = (cusp + ((next_cusp - cusp) % 360) / 2) % 360
        mid_th = to_rad(mid)
        mx, my = polar_to_xy(mid_th, 0.36)
        ax.text(mx, my, str(i + 1), ha="center", va="center",
                fontsize=8, color="#6b7280")

    # ===== 天体ドット＋番号 =====
    DOT_R = 0.64
    for name in PLANET_ORDER:
        if name not in natal_longitudes:
            continue
        deg = natal_longitudes[name]
        th = to_rad(deg)
        px, py = polar_to_xy(th, DOT_R)
        color = PLANET_COLORS.get(name, "black")
        num = PLANET_NUM[name]

        # ドット
        ax.plot(px, py, "o", color=color, markersize=8, zorder=5)
        # 番号をドットの上に白文字で表示
        ax.text(px, py, num, ha="center", va="center",
                fontsize=5.5, color="white", fontweight="bold", zorder=6)

    # ===== トランジット =====
    if transit_longitudes:
        for name, deg in transit_longitudes.items():
            th = to_rad(deg)
            tx, ty = polar_to_xy(th, 0.78)
            ax.plot(tx, ty, "^", color="blue", markersize=5, alpha=0.6, zorder=4)

    # ===== 凡例エリア（チャート下） =====
    ax_leg = fig.add_axes([0.03, 0.01, 0.94, 0.20])
    ax_leg.axis("off")
    ax_leg.set_facecolor("#f5f3ff")
    ax_leg.set_xlim(0, 10)
    ax_leg.set_ylim(0, 4)

    ax_leg.text(5, 3.5, "── 天体一覧 ──", ha="center", va="center",
                fontsize=9, color="#4c1d95", fontweight="bold")

    # 5列×2行で表示
    cols = 5
    items = [(name, PLANET_NUM[name], PLANET_LABELS[name], PLANET_COLORS[name])
             for name in PLANET_ORDER if name in natal_longitudes]

    for idx, (name, num, label, color) in enumerate(items):
        row = idx // cols
        col = idx % cols
        x = 0.8 + col * 1.85
        y = 2.7 - row * 1.3

        deg = natal_longitudes[name]
        from utils.astro import split_sign_degree
        sign, d = split_sign_degree(deg)

        # 番号付き丸
        circle = plt.Circle((x, y), 0.28, color=color, zorder=3)
        ax_leg.add_patch(circle)
        ax_leg.text(x, y, num, ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold", zorder=4)

        # 天体名と度数
        ax_leg.text(x + 0.38, y + 0.15, label,
                    ha="left", va="center", fontsize=7.5, color=color, fontweight="bold")
        ax_leg.text(x + 0.38, y - 0.25, f"{sign} {d:.1f}°",
                    ha="left", va="center", fontsize=6.5, color="#374151")

    return fig
