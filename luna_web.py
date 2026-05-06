import streamlit as st

# ---------- ページ設定 ----------
st.set_page_config(
    page_title="Luna 占星術 Web版",
    page_icon="🌙",
    layout="centered"
)

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

from pathlib import Path

# 👇ここに追加！！
st.markdown("""
<style>
.luna-card-box {
    background: linear-gradient(135deg, #fffaf0, #f6e9ff);
    padding: 20px;
    border-radius: 15px;
    border: 2px solid #d4b5ff;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    margin-top: 20px;
}

.luna-title {
    font-size: 18px;
    font-weight: bold;
    color: #5a2a83;
}

.luna-text {
    margin-top: 10px;
    color: #2b1b4b;
}
</style>
""", unsafe_allow_html=True)

#import datetime

#import datetime as dt

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
    font-size: 22px !important;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.24em;
    color: #2b1b4b;
    margin-bottom: 4px;
}
.luna-caption {
    text-align: center;
    color: #4b5563;
    font-size: 11px;
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

def plot_horoscope(natal_longitudes, houses, transit_longitudes=None):

    import numpy as np
    import matplotlib.pyplot as plt

    SIGN_LABELS = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
    ]

    PLANET_LABELS = {
        "太陽":"Sun","月":"Moon","水星":"Me","金星":"Ve","火星":"Ma",
        "木星":"Jup","土星":"Sat","天王星":"Ur","海王星":"Ne","冥王星":"Pl"
    }

    asc = houses[0]

    def angle(deg):
        return np.deg2rad((asc - deg) % 360)

    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)

    ax.set_rlim(0,1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

    # ===== サイン帯（これで固定）=====
    for i,label in enumerate(SIGN_LABELS):
        start = i * 30
        end = start + 30

        theta = angle(np.linspace(start, end, 100))
        label_angle = angle(start + 15)

        color = "#ede9fe" if i % 2 == 0 else "#e0e7ff"

        ax.fill_between(theta, 0.72, 0.92, color=color)
        ax.text(label_angle, 0.82, label, ha="center", va="center", fontsize=10)

    # ===== 円 =====
    circle = np.linspace(0, 2*np.pi, 400)
    ax.plot(circle, [0.92]*len(circle), color="#7c3aed")
    ax.plot(circle, [0.72]*len(circle), color="#c4b5fd")
    ax.plot(circle, [0.98]*len(circle), color="black")

    # ===== ハウス =====
    for i, cusp in enumerate(houses):
        th = angle(cusp)
        ax.plot([th, th], [0, 0.72], color="gray", linewidth=1)

        next_cusp = houses[(i+1)%12]
        mid = (cusp + ((next_cusp - cusp) % 360)/2) % 360

        ax.text(angle(mid), 0.30, str(i+1),
                ha="center", va="center", fontsize=10)

    # ===== 天体 =====
    for name, deg in natal_longitudes.items():
        th = angle(deg)
        label = PLANET_LABELS.get(name, name)
        color = "red" if name == "太陽" else "black"

        ax.scatter(th, 0.62, s=40, color=color)
        ax.text(th, 0.68, label, ha="center", fontsize=8)

    # ===== トランジット =====
    if transit_longitudes:
        for name, deg in transit_longitudes.items():
            th = np.deg2rad((asc - deg) % 360)
            ax.scatter(th, 0.78, s=25, color="blue")

    return fig

# ---------- トランジット ----------

def get_transit_positions(year, month, day):
    import swisseph as swe
    jd = swe.julday(year, month, day, 12.0)

    planets = {
        "太陽": swe.SUN,
        "月": swe.MOON,
        "水星": swe.MERCURY,
        "金星": swe.VENUS,
        "火星": swe.MARS,
        "木星": swe.JUPITER,
        "土星": swe.SATURN,
    }

    result = {}
    for name, p in planets.items():
        lon = swe.calc_ut(jd, p)[0][0]
        result[name] = lon

    return result

# import swisseph as swe

# def get_transit_positions(year, month, day):
#     # UTCで12時固定（ズレ防止）
#     jd = swe.julday(year, month, day, 12.0)

#     planets = {
#         "☉ 太陽": swe.SUN,
#         "☽ 月": swe.MOON,
#         "☿ 水星": swe.MERCURY,
#         "♀ 金星": swe.VENUS,
#         "♂ 火星": swe.MARS,
#         "♃ 木星": swe.JUPITER,
#         "♄ 土星": swe.SATURN,
#     }

#     result = {}

#     for name, p in planets.items():
#         lon = swe.calc_ut(jd, p)[0][0]
#         result[name] = lon

#     return result


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

# =========================
# タロット（英語キー管理）
# =========================


cards = [
    ("fool", "00_fool.png"),
    ("magician", "01_magician.png"),
    ("high_priestess", "02_high_priestess.png"),
    ("empress", "03_empress.png"),
    ("emperor", "04_emperor.png"),
    ("hierophant", "05_hierophant.png"),
    ("lovers", "06_lovers.png"),
    ("chariot", "07_chariot.png"),
    ("strength", "08_strength.png"),
    ("hermit", "09_hermit.png"),
    ("wheel_of_fortune", "10_wheel_of_fortune.png"),
    ("justice", "11_justice.png"),
    ("hanged_man", "12_hanged_man.png"),
    ("death", "13_death.png"),
    ("temperance", "14_temperance.png"),
    ("devil", "15_devil.png"),
    ("tower", "16_tower.png"),
    ("star", "17_star.png"),
    ("moon", "18_moon.png"),
    ("sun", "19_sun.png"),
    ("judgement", "20_judgement.png"),
    ("world", "21_world.png"),
]

TAROT_NAME_JP = {
    "fool": "愚者",
    "magician": "魔術師",
    "high_priestess": "女教皇",
    "empress": "女帝",
    "emperor": "皇帝",
    "hierophant": "教皇",
    "lovers": "恋人",
    "chariot": "戦車",
    "strength": "力",
    "hermit": "隠者",
    "wheel_of_fortune": "運命の輪",
    "justice": "正義",
    "hanged_man": "吊るされた男",
    "death": "死神",
    "temperance": "節制",
    "devil": "悪魔",
    "tower": "塔",
    "star": "星",
    "moon": "月",
    "sun": "太陽",
    "judgement": "審判",
    "world": "世界",
}

TAROT_BASE = {
    "fool": "新しい始まり。自由な発想で進みましょう。",
    "magician": "現実を動かす力。行動が結果を引き寄せます。",
    "high_priestess": "直感が鍵。静かに内面を見つめましょう。",
    "empress": "豊かさと愛。安心できる環境が整います。",
    "emperor": "安定と支配。自分の軸を持ちましょう。",
    "hierophant": "伝統と学び。基本に立ち返る時です。",
    "lovers": "選択と調和。心の声に従いましょう。",
    "chariot": "前進と勝利。迷わず進む力があります。",
    "strength": "内なる強さ。優しさが力になります。",
    "hermit": "内省の時間。答えは自分の中にあります。",
    "wheel_of_fortune": "運命の転換期。流れに乗りましょう。",
    "justice": "公平と判断。冷静な決断が必要です。",
    "hanged_man": "視点の転換。今は待つことも大切。",
    "death": "終わりと再生。新しいステージへ。",
    "temperance": "調和とバランス。整えることが大事。",
    "devil": "執着と誘惑。冷静に見極めましょう。",
    "tower": "崩壊と覚醒。大きな変化が訪れます。",
    "star": "希望と癒し。未来は明るいです。",
    "moon": "不安と幻想。見えない部分に注意。",
    "sun": "成功と喜び。エネルギーが満ちています。",
    "judgement": "目覚めと再起。過去を超える時。",
    "world": "完成と達成。大きな区切りです。",
}

TAROT_REVERSE = {
    "fool": "無計画さに注意。慎重さが必要です。",
    "magician": "力が空回り。焦らず整えましょう。",
    "high_priestess": "直感が鈍る。情報を見直しましょう。",
    "empress": "甘えすぎに注意。自立がテーマです。",
    "emperor": "支配的になりすぎ。柔軟さを持ちましょう。",
    "hierophant": "常識に縛られすぎ。視野を広げて。",
    "lovers": "迷い・不一致。決断が必要です。",
    "chariot": "暴走注意。コントロールが必要。",
    "strength": "自信不足。内面を整えて。",
    "hermit": "孤立しすぎ。外との繋がりを。",
    "wheel_of_fortune": "流れが停滞。無理に動かない。",
    "justice": "判断ミス。冷静さを取り戻す。",
    "hanged_man": "停滞しすぎ。行動のタイミング。",
    "death": "変化を拒否。手放すことが必要。",
    "temperance": "バランス崩壊。整える意識を。",
    "devil": "依存・執着。距離を取るべき。",
    "tower": "混乱長引く。冷静な立て直しを。",
    "star": "希望薄れる。小さな光を見て。",
    "moon": "不安増大。事実を確認する。",
    "sun": "空回り。無理しすぎに注意。",
    "judgement": "決断遅れ。覚悟が必要。",
    "world": "未完成。もう一歩が必要。",
}

#import random

# def draw_card():
#     card_key, filename = random.choice(cards)

#     card_name = TAROT_NAME_JP[card_key]
#     card_msg = TAROT_BASE[card_key]

#     card_img = f"assets/tarot/{filename}"

#     return card_name, card_msg, card_img

def draw_card():
    import random

    card_key, filename = random.choice(cards)

    is_reversed = random.choice([True, False])

    card_name = TAROT_NAME_JP[card_key]

    if is_reversed:
        card_name += "（逆位置）"
        card_msg = TAROT_REVERSE[card_key]
    else:
        card_msg = TAROT_BASE[card_key]

    card_img = f"assets/tarot/{filename}"

    # 🔴 ここが重要（4つ返す）
    return card_name, card_msg, card_img, is_reversed


import random

def draw_three_cards():
    selected = random.sample(cards, 3)  # 重複なしで3枚

    result = []

    for card_key, filename in selected:
        is_reversed = random.choice([True, False])

        card_name = TAROT_NAME_JP[card_key]

        if is_reversed:
            card_name += "（逆位置）"
            card_msg = TAROT_REVERSE[card_key]
        else:
            card_msg = TAROT_BASE[card_key]

        card_img = f"assets/tarot/{filename}"

        result.append((card_name, card_msg, card_img, is_reversed))

    return result



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
    return signs[int((deg % 360) / 30)]

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
# tab1, tab2, tab3, tab4 = st.tabs([
#     "🌙 ネイタル",
#     "🌞 トランジット",
#     "💞 相性占い",
#     "🃏 カードメッセージ"
# ])

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌙 ネイタル",
    "🌍 トランジット",
    "💕 相性",
    "🔮 カード",
    "📖 詳細説明"
])

# === タブ1：ネイタル ===
with tab1:
    st.write("テスト：ここからネイタル")

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

    mode = st.radio(
        "自分を占う",
        ("自分を占う", "別の人を占う"),
        key="mode_natal",
        help="ご自身か、他の人を選んでください。"
    )

    if mode == "自分を占う":
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
        name = st.text_input(
            "お名前",
            value=default_name,
            key="name_natal",
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
        birth_hour = st.number_input(
            "時",
            min_value=0,
            max_value=23,
            value=default_hour,
            key="birth_hour_natal",
            help="分からなければそのままでOK"
        )

    with col_time2:
        birth_minute = st.number_input(
            "分",
            min_value=0,
            max_value=59,
            value=default_min,
            key="birth_minute_natal"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='luna-section-title'>🌍 今日の運気</div>", unsafe_allow_html=True)

    tz_label = st.radio(
        "出生地のタイムゾーン",
        ("日本（JST = UTC+9）", "世界時で計算（UTC・よく分からない場合）"),
        key="tz_label_natal",
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

    st.markdown("<br>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        btn_natal = st.button("🌙 ネイタルを見る", use_container_width=True, type="primary", key="btn_natal_tab1")

    with col_btn2:
        btn_transit = st.button("✨ 今日の運気を見る", use_container_width=True, key="btn_transit_tab1")

    if btn_natal or btn_transit:
        # =====================================================
        # Tab1 共通計算：ネイタル・ハウス・トランジットをここで一括作成
        # =====================================================
        t_natal = make_ts_from_local(birthday, int(birth_hour), int(birth_minute), tz_offset)
        natal_longs = get_body_longitudes_ts(t_natal)

        # ネイタル：太陽・月・各惑星
        sun_sign, sun_deg, sun_lon = get_sun_info(t_natal)
        moon_sign, moon_deg, moon_lon = get_moon_info(t_natal)
        planets = get_planet_signs_ts(t_natal)

        sun = natal_longs.get("太陽", sun_lon)
        moon = natal_longs.get("月", moon_lon)
        mercury = natal_longs.get("水星", 0.0)
        venus = natal_longs.get("金星", 0.0)
        mars = natal_longs.get("火星", 0.0)
        jupiter = natal_longs.get("木星", 0.0)
        saturn = natal_longs.get("土星", 0.0)

        mercury_sign, mercury_deg = split_sign_degree(mercury)
        venus_sign, venus_deg = split_sign_degree(venus)
        mars_sign, mars_deg = split_sign_degree(mars)
        jupiter_sign, jupiter_deg = split_sign_degree(jupiter)
        saturn_sign, saturn_deg = split_sign_degree(saturn)

        sun_text = f"{sun_sign} {sun_deg:.2f}°"
        moon_text = f"{moon_sign} {moon_deg:.2f}°"

        # ハウス計算：Placidus / 東京固定
        dt_utc = datetime.datetime(
            birthday.year,
            birthday.month,
            birthday.day,
            int(birth_hour),
            int(birth_minute)
        ) - datetime.timedelta(hours=tz_offset)

        jd = swe.julday(
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            dt_utc.hour + dt_utc.minute / 60.0
        )

        lat = 35.68
        lon = 139.76
        house_cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        houses = house_cusps

        asc = ascmc[0]
        asc_deg = asc % 30
        asc_sign = get_sign(asc)

        # トランジット：押した時だけ外側に重ねる
        transit_longs = None
        trans_planets = {}
        if btn_transit:
            t_transit = make_ts_from_local(transit_date, 12, 0, tz_offset)
            t_sun_sign, t_sun_deg, t_sun_lon = get_sun_info(t_transit)
            t_moon_sign, t_moon_deg, t_moon_lon = get_moon_info(t_transit)
            trans_planets = get_planet_signs_ts(t_transit)
            transit_longs = get_body_longitudes_ts(t_transit)

        # 詳細説明タブ用に保存
        st.session_state["natal_detail"] = {
            "sun": sun,
            "sun_sign": sun_sign,
            "sun_deg": sun_deg,
            "moon": moon,
            "moon_sign": moon_sign,
            "moon_deg": moon_deg,
            "mercury": mercury,
            "mercury_sign": mercury_sign,
            "mercury_deg": mercury_deg,
            "venus": venus,
            "venus_sign": venus_sign,
            "venus_deg": venus_deg,
            "mars": mars,
            "mars_sign": mars_sign,
            "mars_deg": mars_deg,
            "jupiter": jupiter,
            "jupiter_sign": jupiter_sign,
            "jupiter_deg": jupiter_deg,
            "saturn": saturn,
            "saturn_sign": saturn_sign,
            "saturn_deg": saturn_deg,
        }

        target_label = "あなた" if mode == "自分を占う" else f"{name or 'この方'}"

        st.markdown("<div class='luna-section-title'>ネイタル（出生図）</div>", unsafe_allow_html=True)
        st.write("鑑定対象：", target_label)
        st.write("名前：", name)
        st.write("生年月日：", birthday)
        st.write("出生時刻：", f"{int(birth_hour):02d}:{int(birth_minute):02d}")
        st.write("タイムゾーン：", tz_label)

        if btn_transit:
            st.markdown("<div class='luna-section-title'>トランジット（選択した日の星の配置）</div>", unsafe_allow_html=True)
            st.write("トランジット日：", transit_date)
            trans_sun_text = f"{t_sun_sign} {t_sun_deg:.2f}°"
            trans_moon_text = f"{t_moon_sign} {t_moon_deg:.2f}°"
            st.write("太陽（トランジット）：", trans_sun_text)
            st.write("月　（トランジット）：", trans_moon_text)
            st.markdown(f"<div class='luna-message'>{simple_compare_message(sun_text, trans_sun_text, '太陽')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='luna-message'>{simple_compare_message(moon_text, trans_moon_text, '月')}</div>", unsafe_allow_html=True)

            st.markdown("#### 主要トランジット惑星（サイン＆度数）")
            for p in ["木星", "土星", "冥王星"]:
                if p in trans_planets:
                    st.write(f"{p}：{trans_planets[p]}")

        if btn_natal:
            st.markdown("## ☺ 第一印象（ASC）")
            st.write(f"{asc_sign} {asc_deg:.2f}°")
            st.write(get_asc_message(asc_sign))

            st.markdown("## ☀ 太陽（本質）")
            st.write(sun_text)
            st.write(get_sun_message(sun_sign))

            st.markdown("## ☽ 月（感情）")
            st.write(moon_text)
            st.write(get_moon_message(moon_sign))

            st.markdown("## ☿ 水星（思考）")
            st.write(f"{mercury_sign} {mercury_deg:.2f}°")
            st.write(get_mercury_message(mercury_sign))

            st.markdown("## ♀ 金星（愛・好み）")
            st.write(f"{venus_sign} {venus_deg:.2f}°")
            st.write(get_venus_message(venus_sign))

            st.markdown("## ♂ 火星（行動）")
            st.write(f"{mars_sign} {mars_deg:.2f}°")
            st.write(get_mars_message(mars_sign))

            st.markdown("## ♃ 木星（拡大・発展）")
            st.write(f"{jupiter_sign} {jupiter_deg:.2f}°")
            st.write(get_jupiter_message(jupiter_sign))

            st.markdown("## ♄ 土星（課題・責任）")
            st.write(f"{saturn_sign} {saturn_deg:.2f}°")
            st.write(get_saturn_message(saturn_sign))

            aspect_planets = {
                "太陽": sun,
                "月": moon,
                "水星": mercury,
                "金星": venus,
                "火星": mars,
            }
            aspects = get_aspects(aspect_planets)
            st.markdown("## 🔷 アスペクト（関係性）")
            if aspects:
                for a in aspects:
                    st.write(f"{a['p1']} × {a['p2']} ：{a['type']}")
                    st.write(get_aspect_message(a["p1"], a["p2"], a["type"]))
            else:
                st.write("主要アスペクトはありません。")

            st.markdown("## 🌟 性格まとめ")
            summary = [
                get_sun_message(sun_sign),
                get_moon_message(moon_sign),
                get_venus_message(venus_sign),
                get_mars_message(mars_sign),
            ]
            for a in aspects:
                summary.append(get_aspect_message(a["p1"], a["p2"], a["type"]))
            for s in summary:
                st.write("・" + s)

        # 円形ホロスコープ
        st.markdown("<div class='luna-section-title'>円形ホロスコープ（内側=ネイタル／外側=トランジット）</div>", unsafe_allow_html=True)
        fig = plot_horoscope(natal_longs, houses, transit_longs)
        st.pyplot(fig)

        # 画像保存
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        st.download_button(
            label="☁ ホロスコープ画像をダウンロード",
            data=buf,
            file_name="luna_horoscope.png",
            mime="image/png",
        )

        st.markdown("#### 🔎 配置一覧（度数）")
        st.write("【ネイタル（出生）】")
        for name_body, deg in natal_longs.items():
            sign, d = split_sign_degree(deg)
            st.write(f"{name_body}: {sign} {d:.2f}°")

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("## 🔍 ホロスコープ（詳細）")

        st.write("太陽：", sun_text)
        st.markdown(
            f"<div class='luna-message'>{get_sun_message(sun_sign)}</div>",
            unsafe_allow_html=True
        )

        st.write("月　：", moon_text)
        st.markdown(
            f"<div class='luna-message'>{get_moon_message(moon_sign)}</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='luna-section-title'>惑星からのメッセージ（ネイタル）</div>", unsafe_allow_html=True)
        for p, v in planets.items():
            st.write(f"{p}：{v}")
            msg = get_planet_message(p)
            if msg:
                st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)

        st.markdown("<div class='luna-section-title'>ハウス（Placidus・ネイタル）</div>", unsafe_allow_html=True)
        for i, cusp in enumerate(house_cusps):
            house_num = i + 1
            sign = get_sign(cusp)
            msg = get_house_message(house_num, sign)
            st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)

# =========================
# 🌍 Tab2：トランジット
# =========================
with tab2:

    st.subheader("🌍 トランジット")

    # ▼ ここ重要（ローカルでdatetime使う＝衝突防止）
    import datetime as dt

    transit_date = st.date_input(
        "トランジットを見る日",
        value=dt.date.today(),
        key="transit_date_only"
    )

    if st.button("🌍 トランジットを見る", key="btn_transit_only"):

        # ▼ 時刻作成（そのまま）
        t_transit = make_ts_from_local(transit_date, 12, 0, 9)

        # ▼ 各天体
        t_sun_sign, t_sun_deg, t_sun_lon = get_sun_info(t_transit)
        t_moon_sign, t_moon_deg, t_moon_lon = get_moon_info(t_transit)

        transit_longs = get_body_longitudes_ts(t_transit)

        st.markdown(
            "<div class='luna-section-title'>トランジット（その日の星の配置）</div>",
            unsafe_allow_html=True
        )

        st.write("日付：", transit_date)
        st.write("☉ 太陽：", f"{t_sun_sign} {t_sun_deg:.2f}°")
        st.write("☽ 月：", f"{t_moon_sign} {t_moon_deg:.2f}°")

        st.markdown("### 🪐 各天体")

        # ▼ カード表示
        for name_body, deg in transit_longs.items():
            sign, d = split_sign_degree(deg)

            st.markdown(f"""
            <div class="luna-card">
                <div class="luna-section-title">{name_body}</div>
                <div>{sign} {d:.1f}°</div>
            </div>
            """, unsafe_allow_html=True)

        # ===== 一言メッセージ =====
        st.markdown("### ✨ 今日の流れ")

        if t_sun_sign == "牡羊座":
            msg = "👉 新しいことを始める力が強い日。動くほど流れが開けます。"
        elif t_sun_sign == "牡牛座":
            msg = "👉 お金・安定・現実面を整える日。無駄を削る判断がそのまま結果に直結します"
        elif t_sun_sign == "双子座":
            msg = "👉 情報・会話・発信が鍵。動き回るほどチャンスが増えます。"
        elif t_sun_sign == "蟹座":
            msg = "👉 心・家・安心がテーマ。自分を守る行動が運を上げます。"
        elif t_sun_sign == "獅子座":
            msg = "👉 自分を出す日。主役意識で動くほど評価が上がります。"
        elif t_sun_sign == "乙女座":
            msg = "👉 整理・改善が運気アップ。細かい見直しが大きな差に。"
        elif t_sun_sign == "天秤座":
            msg = "👉 人間関係が鍵。バランスと調和を意識すると流れが良くなる。"
        elif t_sun_sign == "蠍座":
            msg = "👉 深く集中する日。1つに絞ると強い成果が出ます。"
        elif t_sun_sign == "射手座":
            msg = "👉 広げる日。学び・挑戦・遠くに目を向けると運が動く。"
        elif t_sun_sign == "山羊座":
            msg = "👉 仕事・結果重視。現実的な行動が評価につながる日。"
        elif t_sun_sign == "水瓶座":
            msg = "👉 発想の転換が鍵。いつもと違うやり方で突破できます。"
        elif t_sun_sign == "魚座":
            msg = "👉 感性と流れに乗る日。無理せず委ねると良い方向へ。"

        st.write(msg)            

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
from pathlib import Path
from PIL import Image

with tab4:

    st.markdown("### 🔮 1枚カードメッセージ", unsafe_allow_html=True)

    if st.button("カードを1枚引く", key="card"):

        # カード取得（逆位置含む）
        card_name, card_msg, card_img, is_reversed = draw_card()

        img_path = Path(card_img) if card_img else None

        if img_path and img_path.exists():

            col1, col2, col3 = st.columns([2, 3, 2])

            with col2:
                # 画像読み込み
                img = Image.open(img_path)

                # 🔴 逆位置なら回転
                if is_reversed:
                    img = img.rotate(180)

                # 表示
                st.image(img, width=350)

                st.markdown(f"### {card_name}")
                st.write(card_msg)

        else:
            st.caption("（画像がまだ未設定 or 見つかりません）")

        # 下のカードボックス
        st.markdown(
            f"""
            <div class="luna-card-box">
                <div class="luna-subtitle">✨ 今日のヒント</div>
                <div style="margin-top:6px;color:#2b1b4b;">{card_msg}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    #st.write("")
    #st.write("")

    # テーマ選択
    theme = st.radio(
    "🔮 テーマを選んでください",
    ["総合", "恋愛", "仕事"],
    horizontal=True
    )    

    # 🔮 3枚引き（過去・現在・未来）

    #st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 🔮 3枚引き（過去・現在・未来）")

    if st.button("3枚引きする", key="three"):

        cards_3 = draw_three_cards()
        labels = ["過去", "現在", "未来"]

        col1, col2, col3 = st.columns(3)

        for i, col in enumerate([col1, col2, col3]):
            name, msg, img_path, is_reversed = cards_3[i]

            with col:
                from PIL import Image

                img = Image.open(img_path)

                if is_reversed:
                    img = img.rotate(180)

                st.image(img, width=200)
                st.markdown(f"### {labels[i]}")
                st.markdown(f"**{name}**")
                st.write(msg)

        # 🔴 総合メッセージ（これだけ残す）
        future_name, future_msg, _, _ = cards_3[2]

        #summary = f"これまでの流れを経て、今は「{future_name}」の段階に来ています。{future_msg} 無理せず整えていきましょう。"
        #summary = f"今は「{future_name}」の流れにあります。{future_msg}"

        if theme == "恋愛":
            summary = f"恋愛面では「{future_name}」の流れです。{future_msg}"
        elif theme == "仕事":
            summary = f"仕事面では「{future_name}」の流れです。{future_msg}"
        else:
            summary = f"全体の流れとしては「{future_name}」に向かっています。{future_msg}"

        summary += " 無理せず整えていきましょう。"

        st.markdown(f"""
        <div class="luna-card-box">
            <div class="luna-title">🔮 総合メッセージ</div>
            <div class="luna-text">{summary}</div>
        </div>
        """, unsafe_allow_html=True)



with tab5:

    st.markdown("## 📖 詳細説明")

    detail = st.session_state.get("natal_detail")

    if not detail:
        st.info("まずTab1で『🌙 ネイタルを見る』を押してください。詳細説明はその結果を使って表示します。")
    else:
        sun = detail["sun"]
        sun_sign = detail["sun_sign"]
        sun_deg = detail["sun_deg"]
        moon = detail["moon"]
        moon_sign = detail["moon_sign"]
        moon_deg = detail["moon_deg"]
        mercury = detail["mercury"]
        mercury_sign = detail["mercury_sign"]
        mercury_deg = detail["mercury_deg"]
        venus = detail["venus"]
        venus_sign = detail["venus_sign"]
        venus_deg = detail["venus_deg"]
        mars = detail["mars"]
        mars_sign = detail["mars_sign"]
        mars_deg = detail["mars_deg"]
        jupiter_sign = detail["jupiter_sign"]
        jupiter_deg = detail["jupiter_deg"]
        saturn_sign = detail["saturn_sign"]
        saturn_deg = detail["saturn_deg"]

        st.markdown("## ☀ 太陽（本質）")
        st.write(f"{sun_sign} {sun_deg:.2f}°")
        st.write(get_sun_message(sun_sign))

        st.markdown("## 🌙 月（感情）")
        st.write(f"{moon_sign} {moon_deg:.2f}°")
        st.write(get_moon_message(moon_sign))

        st.markdown("## ☿ 水星（思考）")
        st.write(f"{mercury_sign} {mercury_deg:.2f}°")
        st.write(get_mercury_message(mercury_sign))

        st.markdown("## ♀ 金星（愛・好み）")
        st.write(f"{venus_sign} {venus_deg:.2f}°")
        st.write(get_venus_message(venus_sign))

        st.markdown("## ♂ 火星（行動）")
        st.write(f"{mars_sign} {mars_deg:.2f}°")
        st.write(get_mars_message(mars_sign))

        st.markdown("## ♃ 木星（拡大・発展）")
        st.write(f"{jupiter_sign} {jupiter_deg:.2f}°")
        st.write(get_jupiter_message(jupiter_sign))

        st.markdown("## ♄ 土星（課題・責任）")
        st.write(f"{saturn_sign} {saturn_deg:.2f}°")
        st.write(get_saturn_message(saturn_sign))

        st.markdown("## 🔷 アスペクト")
        aspect_planets = {
            "太陽": sun,
            "月": moon,
            "水星": mercury,
            "金星": venus,
            "火星": mars
        }
        aspects = get_aspects(aspect_planets)

        for a in aspects:
            st.write(f"{a['p1']} × {a['p2']} ：{a['type']}")
            st.write(get_aspect_message(a["p1"], a["p2"], a["type"]))

        st.markdown("## 🌟 性格まとめ")
        summary = [
            get_sun_message(sun_sign),
            get_moon_message(moon_sign),
            get_venus_message(venus_sign),
            get_mars_message(mars_sign),
        ]
        for a in aspects:
            summary.append(get_aspect_message(a["p1"], a["p2"], a["type"]))
        for s in summary:
            st.write("・" + s)