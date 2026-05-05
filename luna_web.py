import streamlit as st

st.markdown("""
<style>
.block-container {
    padding-top: 260px !important;
}
</style>
""", unsafe_allow_html=True)

import datetime
import random
import io  # 追加：ダウンロード用

import numpy as np
import matplotlib.pyplot as plt

import datetime

from datetime import timedelta

#import datetime

#import datetime as dt

# ---------- ページ設定 ----------
st.set_page_config(
    page_title="Luna 占星術 Web版",
    page_icon="🌙",
    layout="centered"
)

st.markdown("""
<style>
@media (max-width: 600px) {
    .block-container {
        padding-top: 120px !important;
    }
}
</style>
""", unsafe_allow_html=True)

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

#st.markdown("## 🔍 生年月日入力")

#birth_date = st.date_input("生年月日を選択")
#birth_time = st.time_input("出生時間", value=datetime.time(12, 0))
#birthday = birth_date

from skyfield.api import load
from skyfield.framelib import ecliptic_frame

#st.markdown("<div class='luna-header'>🌙 ✨</div>", unsafe_allow_html=True)


# ---------- スタイル ----------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #fdf4ff 0%, #f5f3ff 20%, #8a2be2 100%);
}

.block-container {
    padding-top: 80px !important;
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
#def get_sun_message(sun_sign):
#    if sun_sign == "双子座":
#        return (
#            "あなたは『知識をつなぐ魂』。<br>"
#            "好奇心と観察力で世界を読み解き、人と人・過去と未来を結ぶ存在です。<br>"
#            "学び・言葉・探究は、あなたの宿命であり才能です。"
#        )
#    else:
#        return "あなたの太陽は、あなたらしい生き方と使命を示しています。"

def get_sun_message(sign):
    messages = {
        "牡羊座": "行動力と情熱で人生を切り開くタイプです。",
        "牡牛座": "安定と豊かさを大切にする現実的な魂です。",
        "双子座": "知識をつなぐ魂。好奇心と観察力で世界を読み解き、人と人・過去と未来を結ぶ存在。学び・言葉・探究は、あなたの宿命であり才能です。",
        "蟹座": "感情と共感を大切にする優しい魂です。",
        "獅子座": "自分らしさを表現する華やかな存在です。",
        "乙女座": "分析力と繊細さで物事を整える力があります。",
        "天秤座": "調和と美を大切にするバランサーです。",
        "蠍座": "深い洞察と集中力を持つ探究者です。",
        "射手座": "自由と成長を求める冒険者です。",
        "山羊座": "努力と責任で成功を築く現実主義者です。",
        "水瓶座": "独自性と未来志向の改革者です。",
        "魚座": "感性と優しさにあふれる癒しの存在です"
    }
    return messages.get(sign, "あなたの太陽はあなたらしさを示しています。")

#def get_moon_message(moon_sign):
#    if "牡牛座" in moon_sign:
#        return (
#            "あなたの心は『安定・美・心地よさ』を強く求めます。<br>"
#            "本物の美、安心できる場所、あたたかい人間関係があなたを整えます。"
#        )
#    else:
#        return "あなたの心はとても繊細で豊か。安心できる環境が才能を引き出します。"
    
def get_moon_message(sign):
    messages = {
        "牡羊座": "感情はストレートで行動的です。",
        "牡牛座": "安心・安定・心地よさを強く求めます。本物の美、安心できる場所、あたたかい人間関係があなたを整えます。",
        "双子座": "感情も言葉で整理するタイプです。",
        "蟹座": "共感力が高く、家庭的です。",
        "獅子座": "愛されたい気持ちが強いです。",
        "乙女座": "繊細で気配り上手です。",
        "天秤座": "人との関係性で安心します。",
        "蠍座": "感情が深く強いです。",
        "射手座": "自由な感情を持っています。",
        "山羊座": "感情をコントロールするタイプです。",
        "水瓶座": "クールで距離感を大切にします。",
        "魚座": "とても優しく感受性豊かです"
    }
    return messages.get(sign, "あなたの心は繊細で豊かです。")


def get_mercury_message(sign):
    messages = {
        "牡羊座": "直感的でスピーディーな思考。思ったことをすぐ言葉にします。",
        "牡牛座": "じっくり考えるタイプ。現実的で安定した判断をします。",
        "双子座": "情報収集が得意。会話力が高く、頭の回転が早いです。",
        "蟹座": "感情ベースで考える傾向。共感力が高いです。",
        "獅子座": "自分の考えに自信があり、表現力が豊かです。",
        "乙女座": "分析力が高く、細かいところまでよく気づきます。",
        "天秤座": "バランス重視で、客観的に考えることができます。",
        "蠍座": "深く掘り下げる思考。洞察力が鋭いです。",
        "射手座": "自由で広い視野を持つ思考。哲学的です。",
        "山羊座": "現実的で計画的な思考。結果を重視します。",
        "水瓶座": "独創的でユニークな発想。常識にとらわれません。",
        "魚座": "感覚的で直感重視。イメージ力が豊かです"
    }
    return messages.get(sign, "")

def get_venus_message(sign):
    messages = {
        "牡羊座": "恋愛は直感型。好きになったら一直線で情熱的です。",
        "牡牛座": "安定した愛を求めます。五感や心地よさを大切にします。",
        "双子座": "会話が楽しい恋愛を好みます。軽やかでフレンドリーです。",
        "蟹座": "愛情深く、守る恋愛。家庭的で安心感を重視します。",
        "獅子座": "ドラマチックな恋愛を好み、愛情表現が豊かです。",
        "乙女座": "細やかな気配りで愛を示すタイプ。誠実で慎重です。",
        "天秤座": "バランスの良い恋愛。美しさや調和を重視します。",
        "蠍座": "深く強い愛。絆や一体感をとても大切にします。",
        "射手座": "自由な恋愛。束縛を嫌い、楽しい関係を好みます。",
        "山羊座": "現実的で堅実な恋愛。信頼と継続を重視します。",
        "水瓶座": "友達のような恋愛。個性と距離感を大切にします。",
        "魚座": "ロマンチックで優しい愛。感受性が豊かです。"
    }
    return messages.get(sign, "")

def get_mars_message(sign):
    messages = {
        "牡羊座": "行動が早く、エネルギッシュ。思い立ったらすぐ動きます。",
        "牡牛座": "粘り強く着実に行動。マイペースで安定しています。",
        "双子座": "動きが軽やかで柔軟。複数のことを同時に進めます。",
        "蟹座": "感情で動くタイプ。守るために強くなります。",
        "獅子座": "自信に満ちた行動力。目立つことを恐れません。",
        "乙女座": "計画的で正確な行動。無駄を嫌います。",
        "天秤座": "バランスを見て動くタイプ。争いを避けます。",
        "蠍座": "集中力が強く、一点突破型。とことんやり抜きます。",
        "射手座": "自由に動き回るタイプ。冒険心があります。",
        "山羊座": "目的達成型。コツコツと確実に進めます。",
        "水瓶座": "独自のやり方で動く。常識にとらわれません。",
        "魚座": "流れに乗るタイプ。感覚的に動きます。"
    }
    return messages.get(sign, "")

def get_jupiter_message(sign):
    messages = {
        "牡羊座": "チャレンジすることで運が広がります。自分から動くほどチャンスが増えます。",
        "牡牛座": "安定と積み重ねの中で運が育ちます。お金や現実的な価値で成功しやすいです。",
        "双子座": "情報・会話・学びで運が広がります。人との交流がチャンスを呼びます。",
        "蟹座": "家庭・安心できる場所で運が育ちます。人を守ることで発展します。",
        "獅子座": "自己表現・目立つことで運が広がります。自信を持つほど成功します。",
        "乙女座": "細かい努力や分析で運が伸びます。実務能力が成功につながります。",
        "天秤座": "人との関係で運が広がります。パートナーシップが鍵になります。",
        "蠍座": "深い関係や集中力で運が広がります。本気で取り組むほど大きく伸びます。",
        "射手座": "自由・冒険・学びで運が拡大します。海外や哲学とも縁があります。",
        "山羊座": "社会的成功・努力で運が開きます。時間をかけるほど大きく成長します。",
        "水瓶座": "独自性・未来志向で運が広がります。人と違うことが強みになります。",
        "魚座": "感性・優しさ・直感で運が広がります。見えない世界との縁も強いです。"
    }
    return messages.get(sign, "")

def get_saturn_message(sign):
    messages = {
        "牡羊座": "行動することにブレーキを感じやすいですが、乗り越えると強い実行力になります。",
        "牡牛座": "お金や安定に対して課題を感じやすいですが、積み重ねで大きな力になります。",
        "双子座": "言葉やコミュニケーションに慎重さが出ますが、深い思考力が育ちます。",
        "蟹座": "感情や安心感に課題を感じやすいですが、精神的な強さを得られます。",
        "獅子座": "自己表現にブレーキがかかりますが、乗り越えると本物の自信になります。",
        "乙女座": "完璧主義になりやすいですが、精度の高い能力として発揮されます。",
        "天秤座": "対人関係で悩みやすいですが、バランス感覚が鍛えられます。",
        "蠍座": "深い感情や執着が課題ですが、圧倒的な集中力に変わります。",
        "射手座": "自由と責任のバランスが課題ですが、哲学的な深さを得ます。",
        "山羊座": "責任が重く感じやすいですが、大きな成功をつかむ力があります。",
        "水瓶座": "個性を出すことに葛藤がありますが、独自の価値を確立できます。",
        "魚座": "曖昧さに不安を感じますが、精神的な強さと優しさが育ちます。"
    }
    return messages.get(sign, "")

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

def get_aspects(planets):
    aspects = []
    aspect_defs = {
        "コンジャンクション": 0,
        "セクスタイル": 60,
        "スクエア": 90,
        "トライン": 120,
        "オポジション": 180
    }

    for p1_name, p1_deg in planets.items():
        for p2_name, p2_deg in planets.items():
            if p1_name == p2_name:
                continue

            diff = abs(p1_deg - p2_deg)
            if diff > 180:
                diff = 360 - diff

    for p1_name, p1_deg in planets.items():
        for p2_name, p2_deg in planets.items():

            # ★これを入れる（ここ！）
            if p1_name >= p2_name:
                continue

            diff = abs(p1_deg - p2_deg)
            if diff > 180:
                diff = 360 - diff

            for aspect_name, angle in aspect_defs.items():
                if abs(diff - angle) < 5:
                    aspects.append({
                        "p1": p1_name,
                        "p2": p2_name,
                        "type": aspect_name
                    })

    return aspects

def get_aspect_message(p1, p2, aspect):
    if p1 == "火星" and p2 == "金星" and aspect == "セクスタイル":
        return "行動と愛情のバランスが良く、自然体で人と関われる魅力があります。"

    return "この配置はあなたに独自の個性と可能性を与えています。"

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
    for i, cusp in enumerate(houses):
        angle_rad = np.deg2rad(cusp)

        ax.plot([angle_rad, angle_rad], [0.0, 0.7],
                linewidth=0.7, color="#9ca3af")

        label_angle = np.deg2rad(cusp + 15)
        ax.text(label_angle, 0.15, str(i+1),
                ha='center', va='center', fontsize=10, color="#111827")

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

# ---------- ASC ----------
#import streamlit as st
import swisseph as swe

# ←ここに入れる！
def get_sign(deg):
    signs = ["牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座",
             "天秤座","蠍座","射手座","山羊座","水瓶座","魚座"]
    return signs[int(deg / 30)]

def get_asc_message(sign):
    messages = {
        "牡羊座": "第一印象はとても行動的で、思い立ったらすぐ動くタイプです。",
        "牡牛座": "落ち着いた雰囲気で、安心感を与える第一印象を持っています。",
        "双子座": "軽やかで話しやすく、知的な印象を与えます。",
        "蟹座": "優しく親しみやすく、安心感を与える存在です。",
        "獅子座": "明るく華やかで、人を惹きつける存在感があります。",
        "乙女座": "丁寧で落ち着いた、信頼感のある印象です。",
        "天秤座": "上品でバランス感覚があり、社交的な雰囲気です。",
        "蠍座": "静かながらも強い意志を感じさせる印象です。",
        "射手座": "自由で伸びやか、明るく前向きな印象を与えます。",
        "山羊座": "しっかりしていて、責任感のある印象を持たれます。",
        "水瓶座": "個性的でユニーク、独自の空気感を持っています。",
        "魚座": "柔らかく優しい、感受性豊かな印象です。"
    }
    return messages.get(sign, "")


# ---------- タブ構成 ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "🌙 ネイタル",
    "🌞 トランジット",
    "💞 相性占い",
    "🃏 カードメッセージ"
])


# === タブ1：ネイタル ===
with tab1:
    st.write("テスト：ここからネイタル")

    # 入力
    #birthday = st.date_input("生年月日")

    # 仮の時間
    birth_hour = 12
    birth_minute = 0

    # 変換
    # year = default_date.year
    # month = default_date.month
    # day = default_date.day
    # hour = default_hour + default_min / 60


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
            #houses = get_equal_houses()

            # ★ここに追加
            #year = birthday.year
            #month = birthday.month
            #day = birthday.day
            #hour = birth_hour + birth_minute / 60.0 - 9

            #jd = swe.julday(year, month, day, hour)

                     


            #from datetime import datetime, timedelta

            # 入力 → JST
            # dt_local = datetime(
            dt_local = datetime.datetime(
                birthday.year,
                birthday.month,
                birthday.day,
                int(birth_hour),
                int(birth_minute)
            )

            # JST → UTC（必須）
            dt_utc = dt_local - timedelta(hours=9)

            # ★ここが毎回新しく計算される
            jd = swe.julday(
                dt_utc.year,
                dt_utc.month,
                dt_utc.day,
                dt_utc.hour + dt_utc.minute / 60.0
            )

            lat = 35.68
            lon = 139.76

            houses, ascmc = swe.houses(jd, lat, lon, b'P')
            asc = ascmc[0]

            #st.write("DEBUG ASC:", asc)
            asc_deg = asc % 30

            asc_sign = get_sign(asc)


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

            # ★ここだけ使う（birthday に統一）
            year = birthday.year
            month = birthday.month
            day = birthday.day
            hour = birth_hour + birth_minute / 60

            # jd = swe.julday(year, month, day, hour)

            lat = 35.68
            lon = 139.76

            houses, ascmc = swe.houses(jd, lat, lon, b'P')
            asc = ascmc[0]

            asc_sign = get_sign(asc)


        for i, cusp in enumerate(houses):
            house_num = i + 1
            sign = get_sign(cusp)
            msg = get_house_message(house_num, sign)

            st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)                  

        st.markdown("### 🌙 第一印象（ASC）")
        #st.write(f"{asc_sign} {asc:.2f}°")
        st.write(f"{asc_sign} {asc_deg:.2f}°")
        st.write(get_asc_message(asc_sign))    

        # 🌞 太陽（本質）
        sun = swe.calc_ut(jd, swe.SUN)[0][0]
        sun_sign = get_sign(sun)

        st.markdown("## ☀ 太陽（本質）")
        st.write(f"{sun_sign} {sun:.2f}°")
        st.write(get_sun_message(sun_sign))

        # 🌙 月（感情）
        moon = swe.calc_ut(jd, swe.MOON)[0][0]
        moon_sign = get_sign(moon)

        st.markdown("## 🌙 月（感情）")
        st.write(f"{moon_sign} {moon:.2f}°")     
        st.write(get_moon_message(moon_sign)) 

        # 水星
        mercury = swe.calc_ut(jd, swe.MERCURY)[0][0]
        mercury_sign = get_sign(mercury)

        st.markdown("## ☿ 水星（思考）")
        st.write(f"{mercury_sign} {mercury:.2f}°")
        st.write(get_mercury_message(mercury_sign))


        # 金星
        venus = swe.calc_ut(jd, swe.VENUS)[0][0]
        venus_sign = get_sign(venus)

        st.markdown("## ♀ 金星（愛・好み）")
        st.write(f"{venus_sign} {venus:.2f}°")
        st.write(get_venus_message(venus_sign))


        # 火星
        mars = swe.calc_ut(jd, swe.MARS)[0][0]
        mars_sign = get_sign(mars)

        st.markdown("## ♂ 火星（行動）")
        st.write(f"{mars_sign} {mars:.2f}°")
        st.write(get_mars_message(mars_sign))   


        # 木星
        jupiter = swe.calc_ut(jd, swe.JUPITER)[0][0]
        jupiter_sign = get_sign(jupiter)

        st.markdown("## ♃ 木星（拡大・発展）")
        st.write(f"{jupiter_sign} {jupiter:.2f}°")
        st.write(get_planet_message("木星"))

        # 土星
        saturn = swe.calc_ut(jd, swe.SATURN)[0][0]
        saturn_sign = get_sign(saturn)

        st.markdown("## ♄ 土星（課題・責任）")
        st.write(f"{saturn_sign} {saturn:.2f}°")
        st.write(get_planet_message("土星"))   

   # ←ここに追加
        planets = {
            "太陽": sun,
            "月": moon,
            "水星": mercury,
            "金星": venus,
            "火星": mars
        }       

        st.markdown("## 🔷 アスペクト（関係性）")

        aspects = get_aspects(planets)

        for a in aspects:
            st.write(f"{a['p1']} × {a['p2']} ：{a['type']}")
            msg = get_aspect_message(a["p1"], a["p2"], a["type"])

            msg = get_aspect_message(a["p1"], a["p2"], a["type"])
            st.write(msg)     

        st.markdown("## 🌟 性格まとめ")

        summary = []

        summary.append(get_sun_message(sun_sign))
        summary.append(get_moon_message(moon_sign))
        summary.append(get_venus_message(venus_sign))
        summary.append(get_mars_message(mars_sign))

        for a in aspects:
            summary.append(get_aspect_message(a["p1"], a["p2"], a["type"]))

        for s in summary:
            st.write("・" + s)           


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
        #value=datetime.date.today(),
        value=datetime.datetime.now().date(),
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








