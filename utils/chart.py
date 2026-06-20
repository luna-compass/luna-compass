# utils/chart.py
import numpy as np
import matplotlib.pyplot as plt
from utils.astro import split_sign_degree

def plot_horoscope(natal_longitudes, houses, transit_longitudes=None, time_unknown=False):

    SIGN_LABELS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    SIGN_SHORT = {
        "牡羊座":"Ari","牡牛座":"Tau","双子座":"Gem","蟹座":"Can","獅子座":"Leo","乙女座":"Vir",
        "天秤座":"Lib","蠍座":"Sco","射手座":"Sag","山羊座":"Cap","水瓶座":"Aqu","魚座":"Pis"
    }

    PLANET_LABELS = {
        "太陽":"Sun","月":"Moon","水星":"Me","金星":"Ve","火星":"Ma",
        "木星":"Jup","土星":"Sat","天王星":"Ur","海王星":"Ne","冥王星":"Pl"
    }

    PLANET_COLORS = {
        "太陽": "#e53e3e", "月": "#6b7280", "水星": "#2563eb", "金星": "#16a34a",
        "火星": "#dc2626", "木星": "#9333ea", "土星": "#92400e",
        "天王星": "#0891b2", "海王星": "#1d4ed8", "冥王星": "#374151",
    }

    PLANET_ORDER = ["太陽","月","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]

    ASPECT_STYLES = {
        "コンジャンクション": {"color": "#e53e3e", "lw": 1.5, "ls": "-"},
        "トライン":           {"color": "#16a34a", "lw": 1.2, "ls": "-"},
        "スクエア":           {"color": "#dc2626", "lw": 1.0, "ls": "--"},
        "セクスタイル":       {"color": "#2563eb", "lw": 0.8, "ls": "-"},
        "オポジション":       {"color": "#9333ea", "lw": 1.0, "ls": "--"},
    }

    # ソーラーチャート：出生時刻不明のとき太陽を1ハウスに固定
    if time_unknown and "太陽" in natal_longitudes:
        sun_lon = natal_longitudes["太陽"]
        asc = sun_lon
        houses = [(sun_lon + i * 30) % 360 for i in range(12)]
    else:
        asc = houses[0]

    def lon_to_xy(lon, r):
        math_deg = 180.0 + ((lon - asc) % 360)
        rad = np.deg2rad(math_deg)
        return r * np.cos(rad), r * np.sin(rad)

    def lon_to_rad(lon):
        math_deg = 180.0 + ((lon - asc) % 360)
        return np.deg2rad(math_deg)

    fig, ax = plt.subplots(figsize=(10, 11))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.30, 1.05)
    fig.patch.set_facecolor("#f5f3ff")
    ax.set_facecolor("#f5f3ff")

    def draw_circle(r, color, lw=1.0):
        ax.add_patch(plt.Circle((0,0), r, color=color, fill=False, linewidth=lw))

    draw_circle(0.98, "#4c1d95", lw=3.0)
    draw_circle(0.92, "#7c3aed", lw=2.5)
    draw_circle(0.72, "#a78bfa", lw=2.5)
    draw_circle(0.60, "#c4b5fd", lw=1.5)

    # サイン帯
    for i, label in enumerate(SIGN_LABELS):
        lons = np.linspace(i*30, (i+1)*30, 50)
        rads = np.deg2rad(180.0 + ((lons - asc) % 360))
        xs_o = 0.92 * np.cos(rads)
        ys_o = 0.92 * np.sin(rads)
        xs_i = 0.72 * np.cos(rads)
        ys_i = 0.72 * np.sin(rads)
        color = "#ede9fe" if i % 2 == 0 else "#ddd6fe"
        ax.fill(np.concatenate([xs_o, xs_i[::-1]]),
                np.concatenate([ys_o, ys_i[::-1]]), color=color, alpha=0.9)
        lx, ly = lon_to_xy(i*30+15, 0.86)
        ax.text(lx, ly, label, ha="center", va="center",
                fontsize=14, color="#4c1d95", fontweight="bold")

    # ハウス線
    for i, cusp in enumerate(houses):
        x0, y0 = lon_to_xy(cusp, 0.0)
        x1, y1 = lon_to_xy(cusp, 0.72)
        ax.plot([x0,x1],[y0,y1],
                color="#4c1d95" if i==0 else "#9ca3af",
                linewidth=2.5 if i==0 else 1.2)
        next_cusp = houses[(i+1)%12]
        diff = (next_cusp - cusp) % 360
        mid = (cusp + diff/2) % 360
        mx, my = lon_to_xy(mid, 0.36)
        ax.text(mx, my, str(i+1), ha="center", va="center",
                fontsize=14, color="#6b7280")

    # アスペクトライン
    aspect_defs = {
        "コンジャンクション":0,"トライン":120,"スクエア":90,
        "セクスタイル":60,"オポジション":180
    }
    pnames = list(natal_longitudes.keys())
    for i in range(len(pnames)):
        for j in range(i+1, len(pnames)):
            p1, p2 = pnames[i], pnames[j]
            d1, d2 = natal_longitudes[p1], natal_longitudes[p2]
            diff = abs(d1-d2) % 360
            if diff > 180: diff = 360-diff
            for asp_name, asp_angle in aspect_defs.items():
                if abs(diff-asp_angle) < 6:
                    style = ASPECT_STYLES[asp_name]
                    ax1, ay1 = lon_to_xy(d1, 0.60)
                    ax2, ay2 = lon_to_xy(d2, 0.60)
                    ax.plot([ax1,ax2],[ay1,ay2], color=style["color"],
                            linewidth=style["lw"], linestyle=style["ls"],
                            alpha=0.5, zorder=2)

    # 天体ドット
    dot_info = []
    for name in PLANET_ORDER:
        if name not in natal_longitudes:
            continue
        deg = natal_longitudes[name]
        color = PLANET_COLORS.get(name, "black")
        label = PLANET_LABELS.get(name, name)
        px, py = lon_to_xy(deg, 0.64)
        ax.plot(px, py, "o", color=color, markersize=12, zorder=5)
        rad = lon_to_rad(deg)
        dot_info.append({
            "deg": deg, "rad": rad,
            "color": color, "label": label,
            "px": px, "py": py
        })

    # ラベル：外側レーン（r=0.72〜0.92の間）に引き出し線付きで表示
    # 重なり解消はXY座標ベースで行う
    LABEL_R = 0.75

    # まず元の角度を取得
    adjusted = [item["rad"] for item in dot_info]

    # 重なり解消
    MIN_GAP = 0.20
    for _ in range(50):
        changed = False
        for i in range(len(adjusted)):
            for j in range(len(adjusted)):
                if i == j: continue
                diff = adjusted[i] - adjusted[j]
                if diff > np.pi: diff -= 2*np.pi
                elif diff < -np.pi: diff += 2*np.pi
                if 0 < abs(diff) < MIN_GAP:
                    push = (MIN_GAP - abs(diff)) / 2 + 0.008
                    adjusted[i] += push * np.sign(diff)
                    adjusted[j] -= push * np.sign(diff)
                    changed = True
        if not changed:
            break

    for i, item in enumerate(dot_info):
        lrad = adjusted[i]
        lx = LABEL_R * np.cos(lrad)
        ly = LABEL_R * np.sin(lrad)
        # 引き出し線
        ax.annotate("", xy=(lx, ly), xytext=(item["px"], item["py"]),
                    arrowprops=dict(arrowstyle="-", color=item["color"],
                                   lw=0.7, alpha=0.4))
        ax.text(lx, ly, item["label"],
                ha="center", va="center",
                fontsize=10, color=item["color"], fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                          edgecolor=item["color"], linewidth=0.8, alpha=0.95),
                zorder=6)

    # トランジット
    if transit_longitudes:
        for name, deg in transit_longitudes.items():
            tx, ty = lon_to_xy(deg, 0.85)
            ax.plot(tx, ty, "^", color="blue", markersize=8, alpha=0.6, zorder=4)

    # 凡例
    row1, row2 = [], []
    for i, name in enumerate(PLANET_ORDER):
        if name not in natal_longitudes:
            continue
        sign, d = split_sign_degree(natal_longitudes[name])
        sign_en = SIGN_SHORT.get(sign, sign[:3])
        label = PLANET_LABELS.get(name, name)
        entry = f"{label}:{sign_en}{d:.0f}"
        if i < 5: row1.append(entry)
        else: row2.append(entry)

    ax.text(0, -1.12, "  |  ".join(row1), ha="center", va="center",
            fontsize=13, color="#1a202c", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#7c3aed", linewidth=2.0))
    ax.text(0, -1.26, "  |  ".join(row2), ha="center", va="center",
            fontsize=13, color="#1a202c", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#7c3aed", linewidth=2.0))

    return fig
