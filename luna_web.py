import datetime
import random
import io  # 追加：ダウンロード用

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

#st.markdown("""
#<style>
#.luna-header {
#    text-align: center;
#    font-size: 16px;
#    padding-top: 0px;
#    margin-top: 0px;
#    line-height: 1;
#}
#</style>
#""", unsafe_allow_html=True)

from skyfield.api import load
from skyfield.framelib import ecliptic_frame

#st.markdown("<div class='luna-header'>🌙 ✨</div>", unsafe_allow_html=True)

# ---------- ページ設定 ----------
st.set_page_config(
    page_title="Luna 占星術 Web版",
    page_icon="🌙",
    layout="centered"
)

# ---------- スタイル ----------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #fdf4ff 0%, #f5f3ff 20%, #8a2be2 100%);
}

.block-container {
    padding-top: 3rem;
}
            
/* タイトルの白い帯 */
.luna-header-wrap {
    background: rgba(255, 255, 255, 0.92);
    border-radius: 18px;
    padding: 10px 20px 14px 20px;
    display: inline-block;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
}
.luna-title {
    font-size: 30px !important;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.24em;
    color: #2b1b4b;
    margin-bottom: 4px;
}
.luna-caption {
    text-align: center;
    color: #4b5563;
    font-size: 13px;
}

/* メインカード */
.luna-card {
    background: rgba(255, 255, 255, 0.97);
    border-radius: 24px;
    padding: 26px 30px;
    border: 1px solid #d8b4fe;
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.25);
}

/* セクション見出し */
.luna-section-title {
    font-size: 18px;
    margin-top: 20px;
    margin-bottom: 10px;
    color: #2b1b4b;
    border-left: 4px solid #d8b4fe;
    padding-left: 10px;
    font-weight: 600;
}

/* メッセージ箱 */
.luna-message {
    background: #f9f5ff;
    padding: 14px 18px;
    border-radius: 14px;
    margin: 10px 0 18px 0;
    color: #1f1437;
    line-height: 1.7em;
    border: 1px solid #a855f7;
}

/* 入力欄 */
.stTextInput input, .stDateInput input, .stNumberInput input {
    background: #ffffff !important;
    border: 1px solid #c4b5fd !important;
    border-radius: 8px !important;
    color: #111827 !important;
    padding: 6px 8px !important;
}

/* カード風ボックス */
.luna-card-box {
    background: #ffffff;
    border-radius: 16px;
    border: 2px solid #a855f7;
    padding: 16px 18px;
    margin-top: 10px;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
}

@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
    }

    .luna-card {
        max-width: 100% !important;
        padding: 14px 14px !important;
    }

    .luna-title {
        font-size: 30px !important;
        letter-spacing: 0.18em !important;
    }
}

button[kind="primary"] {
    width: 100% !important;
    height: 48px !important;
    font-size: 16px !important;
    border-radius: 10px !important;
}
            
button[kind="primary"] {
    margin-bottom: 12px !important;
}            

button[kind="primary"] {
    border-radius: 999px !important;
}

button[kind="secondary"] {
    border-radius: 999px !important;
}                                                                     
</style>
""", unsafe_allow_html=True)

# ---------- 天文準備 ----------
TS = load.timescale()
EPH = load("de421.bsp")

SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]

ELEMENTS = {
    "牡羊座": "火", "獅子座": "火", "射手座": "火",
    "牡牛座": "地", "乙女座": "地", "山羊座": "地",
    "双子座": "風", "天秤座": "風", "水瓶座": "風",
    "蟹座": "水", "蠍座": "水", "魚座": "水"
}

# ---------- ヘルパー：度数 → サイン＋度 ----------
def split_sign_degree(lon_deg: float):
    lon_norm = lon_deg % 360.0
    index = int(lon_norm // 30)
    degree = lon_norm % 30
    return SIGNS[index], degree

# ---------- ローカル時刻 → UTC（SkyfieldのTime） ----------
def make_ts_from_local(date_obj: datetime.date, hour: int, minute: int, tz_offset_hours: int):
    local_dt = datetime.datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)
    utc_dt = local_dt - datetime.timedelta(hours=tz_offset_hours)
    return TS.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)

# ---------- 太陽・月・惑星情報（Timeを渡す） ----------
def get_sun_info(t):
    earth = EPH["earth"]
    sun_pos = earth.at(t).observe(EPH["sun"])
    _, lon, _ = sun_pos.frame_latlon(ecliptic_frame)
    lon_deg = lon.degrees
    sign, deg = split_sign_degree(lon_deg)
    return sign, deg, lon_deg % 360.0

def get_moon_info(t):
    earth = EPH["earth"]
    moon_pos = earth.at(t).observe(EPH["moon"])
    _, lon, _ = moon_pos.frame_latlon(ecliptic_frame)
    lon_deg = lon.degrees
    sign, deg = split_sign_degree(lon_deg)
    return sign, deg, lon_deg % 360.0

def get_planet_signs_ts(t):
    earth = EPH["earth"]
    planet_keys = {
        "水星": "mercury",
        "金星": "venus",
        "火星": "mars",
        "木星": "jupiter barycenter",
        "土星": "saturn barycenter",
        "天王星": "uranus barycenter",
        "海王星": "neptune barycenter",
        "冥王星": "pluto barycenter"
    }

    result = {}
    for name, key in planet_keys.items():
        pos = earth.at(t).observe(EPH[key])
        _, lon, _ = pos.frame_latlon(ecliptic_frame)
        lon_deg = lon.degrees
        sign, deg = split_sign_degree(lon_deg)
        result[name] = f"{sign} {deg:.2f}°"
    return result

def get_body_longitudes_ts(t):
    earth = EPH["earth"]
    bodies = {}

    # 太陽
    sun_pos = earth.at(t).observe(EPH["sun"])
    _, sun_lon, _ = sun_pos.frame_latlon(ecliptic_frame)
    bodies["太陽"] = sun_lon.degrees % 360.0

    # 月
    moon_pos = earth.at(t).observe(EPH["moon"])
    _, moon_lon, _ = moon_pos.frame_latlon(ecliptic_frame)
    bodies["月"] = moon_lon.degrees % 360.0

    # 惑星
    planet_keys = {
        "水星": "mercury",
        "金星": "venus",
        "火星": "mars",
        "木星": "jupiter barycenter",
        "土星": "saturn barycenter",
        "天王星": "uranus barycenter",
        "海王星": "neptune barycenter",
        "冥王星": "pluto barycenter"
    }
    for name, key in planet_keys.items():
        pos = earth.at(t).observe(EPH[key])
        _, lon, _ = pos.frame_latlon(ecliptic_frame)
        bodies[name] = lon.degrees % 360.0

    return bodies

# ---------- ハウス（簡易イコールハウス） ----------
def get_equal_houses():
    houses = {}
    for i in range(12):
        cusp_deg = i * 30.0
        sign_name = SIGNS[i]
        houses[i + 1] = {
            "cusp_deg": cusp_deg,
            "sign": sign_name
        }
    return houses

# ---------- メッセージ系 ----------
def get_sun_message(sun_sign):
    if sun_sign == "双子座":
        return (
            "あなたは『知識をつなぐ魂』。<br>"
            "好奇心と観察力で世界を読み解き、人と人・過去と未来を結ぶ存在です。<br>"
            "学び・言葉・探究は、あなたの宿命であり才能です。"
        )
    else:
        return "あなたの太陽は、あなたらしい生き方と使命を示しています。"

def get_moon_message(moon_sign):
    if "牡牛座" in moon_sign:
        return (
            "あなたの心は『安定・美・心地よさ』を強く求めます。<br>"
            "本物の美、安心できる場所、あたたかい人間関係があなたを整えます。"
        )
    else:
        return "あなたの心はとても繊細で豊か。安心できる環境が才能を引き出します。"

def get_planet_message(name):
    messages = {
        "水星": "思考・言葉・学び方を表します。",
        "金星": "愛情表現・美意識・人間関係の心地よさを表します。",
        "火星": "行動力・やる気・怒り方のクセを表します。",
        "木星": "拡大・チャンス・どこで運が広がるかを示します。",
        "土星": "課題・責任・乗り越えると大きな力になるポイントです。",
        "天王星": "個性・革命・人と違う部分の輝きです。",
        "海王星": "直感・夢・スピリチュアルな感性を表します。",
        "冥王星": "魂レベルの変容・大きな転機を表します。",
    }
    return messages.get(name, "")

def get_house_message(house_num, sign):
    base = f"{house_num}ハウス（{sign}）："
    table = {
        1: "自分自身・性格・第一印象の領域です。",
        2: "お金・才能・所有・価値観の領域です。",
        3: "学び・コミュニケーション・兄弟姉妹の領域です。",
        4: "家・家族・ルーツ・安心できる場所の領域です。",
        5: "恋愛・創造性・趣味・自己表現の領域です。",
        6: "仕事・健康・日々の習慣の領域です。",
        7: "パートナーシップ・契約・対人関係の領域です。",
        8: "心の深い結びつき・共有資産・変容の領域です。",
        9: "哲学・専門的学び・海外・精神性の領域です。",
        10: "社会的地位・キャリア・使命の領域です。",
        11: "仲間・コミュニティ・未来のビジョンの領域です。",
        12: "潜在意識・癒し・見えない世界の領域です。",
    }
    return base + table.get(house_num, "")

def simple_compare_message(natal_text, transit_text, label):
    if natal_text == transit_text:
        return f"{label}はネイタル・トランジットともに『{natal_text}』。<br>自分らしさと、その日の流れが重なりやすい配置です。"
    else:
        return (
            f"{label}のネイタルは『{natal_text}』、トランジットは『{transit_text}』。<br>"
            "ふだんの傾向に、期間限定で別のテーマが重なっているタイミングです。"
        )

# ---------- 円形ホロスコープ（ネイタル＋トランジット2重） ----------
def plot_horoscope(natal_longitudes, houses, transit_longitudes=None):
    SIGN_LABELS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    PLANET_LABELS = {
        "太陽": "Sun",
        "月": "Moon",
        "水星": "Me",
        "金星": "Ve",
        "火星": "Ma",
        "木星": "Jup",
        "土星": "Sat",
        "天王星": "Ur",
        "海王星": "Ne",
        "冥王星": "Pl",
    }

    fig = plt.figure(figsize=(5.6, 5.6))
    ax = fig.add_subplot(111, polar=True)

    ax.set_facecolor("#f5f3ff")

    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)

    ax.set_rlim(0, 1.0)
    ax.set_yticklabels([])

    # サイン帯
    for i, label in enumerate(SIGN_LABELS):
        start_deg = i * 30
        end_deg = start_deg + 30
        theta = np.deg2rad(np.linspace(start_deg, end_deg, 50))
        r_inner = 0.7
        r_outer = 0.9
        color = "#ede9fe" if i % 2 == 0 else "#e0e7ff"
        ax.fill_between(theta, r_inner, r_outer, color=color, alpha=1.0)

        label_angle = np.deg2rad(start_deg + 15)
        ax.text(label_angle, 0.8, label,
                ha="center", va="center", fontsize=10, color="#111827")

    # 外周円
    circle_theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(circle_theta, [0.9] * len(circle_theta),
            color="#7c3aed", linewidth=1.2)

    # ハウス線＆番号
    for num, info in houses.items():
        cusp_deg = info["cusp_deg"]
        angle_rad = np.deg2rad(cusp_deg)
        ax.plot([angle_rad, angle_rad], [0.0, 0.7],
                linewidth=0.7, color="#9ca3af")

        label_angle = np.deg2rad(cusp_deg + 15)
        ax.text(label_angle, 0.15, str(num),
                ha="center", va="center", fontsize=10, color="#111827")

    # ① ネイタル（内側）
    for name, deg in natal_longitudes.items():
        angle = np.deg2rad(deg)

        if name == "太陽":
            r = 0.72
            ax.scatter(angle, r, s=90, marker="o", color="#f97316", zorder=3)
        elif name == "月":
            r = 0.68
            ax.scatter(angle, r, s=80, marker="D", color="#4b5563", zorder=3)
        else:
            r = 0.64
            ax.scatter(angle, r, s=65, marker="o", color="#111827", zorder=3)

        label = PLANET_LABELS.get(name, name)
        ax.text(angle, r + 0.08, label,
                ha="center", va="center", fontsize=9, color="#111827")

    # ② トランジット（外側・薄い色）
    if transit_longitudes is not None:
        for name, deg in transit_longitudes.items():
            angle = np.deg2rad(deg)
            r = 0.82
            ax.scatter(angle, r, s=55, marker="^", color="#60a5fa", alpha=0.8, zorder=2)

            label = PLANET_LABELS.get(name, name)
            ax.text(angle, r + 0.06, label,
                    ha="center", va="center", fontsize=8, color="#1d4ed8", alpha=0.9)

    ax.set_xticklabels([])
    ax.grid(False)
    plt.tight_layout(pad=0.1)
    return fig

# ---------- カード ----------
from pathlib import Path

ASSET_DIR = Path(__file__).parent / "assets" / "tarot"

CARDS = [
    ("愚者", "自由、冒険、はじまり", str(ASSET_DIR / "00_fool.png")),
    ("魔術師", "創造、可能性、スタート", str(ASSET_DIR / "01_magician.png")),
    ("女教皇", "直感、知性、内省", str(ASSET_DIR / "02_high_priestess.png")),
    ("女帝", "愛、豊かさ、実り", str(ASSET_DIR / "03_empress.png")),
    ("星", "希望、インスピレーション", str(ASSET_DIR / "17_star.png")),
]

import random

def draw_card():
    # CARDS は (name, msg, img_path) のタプル想定
    return random.choice(CARDS)


# ---------- 相性 ----------
def get_element(sign):
    return ELEMENTS.get(sign, None)

def compatibility_message(sun1, sun2, moon1, moon2, name1="Aさん", name2="Bさん"):
    e1 = get_element(sun1)
    e2 = get_element(sun2)

    base = f"{name1}（太陽{sun1}）と{name2}（太陽{sun2}）の関係性は、<br>"

    if e1 == e2 and e1 is not None:
        msg = "同じエレメント同士。基本的な感覚やテンポが似ていて、自然体でいられる相性です。"
    elif {e1, e2} == {"火", "風"}:
        msg = "火と風の組み合わせ。勢いとアイデアが噛み合う、刺激的で前向きな相性です。"
    elif {e1, e2} == {"地", "水"}:
        msg = "地と水の組み合わせ。安心感や現実性、情の深さを育てやすい、落ち着いた相性です。"
    elif {e1, e2} == {"火", "水"}:
        msg = "火と水の組み合わせ。情熱と感情が揺れやすく、ドラマチックになりやすい相性です。"
    elif {e1, e2} == {"風", "地"}:
        msg = "風と地の組み合わせ。考え方と現実感覚がすれ違いやすい分、お互いを補い合える相性です。"
    else:
        msg = "違うタイプ同士。最初は「違い」を感じますが、理解し合えれば学び合う関係になれます。"

    moon_part = f"<br><br>月の組み合わせとしては、{name1}の月は{moon1}、{name2}の月は{moon2}。<br>"
    moon_part += "感情面・安心感のポイントを大切にすると、関係性がより穏やかになります。"

    return base + msg + moon_part

# ---------- タイトル ----------
st.markdown(
    "<div style='text-align:center; margin-top:16px; margin-bottom:12px;'>"
    "<div class='luna-header-wrap'>"
    "<div class='luna-title'>Luna 占星術</div>"
    "<div class='luna-caption'>出生時刻対応・トランジット対応  Luna-compass</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True
)

# ---------- タブ構成 ----------
# tab1, tab2, tab3 = st.tabs(["🔮 ネイタル", "トランジット","💞 相性占い", "🃏 カードメッセージ"])
tab1, tab2, tab3, tab4 = st.tabs([
    "🌙 ネイタル",
    "🌞 トランジット",
    "💞 相性占い",
    "🃏 カードメッセージ"
])


# === タブ1：ネイタル ===
with tab1:

    st.markdown("""
    <style>
    .luna-card {
        max-width: 820px;
        margin: 0 auto 24px auto;
        padding: 18px 22px;
        border-radius: 14px;
        background: rgba(255,255,255,0.75);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        backdrop-filter: blur(6px);
    }
    .luna-section-title {
        font-weight: 600;
        font-size: 18px;
        margin: 6px 0 14px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='luna-section-title'>👤 基本情報</div>", unsafe_allow_html=True)
    #st.markdown("<div class='luna-section-title'>🔎 基本情報を入力</div>", unsafe_allow_html=True)

    mode = st.radio(
        "自分を占う",
        ("自分を占う", "別の人を占う"),
        key="mode_natal",
        help="ご自身か、他の人をを選んでください。"
    )

    if mode == "自分（Luna）を占う":
        default_name = "Luna"
        default_date = datetime.date(1968, 5, 27)
        default_hour = 0
        default_min = 0
    else:
        default_name = ""
        default_date = datetime.date(1990, 1, 1)
        default_hour = 12
        default_min = 0


    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("お名前", value=default_name, key="name_natal",
        help="ニックネームでもOKです"
    )

    with col2:
        birthday = st.date_input(
            "生年月日（ネイタル）",
            value=default_date,
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            key="birthday_natal",
            help="出生図を作るために使います"
        )    
  
    st.markdown("<br>", unsafe_allow_html=True)       
    st.markdown("<div class='luna-section-title'>⏰ 出生時間</div>", unsafe_allow_html=True)

    col_time1, col_time2 = st.columns(2)

    with col_time1:
        birth_hour = st.number_input("時", min_value=0, max_value=23,
        help="分からなければそのままでOK"
    )    

    with col_time2:
        birth_minute = st.number_input("分", min_value=0, max_value=59)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='luna-section-title'>🌍 今日の運気</div>", unsafe_allow_html=True)

    tz_label = st.radio(
        "出生地のタイムゾーン",
        ("日本（JST = UTC+9）", "世界時で計算（UTC・よく分からない場合）"),
        help="海外出生の場合のみ変更してください"
    )
    tz_offset = 9 if tz_label.startswith("日本") else 0

    transit_date = st.date_input(
        "トランジットを見る日（今日・気になる日など）",
        value=datetime.date.today(),
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.date(2100, 12, 31),
        key="transit_date",
        help="今日や気になる日を選べます"
    )

    #st.markdown("---")

    #col_btn1, col_btn2 = st.columns(2)

    #with col_btn1:
    #    btn_natal = st.button("🌙 ネイタルを見る", key="btn_natal")

    #with col_btn2:
    #    btn_transit = st.button("✨ 今日の運気を見る", key="btn_transit")    

    st.markdown("<br>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        btn_natal = st.button("🌙 ネイタルを見る", use_container_width=True, type="primary")

    with col_btn2:
        btn_transit = st.button("✨ 今日の運気を見る", use_container_width=True)

    if btn_natal or btn_transit:
    # if st.button("🌙 ネイタル & トランジットを見る", key="single_chart"):
        # Time生成
        t_natal = make_ts_from_local(birthday, birth_hour, birth_minute, tz_offset)
        # トランジットは、その日の正午（現地時刻）で見る
        t_transit = make_ts_from_local(transit_date, 12, 0, tz_offset)

        # ネイタル
        if btn_natal:
            sun_sign, sun_deg, sun_lon = get_sun_info(t_natal)
            moon_sign, moon_deg, moon_lon = get_moon_info(t_natal)
            planets = get_planet_signs_ts(t_natal)
            natal_longs = get_body_longitudes_ts(t_natal)
            houses = get_equal_houses()

        # トランジット
        if btn_transit:
            t_sun_sign, t_sun_deg, t_sun_lon = get_sun_info(t_transit)
            t_moon_sign, t_moon_deg, t_moon_lon = get_moon_info(t_transit)
            trans_planets = get_planet_signs_ts(t_transit)
            transit_longs = get_body_longitudes_ts(t_transit)

        target_label = "あなた" if mode == "自分（Luna）を占う" else f"{name or 'この方'}"

        # 基本情報
        st.markdown("<div class='luna-section-title'>ネイタル（出生図）</div>", unsafe_allow_html=True)
        st.write("鑑定対象：", target_label)
        st.write("名前：", name)
        st.write("生年月日：", birthday)
        st.write("出生時刻：", f"{birth_hour:02d}:{birth_minute:02d}")
        st.write("タイムゾーン：", tz_label)

        sun_sign, sun_deg, sun_lon = get_sun_info(t_natal)
        moon_sign, moon_deg, moon_lon = get_moon_info(t_natal)

        sun_text = f"{sun_sign} {sun_deg:.2f}°"
        moon_text = f"{moon_sign} {moon_deg:.2f}°"

        st.write("太陽：", sun_text)
        st.markdown(
            f"<div class='luna-message'>{get_sun_message(sun_sign)}</div>",
            unsafe_allow_html=True
        )

        st.write("月　：", moon_text)
        st.markdown(
            f"<div class='luna-message'>{get_moon_message(moon_text)}</div>",
            unsafe_allow_html=True
        )

        # トランジット
        if btn_transit:
            st.markdown("<div class='luna-section-title'>トランジット（選択した日の星の配置）</div>", unsafe_allow_html=True)
            st.write("トランジット日：", transit_date)
            trans_sun_text = f"{t_sun_sign} {t_sun_deg:.2f}°"
            trans_moon_text = f"{t_moon_sign} {t_moon_deg:.2f}°"

            st.write("太陽（トランジット）：", trans_sun_text)
            st.write("月　（トランジット）：", trans_moon_text)

            comp_sun = simple_compare_message(sun_text, trans_sun_text, "太陽")
            comp_moon = simple_compare_message(moon_text, trans_moon_text, "月")
            st.markdown(f"<div class='luna-message'>{comp_sun}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='luna-message'>{comp_moon}</div>", unsafe_allow_html=True)

            st.markdown("#### 主要トランジット惑星（サイン＆度数）")
            for p in ["木星", "土星", "冥王星"]:
                if p in trans_planets:
                    st.write(f"{p}：{trans_planets[p]}")

        # 惑星メッセージ（ネイタル）
        if btn_natal:
            st.markdown("<div class='luna-section-title'>惑星からのメッセージ（ネイタル）</div>", unsafe_allow_html=True)
            for p, v in planets.items():
                st.write(f"{p}：{v}")
                msg = get_planet_message(p)
                if msg:
                    st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)

        # ハウス（ネイタル）
        if btn_natal:
            st.markdown("<div class='luna-section-title'>ハウス（象徴的イコールハウス・ネイタル）</div>", unsafe_allow_html=True)
            for num, info in houses.items():
                sign = info["sign"]
                msg = get_house_message(num, sign)
                st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)

        # 円形ホロ（ネイタル＋トランジット2重）
        if btn_natal:
            st.markdown("<div class='luna-section-title'>円形ホロスコープ（内側＝ネイタル／外側＝トランジット）</div>", unsafe_allow_html=True)
            fig = plot_horoscope(natal_longs, houses, {})
            st.pyplot(fig)

        # 🔽 ここから：画像ダウンロードボタン（追加分）
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)

            st.download_button(
                label="📥 ホロスコープ画像をダウンロード",
                data=buf,
                file_name="luna_horoscope.png",
                mime="image/png",
            )

        # テキスト一覧（ネイタル・トランジット）
    if btn_natal:
        st.markdown("#### 🔎 配置一覧（度数）")
        st.write("【ネイタル（出生）】")

        for name_body, deg in natal_longs.items():
            sign, d = split_sign_degree(deg)
            st.write(f"{name_body}: {sign} {d:.2f}°")

        # トランジット取得
        t_sun_sign, t_sun_deg, t_sun_lon = get_sun_info(t_transit)
        t_moon_sign, t_moon_deg, t_moon_lon = get_moon_info(t_transit)

        st.markdown("### 🌟 今日の影響")

        if sun_sign == t_sun_sign:
            st.write("今日はあなたの本質が強く出る日です。自然体でいられます。")

        else:
            st.write("今日は外からの刺激を受けやすい日です。柔軟に対応すると良いでしょう。")

        st.markdown("### 🌙 感情の流れ")

        if moon_sign == t_moon_sign:
            st.write("今日は感情が安定しやすく、安心して過ごせる日です。")

        else:
            st.write("今日は気持ちが揺れやすい日です。無理せず過ごしましょう。")    

        st.markdown("### 🔮 心と行動のバランス")

        if sun_sign == t_moon_sign:
            st.write("今日は『やりたいこと』と『気持ち』が一致しやすい日です。自然に行動できます。")

        elif moon_sign == t_sun_sign:
            st.write("今日は感情が行動に影響しやすい日です。直感を大切にすると良いでしょう。")

        else:
            st.write("今日は心と行動に少しズレが出やすい日です。無理せずバランスを取りましょう。")        

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# === タブ2：トランジット ===
with tab2:
    #st.markdown("<div class='luna-card'>", unsafe_allow_html=True)

    st.subheader("🌞 トランジット")

    transit_only_date = st.date_input(
        "トランジットを見る日",
        value=datetime.date.today(),
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.date(2100, 12, 31),
        key="transit_only_date"
    )

    if st.button("🌞 トランジットを見る", key="btn_transit_only"):
        t_transit = make_ts_from_local(transit_only_date, 12, 0, 9)

        t_sun_sign, t_sun_deg, t_sun_lon = get_sun_info(t_transit)
        t_moon_sign, t_moon_deg, t_moon_lon = get_moon_info(t_transit)
        trans_planets = get_planet_signs_ts(t_transit)
        transit_longs = get_body_longitudes_ts(t_transit)

        st.markdown("<div class='luna-section-title'>トランジット（選択した日の星の配置）</div>", unsafe_allow_html=True)
        st.write("トランジット日：", transit_only_date)
        st.write("太陽：", f"{t_sun_sign} {t_sun_deg:.2f}°")
        st.write("月　：", f"{t_moon_sign} {t_moon_deg:.2f}°")

        st.markdown("#### 🔎 配置一覧（度数）")
        for name_body, deg in transit_longs.items():
            sign, d = split_sign_degree(deg)
            st.write(f"{name_body}：{sign} {d:.2f}°")

    st.markdown("</div>", unsafe_allow_html=True)


# === タブ3：相性占い ===
with tab3:
    #st.markdown("<div class='luna-card'>", unsafe_allow_html=True)
    st.markdown("<div class='luna-section-title'>お二人の相性</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name1 = st.text_input("お相手1のお名前", value="Luna", key="compat_name1")
        bday1 = st.date_input(
            "お相手1の生年月日",
            key="bday1",
            value=datetime.date(1968, 5, 27),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today()
        )
    with col2:
        name2 = st.text_input("お相手2のお名前", value="", placeholder="お相手のお名前", key="compat_name2")
        bday2 = st.date_input(
            "お相手2の生年月日",
            key="bday2",
            value=datetime.date(1990, 1, 1),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today()
        )

    if st.button("💞 相性を見る", key="compat"):
        # 相性は簡易：日付の正午をJSTとして計算
        def get_signs_for_date(d: datetime.date):
            t = make_ts_from_local(d, 12, 0, 9)  # 日本時間前提
            sun_s, sun_d, _ = get_sun_info(t)
            moon_s, moon_d, _ = get_moon_info(t)
            return sun_s, moon_s

        sun1, moon1 = get_signs_for_date(bday1)
        sun2, moon2 = get_signs_for_date(bday2)

        disp1 = name1 or "Aさん"
        disp2 = name2 or "Bさん"

        st.write(f"{disp1}：太陽 {sun1}／月 {moon1}")
        st.write(f"{disp2}：太陽 {sun2}／月 {moon2}")

        comp = compatibility_message(sun1, sun2, moon1, moon2, disp1, disp2)
        st.markdown(f"<div class='luna-message'>{comp}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# === タブ4：カードメッセージ ===
with tab4:
    #st.markdown("<div class='luna-card'>", unsafe_allow_html=True)
    st.markdown("### 🔮 1枚カードメッセージ", unsafe_allow_html=True)

    if st.button("カードを1枚引く", key="card"):
        card_name, card_msg, card_img = draw_card()

        img_path = Path(card_img) if card_img else None

        if img_path and img_path.exists():
            col1, col2, col3 = st.columns([2, 3, 2])
            with col2:
                st.image(img_path.read_bytes(), width=350)
                st.markdown(f"### {card_name}")
                st.write(card_msg)
        else:
            st.caption("（画像がまだ未設定 or 見つかりません）")

        st.markdown(
            f"""
            <div class="luna-card-box">
                <div class="luna-subtitle">カード：{card_name}</div>
                <div style="margin-top:6px;color:#2b1b4b;">{card_msg}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)








