# tabs/natal.py
# タブ1：ネイタル（出生図）

import streamlit as st
import datetime
import io
import swisseph as swe

from utils.astro import (
    make_ts_from_local, get_sun_info, get_moon_info,
    get_planet_signs_ts, get_body_longitudes_ts,
    split_sign_degree, get_aspects, get_sign,
    simple_compare_message, format_degree,
    detect_special_patterns
)
from utils.messages import (
    get_sun_message as _get_sun_message,
    get_moon_message as _get_moon_message,
    get_mercury_message as _get_mercury_message,
    get_venus_message as _get_venus_message,
    get_mars_message as _get_mars_message,
    get_jupiter_message as _get_jupiter_message,
    get_saturn_message as _get_saturn_message,
    get_uranus_message as _get_uranus_message,
    get_neptune_message as _get_neptune_message,
    get_pluto_message as _get_pluto_message,
    get_aspect_message as _get_aspect_message,
    get_asc_message as _get_asc_message,
    get_house_planet_message as _get_house_planet_message,
    LIFE_PATH_MESSAGES as _LIFE_PATH_MESSAGES,
)
from utils.chart import plot_horoscope
from utils.pdf_report import create_reading_pdf
from utils.messages_loader import get_message, get_aspect_message_json, get_summary_keyword as _gkw, get_summary_keyword as _gkw

# ===== キャッシュ付き天文計算関数 =====
@st.cache_data(show_spinner=False)
def _cached_calc(birthday_str, birth_hour, birth_minute, tz_offset, lat, lon):
    """天文計算をキャッシュして高速化"""
    import datetime, swisseph as _swe
    birthday = datetime.date.fromisoformat(birthday_str)
    t = make_ts_from_local(birthday, birth_hour, birth_minute, tz_offset)
    natal_longs = get_body_longitudes_ts(t)
    sun_sign, sun_deg, sun_lon = get_sun_info(t)
    moon_sign, moon_deg, moon_lon = get_moon_info(t)
    # ハウス計算
    import datetime as _dt
    dt = _dt.datetime(birthday.year, birthday.month, birthday.day, birth_hour, birth_minute)
    jd = _swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 - tz_offset)
    house_cusps, ascmc = _swe.houses(jd, lat, lon, b'P')
    houses = house_cusps
    aspects = get_aspects(natal_longs)
    return t, natal_longs, sun_sign, sun_deg, sun_lon, moon_sign, moon_deg, moon_lon, houses, aspects

@st.cache_data(show_spinner=False)
def _cached_chart(natal_longs_key, houses_key, time_unknown):
    """チャート画像をキャッシュ"""
    import io, json
    natal_longs = json.loads(natal_longs_key)
    houses = json.loads(houses_key)
    from utils.chart import plot_horoscope
    fig = plot_horoscope(natal_longs, houses, time_unknown=time_unknown)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

# JSONから読み込む関数（なければmessages.pyにフォールバック）
def get_sun_message(sign):       return get_message("sun", sign) or _get_sun_message(sign)
def get_moon_message(sign):      return get_message("moon", sign) or _get_moon_message(sign)
def get_mercury_message(sign):   return get_message("mercury", sign) or _get_mercury_message(sign)
def get_venus_message(sign):     return get_message("venus", sign) or _get_venus_message(sign)
def get_mars_message(sign):      return get_message("mars", sign) or _get_mars_message(sign)
def get_jupiter_message(sign):   return get_message("jupiter", sign) or _get_jupiter_message(sign)
def get_saturn_message(sign):    return get_message("saturn", sign) or _get_saturn_message(sign)
def get_uranus_message(sign):    return get_message("uranus", sign) or _get_uranus_message(sign)
def get_neptune_message(sign):   return get_message("neptune", sign) or _get_neptune_message(sign)
def get_pluto_message(sign):     return get_message("pluto", sign) or _get_pluto_message(sign)
def get_asc_message(sign):       return get_message("asc", sign) or _get_asc_message(sign)

def get_aspect_message(p1, p2, aspect):
    return get_aspect_message_json(p1, p2, aspect) or _get_aspect_message(p1, p2, aspect)

def get_house_planet_message(house_num, planet):
    from utils.messages_loader import get_message as _gm
    msg = _gm("house_planet", f"{house_num}|{planet}")
    return msg or _get_house_planet_message(house_num, planet)


def _get_tarot_for_pdf():
    """PDF用にランダムでタロット1枚を引く（JSONからメッセージ取得）"""
    import random
    from utils.messages_loader import get_tarot_message as _get_tarot_msg

    cards = [
        ("愚者",       "fool",              "assets/tarot/00_fool.png"),
        ("魔術師",     "magician",          "assets/tarot/01_magician.png"),
        ("女教皇",     "high_priestess",    "assets/tarot/02_high_priestess.png"),
        ("女帝",       "empress",           "assets/tarot/03_empress.png"),
        ("皇帝",       "emperor",           "assets/tarot/04_emperor.png"),
        ("教皇",       "hierophant",        "assets/tarot/05_hierophant.png"),
        ("恋人",       "lovers",            "assets/tarot/06_lovers.png"),
        ("戦車",       "chariot",           "assets/tarot/07_chariot.png"),
        ("力",         "strength",          "assets/tarot/08_strength.png"),
        ("隠者",       "hermit",            "assets/tarot/09_hermit.png"),
        ("運命の輪",   "wheel_of_fortune",  "assets/tarot/10_wheel_of_fortune.png"),
        ("正義",       "justice",           "assets/tarot/11_justice.png"),
        ("吊るされた男","hanged_man",        "assets/tarot/12_hanged_man.png"),
        ("死神",       "death",             "assets/tarot/13_death.png"),
        ("節制",       "temperance",        "assets/tarot/14_temperance.png"),
        ("悪魔",       "devil",             "assets/tarot/15_devil.png"),
        ("塔",         "tower",             "assets/tarot/16_tower.png"),
        ("星",         "star",              "assets/tarot/17_star.png"),
        ("月",         "moon",              "assets/tarot/18_moon.png"),
        ("太陽",       "sun",               "assets/tarot/19_sun.png"),
        ("審判",       "judgement",         "assets/tarot/20_judgement.png"),
        ("世界",       "world",             "assets/tarot/21_world.png"),
    ]
    is_reversed = random.choice([True, False])
    card_name, card_key, card_img = random.choice(cards)
    position = "逆位置" if is_reversed else "正位置"

    # JSONのtarotセクションから取得（正位置・逆位置対応）
    pos_key = "逆位置" if is_reversed else "正位置"
    tarot_data = _get_tarot_msg(card_name, pos_key)

    if tarot_data and isinstance(tarot_data, dict):
        card_msg = tarot_data.get("message", "")
    else:
        # フォールバック
        fallback = {
            "正位置": "新しい流れが訪れています。直感を信じて進んでください。",
            "逆位置": "内省と見直しのタイミングです。立ち止まって考えてみましょう。",
        }
        card_msg = fallback[pos_key]

    return {
        "name": card_name,
        "position": position,
        "message": card_msg,
        "image": card_img,
        "is_reversed": is_reversed,
    }


def get_house_num(planet_deg, house_cusps):
    """天体の度数からハウス番号を求める"""
    for i in range(12):
        cusp_start = house_cusps[i]
        cusp_end = house_cusps[(i + 1) % 12]
        if cusp_end < cusp_start:
            if planet_deg >= cusp_start or planet_deg < cusp_end:
                return i + 1
        else:
            if cusp_start <= planet_deg < cusp_end:
                return i + 1
    return 1


def _render(container, user_info):
    """鑑定結果を表示する共通処理（タブ・直接表示の両方から呼ばれる）"""
    with container:
        name         = user_info["name"]
        birthday     = user_info["birthday"]
        birth_hour   = user_info["birth_hour"]
        birth_minute = user_info["birth_minute"]
        tz_offset    = user_info["tz_offset"]
        lat          = user_info["lat"]
        lon          = user_info["lon"]
        mode         = user_info["mode"]

        st.markdown("---")
        st.markdown("### 🔮 占い師からのメッセージ（任意）")
        st.caption("PDFに載せる一言メッセージをあらかじめ入力してからボタンを押してください。")
        astrologer_message = st.text_area(
            "占い師からの一言",
            placeholder=f"{user_info.get('name') or 'お客様'}さんへ\n\n今日の星たちは、あなたの内側にある光をそっと照らしています。今回の鑑定で心に浮かんだテーマや、胸に響いた感覚を大切にしてみてください。\n\n太陽と月が示すあなたの本質は、今まさに新しい流れへと導かれています。直感が教えてくれる小さなサインを受け取りながら、あなたらしいペースで進んでいけば大丈夫です。\n\nこのメッセージが、あなたの未来を照らす道しるべとなりますように。",
            height=250,
            key="astrologer_message_main"
        )
        st.markdown("---")

        btn_natal = st.button("🌙 ネイタルを見る", use_container_width=True, type="primary", key="btn_natal")

        if btn_natal:
            # ===== 天文計算（キャッシュ利用）=====
            time_unknown = user_info.get("time_unknown", False)
            import json as _json
            t_natal, natal_longs, sun_sign, sun_deg, sun_lon, moon_sign, moon_deg, moon_lon, _houses_raw, _aspects_raw = _cached_calc(
                birthday.isoformat(), int(birth_hour), int(birth_minute), tz_offset, lat, lon
            )

            sun     = natal_longs.get("太陽", sun_lon)
            moon    = natal_longs.get("月", moon_lon)
            mercury = natal_longs.get("水星", 0.0)
            venus   = natal_longs.get("金星", 0.0)
            mars    = natal_longs.get("火星", 0.0)
            jupiter = natal_longs.get("木星", 0.0)
            saturn  = natal_longs.get("土星", 0.0)

            mercury_sign, mercury_deg = split_sign_degree(mercury)
            venus_sign,   venus_deg   = split_sign_degree(venus)
            mars_sign,    mars_deg    = split_sign_degree(mars)
            jupiter_sign, jupiter_deg = split_sign_degree(jupiter)
            saturn_sign,  saturn_deg  = split_sign_degree(saturn)
            uranus_sign,  uranus_deg  = split_sign_degree(natal_longs["天王星"])
            neptune_sign, neptune_deg = split_sign_degree(natal_longs["海王星"])
            pluto_sign,   pluto_deg   = split_sign_degree(natal_longs["冥王星"])

            sun_text  = f"{sun_sign} {format_degree(sun_deg)}"
            moon_text = f"{moon_sign} {format_degree(moon_deg)}"

            # ===== ハウス計算（Placidus） =====
            dt_utc = datetime.datetime(
                birthday.year, birthday.month, birthday.day,
                int(birth_hour), int(birth_minute)
            ) - datetime.timedelta(hours=tz_offset)

            jd = swe.julday(
                dt_utc.year, dt_utc.month, dt_utc.day,
                dt_utc.hour + dt_utc.minute / 60.0
            )
            house_cusps, ascmc = swe.houses(jd, lat, lon, b'P')
            houses = house_cusps
            asc = ascmc[0]
            asc_deg_val = asc % 30
            asc_sign = get_sign(asc)

            # 各天体のハウス番号
            planet_houses = {
                "太陽": get_house_num(sun, houses),
                "月": get_house_num(moon, houses),
                "水星": get_house_num(mercury, houses),
                "金星": get_house_num(venus, houses),
                "火星": get_house_num(mars, houses),
                "木星": get_house_num(jupiter, houses),
                "土星": get_house_num(saturn, houses),
                "天王星": get_house_num(natal_longs["天王星"], houses),
                "海王星": get_house_num(natal_longs["海王星"], houses),
                "冥王星": get_house_num(natal_longs["冥王星"], houses),
            }

            target_label = "あなた" if mode == "自分を占う" else f"{name or 'この方'}"

            # ===== 基本情報 =====
            st.markdown("<div class='luna-section-title'>🌙 ネイタル（出生図）</div>", unsafe_allow_html=True)
            st.write("鑑定対象：", target_label)
            st.write("生年月日：", birthday)
            st.write("出生時刻：", f"{int(birth_hour):02d}:{int(birth_minute):02d}")

            # ===== ①円形ホロスコープ（一番上） =====
            st.markdown("### 🌙 円形ホロスコープ")
            fig = plot_horoscope(natal_longs, houses, time_unknown=time_unknown)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")  # 表示用はdpi=150で十分
            buf.seek(0)
            st.image(buf, use_container_width=True)

            buf2 = io.BytesIO()
            fig.savefig(buf2, format="png", dpi=150, bbox_inches="tight")  # ダウンロード用もdpi=150
            buf2.seek(0)
            st.download_button(
                label="☁ ホロスコープ画像をダウンロード",
                data=buf2,
                file_name="luna_horoscope.png",
                mime="image/png",
            )

            # ===== 星座・惑星記号の見方 =====
            with st.expander("🔍 ホロスコープの記号の見方"):
                st.markdown("""
**【星座記号の見方】**

| 記号 | 星座 | 記号 | 星座 |
|:---:|:---:|:---:|:---:|
| ♈ | 牡羊座 | ♎ | 天秤座 |
| ♉ | 牡牛座 | ♏ | 蠍座 |
| ♊ | 双子座 | ♐ | 射手座 |
| ♋ | 蟹座   | ♑ | 山羊座 |
| ♌ | 獅子座 | ♒ | 水瓶座 |
| ♍ | 乙女座 | ♓ | 魚座   |

**【惑星略称の見方】**

| 略称 | 惑星 | 略称 | 惑星 |
|:---:|:---:|:---:|:---:|
| Sun | 太陽 | Jup | 木星 |
| Moon | 月 | Sat | 土星 |
| Me | 水星 | Ur | 天王星 |
| Ve | 金星 | Ne | 海王星 |
| Ma | 火星 | Pl | 冥王星 |

**【度数の見方】**
例：`Sun:Gem5°` → 太陽が双子座5度にあります
""")

            # ===== ✨ キーワードサマリー =====
            st.markdown("---")
            st.markdown("### ✨ あなたのキーワード")
            kw_asc_val     = _gkw("asc", asc_sign) if not time_unknown else ""
            kw_sun_val     = _gkw("sun", sun_sign)
            kw_moon_val    = _gkw("moon", moon_sign)
            kw_mercury_val = _gkw("mercury", mercury_sign)
            kw_venus_val   = _gkw("venus", venus_sign)
            kw_mars_val    = _gkw("mars", mars_sign)

            kw_items_disp = []
            if kw_asc_val:
                kw_items_disp.append(("第一印象", kw_asc_val))
            if kw_sun_val:
                kw_items_disp.append(("人生のテーマ", kw_sun_val))
            if kw_moon_val:
                kw_items_disp.append(("心が求めるもの", kw_moon_val))
            if kw_mercury_val:
                kw_items_disp.append(("思考スタイル", kw_mercury_val))
            if kw_venus_val:
                kw_items_disp.append(("愛のスタイル", kw_venus_val))
            if kw_mars_val:
                kw_items_disp.append(("行動スタイル", kw_mars_val))

            kw_html = "<div class='luna-message'>"
            for label, kw in kw_items_disp:
                kw_html += f"<div style='margin-bottom:6px;'><span style='color:#7c3aed;font-weight:bold;'>{label}：</span>{kw}</div>"
            kw_html += "</div>"
            st.markdown(kw_html, unsafe_allow_html=True)

            # ===== ②ASC =====
            st.markdown("---")
            st.markdown("### ☺ 第一印象（ASC）")
            st.markdown(f"**{asc_sign} {format_degree(asc_deg_val)}**")
            st.markdown(f"<div class='luna-message'>{get_asc_message(asc_sign)}</div>", unsafe_allow_html=True)

            # ===== ③内惑星（太陽・月・水星・金星・火星） =====
            st.markdown("---")
            planets_inner = [
                ("☀ 太陽（本質）", sun_sign, sun_deg, sun_text, get_sun_message, "太陽"),
                ("☽ 月（感情）", moon_sign, moon_deg, moon_text, get_moon_message, "月"),
                ("☿ 水星（思考）", mercury_sign, mercury_deg, f"{mercury_sign} {format_degree(mercury_deg)}", get_mercury_message, "水星"),
                ("♀ 金星（愛・好み）", venus_sign, venus_deg, f"{venus_sign} {format_degree(venus_deg)}", get_venus_message, "金星"),
                ("♂ 火星（行動）", mars_sign, mars_deg, f"{mars_sign} {format_degree(mars_deg)}", get_mars_message, "火星"),
            ]

            for title, sign, deg, text, msg_func, pname in planets_inner:
                house_num = planet_houses[pname]
                st.markdown(f"### {title}")
                st.markdown(f"**{text}　{house_num}ハウス**")
                st.markdown(f"<div class='luna-message'>{msg_func(sign)}</div>", unsafe_allow_html=True)
                house_msg = get_house_planet_message(house_num, pname)
                st.markdown(f"<div class='luna-message'>🏠 {house_msg}</div>", unsafe_allow_html=True)

            # ===== ④外惑星 =====
            st.markdown("---")
            planets_outer = [
                ("♃ 木星（拡大・発展）", jupiter_sign, jupiter_deg, get_jupiter_message, "木星"),
                ("♄ 土星（課題・責任）", saturn_sign, saturn_deg, get_saturn_message, "土星"),
                ("♅ 天王星（覚醒・個性）", uranus_sign, uranus_deg, get_uranus_message, "天王星"),
                ("♆ 海王星（夢・直感）", neptune_sign, neptune_deg, get_neptune_message, "海王星"),
                ("♇ 冥王星（変容・再生）", pluto_sign, pluto_deg, get_pluto_message, "冥王星"),
            ]

            for title, sign, deg, msg_func, pname in planets_outer:
                house_num = planet_houses[pname]
                st.markdown(f"### {title}")
                st.markdown(f"**{sign} {format_degree(deg)}　{house_num}ハウス**")
                st.markdown(f"<div class='luna-message'>{msg_func(sign)}</div>", unsafe_allow_html=True)
                house_msg = get_house_planet_message(house_num, pname)
                st.markdown(f"<div class='luna-message'>🏠 {house_msg}</div>", unsafe_allow_html=True)

            # ===== ⑤アスペクト =====
            st.markdown("---")
            aspect_planets = {
                "太陽": sun, "月": moon, "水星": mercury, "金星": venus, "火星": mars,
                "木星": jupiter, "土星": saturn,
                "天王星": natal_longs["天王星"], "海王星": natal_longs["海王星"], "冥王星": natal_longs["冥王星"],
            }
            OUTER_PLANETS = {"天王星", "海王星", "冥王星"}
            aspects_raw = get_aspects(aspect_planets)
            aspects_filtered = [
                a for a in aspects_raw
                if not (a["p1"] in OUTER_PLANETS and a["p2"] in OUTER_PLANETS)
            ]
            # 優先度順に並び替え（個人天体優先→アスペクト強度順）
            PERSONAL = {"太陽", "月", "水星", "金星", "火星"}
            ASPECT_PRIO = {"コンジャンクション":0,"オポジション":1,"スクエア":2,"トライン":3,"セクスタイル":4}
            aspects = sorted(aspects_filtered, key=lambda a: (
                (0 if a["p1"] in PERSONAL else 1) + (0 if a["p2"] in PERSONAL else 1),
                ASPECT_PRIO.get(a["type"], 5)
            ))
            st.markdown("### 🔷 アスペクト（天体の関係性）")
            if aspects:
                for a in aspects:
                    st.markdown(f"**{a['p1']} × {a['p2']}** ：{a['type']}")
                    st.markdown(f"<div class='luna-message'>{get_aspect_message(a['p1'], a['p2'], a['type'])}</div>", unsafe_allow_html=True)
            else:
                st.write("主要アスペクトはありません。")

            # ===== グランドトライン・グランドクロス判定 =====
            patterns = detect_special_patterns(natal_longs)
            gt_natal = patterns["natal_grand_trine"]
            gc_natal = patterns["natal_grand_cross"]

            if gt_natal or gc_natal:
                st.markdown("---")
                st.markdown("### ✨ 特別なパターン（ネイタル）")

            for gt in gt_natal:
                elem = gt["element"]
                planets_str = "・".join(gt["planets"])
                signs_str = "・".join(gt["signs"])
                elem_base = {
                    "火": "情熱・行動力・創造性が大きく調和しています。自然なエネルギーの流れで、才能が開花しやすい配置です。",
                    "地": "現実的な安定・忍耐・実行力が深く調和しています。着実に目標を実現する強い力を持っています。",
                    "風": "知性・コミュニケーション・自由な発想が調和しています。アイデアが自然に広がる才能があります。",
                    "水": "感情・共感・直感が深く調和しています。人の心を感じ取る繊細な感受性が大きな力になります。",
                    "混合": "異なるエネルギーが大きく調和した、ユニークなグランドトラインです。",
                }.get(elem, "")
                elem_msg = f"{planets_str}が{elem}のエレメントで大きな三角形を形成しています。{elem_base}"
                st.markdown(f"""
<div class='luna-message'>
🔺 <b>グランドトライン（{elem}のエレメント）</b><br>
天体：{planets_str}<br>
星座：{signs_str}<br><br>
{elem_msg}
</div>
""", unsafe_allow_html=True)

            for gc in gc_natal:
                mode = gc["mode"]
                planets_str = "・".join(gc["planets"])
                signs_str = "・".join(gc["signs"])
                mode_base = {
                    "活動": "変化と行動のエネルギーが四方向から働いています。多くの課題に同時に向き合いながら、大きな成長を遂げる配置です。",
                    "固定": "強い意志と粘り強さが四方向から働いています。困難を乗り越えて、揺るぎない力を築く配置です。",
                    "柔軟": "適応力と変化への対応力が四方向から働いています。多様な状況に対処しながら、深い智慧を育てる配置です。",
                    "不定": "強烈なエネルギーが四方向から交差するグランドクロスです。大きな試練と同時に、大きな成長の機会があります。",
                }.get(mode, "")
                mode_msg = f"{planets_str}が{mode}モードで大きな十字を形成しています。{mode_base}"
                st.markdown(f"""
<div class='luna-message'>
✚ <b>グランドクロス（{mode}モード）</b><br>
天体：{planets_str}<br>
星座：{signs_str}<br><br>
{mode_msg}
</div>
""", unsafe_allow_html=True)

            # ===== 🌟 総合メッセージ =====
            st.markdown("---")
            st.markdown("### 🌟 総合メッセージ")

            asc_full = get_asc_message(asc_sign).split("\n")[0]
            sun_full = get_sun_message(sun_sign).split("\n")[0]
            moon_full = get_moon_message(moon_sign).split("\n")[0]
            mercury_full = get_mercury_message(mercury_sign).split("\n")[0]
            venus_full = get_venus_message(venus_sign).split("\n")[0]
            mars_full = get_mars_message(mars_sign).split("\n")[0]

            overall_parts = []
            name_display = (name + "さん") if name else "あなた"
            if not time_unknown:
                overall_parts.append(f"{name_display}は{asc_sign}のASCを持ち、{asc_full}")
                overall_parts.append(f"太陽は{sun_sign}の{planet_houses['太陽']}ハウスに位置し、{sun_full}")
                overall_parts.append(f"月は{moon_sign}の{planet_houses['月']}ハウスにあり、{moon_full}")
            else:
                overall_parts.append(f"太陽は{sun_sign}にあり、{sun_full}")
                overall_parts.append(f"月は{moon_sign}にあり、{moon_full}")
            overall_parts += [
                f"水星は{mercury_sign}にあり、{mercury_full}",
                f"金星は{venus_sign}にあり、{venus_full}",
                f"火星は{mars_sign}にあり、{mars_full}",
            ]
            if aspects:
                a0 = aspects[0]
                asp_short = get_aspect_message(a0['p1'], a0['p2'], a0['type']).split("\n")[0]
                overall_parts.append(f"また、{a0['p1']}と{a0['p2']}の{a0['type']}が示すように、{asp_short}")

            overall_text = "\n".join(overall_parts)
            summary = [overall_text]

            st.markdown("**⭐ 星が示すあなたのストーリー**")
            st.markdown(f"<div class='luna-message'>{overall_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📄 鑑定書PDFをダウンロード")

            # ホロスコープ画像をbytesで取得
            chart_buf = io.BytesIO()
            fig.savefig(chart_buf, format="png", dpi=150, bbox_inches="tight")
            chart_buf.seek(0)

            # 数秘術計算
            def reduce_num(n):
                while n > 9 and n not in (11, 22, 33):
                    n = sum(int(d) for d in str(n))
                return n

            digits = str(birthday.year) + str(birthday.month).zfill(2) + str(birthday.day).zfill(2)
            life_path = reduce_num(sum(int(d) for d in digits))
            birthday_num = reduce_num(birthday.day)
            ruler_num = reduce_num(sum(int(d) for d in str(birthday.year)))

            from utils.messages_loader import get_message as _gm

            lp_data = _LIFE_PATH_MESSAGES.get(life_path, {})

            # JSONから数秘術メッセージを取得
            lp_json = _gm("numerology_life_path", str(life_path))
            bd_json = _gm("numerology_birthday", str(birthday_num))
            rl_json = _gm("numerology_ruler", str(ruler_num))

            # ライフパスの詳細メッセージを組み立て
            if lp_json and isinstance(lp_json, dict):
                title = lp_json.get('title','')
                message = lp_json.get('message','')
                talent = lp_json.get('talent','')
                challenge = lp_json.get('challenge','')
                keywords = lp_json.get('keywords','')
                lp_full = title + "\n\n" + message + "\n\n【才能】\n" + talent + "\n\n【課題】\n" + challenge + "\n\n【キーワード】\n" + keywords
            else:
                lp_full = lp_data.get("message", "")

            # user_dataを組み立て
            def _house(planet_jp):
                return "" if time_unknown else planet_houses[planet_jp]
            def _house_msg(planet_jp, planet_name):
                return "" if time_unknown else get_house_planet_message(planet_houses[planet_jp], planet_name)

            user_data = {
                "name": name or "　",
                "birthday": f"{birthday.year}年{birthday.month}月{birthday.day}日",
                "birth_time": f"{int(birth_hour):02d}:{int(birth_minute):02d}",
                "reading_date": datetime.date.today().strftime("%Y年%m月%d日"),
                "asc_sign": asc_sign,
                "asc_deg": format_degree(asc_deg_val),
                "asc_message": get_asc_message(asc_sign),
                "sun_sign": sun_sign, "sun_deg": format_degree(sun_deg),
                "sun_house": _house("太陽"), "sun_message": get_sun_message(sun_sign),
                "sun_house_message": _house_msg("太陽", "太陽"),
                "moon_sign": moon_sign, "moon_deg": format_degree(moon_deg),
                "moon_house": _house("月"), "moon_message": get_moon_message(moon_sign),
                "moon_house_message": _house_msg("月", "月"),
                "mercury_sign": mercury_sign, "mercury_deg": format_degree(mercury_deg),
                "mercury_house": _house("水星"), "mercury_message": get_mercury_message(mercury_sign),
                "mercury_house_message": _house_msg("水星", "水星"),
                "venus_sign": venus_sign, "venus_deg": format_degree(venus_deg),
                "venus_house": _house("金星"), "venus_message": get_venus_message(venus_sign),
                "venus_house_message": _house_msg("金星", "金星"),
                "mars_sign": mars_sign, "mars_deg": format_degree(mars_deg),
                "mars_house": _house("火星"), "mars_message": get_mars_message(mars_sign),
                "mars_house_message": _house_msg("火星", "火星"),
                "jupiter_sign": jupiter_sign, "jupiter_deg": format_degree(jupiter_deg),
                "jupiter_house": _house("木星"), "jupiter_message": get_jupiter_message(jupiter_sign),
                "jupiter_house_message": _house_msg("木星", "木星"),
                "saturn_sign": saturn_sign, "saturn_deg": format_degree(saturn_deg),
                "saturn_house": _house("土星"), "saturn_message": get_saturn_message(saturn_sign),
                "saturn_house_message": _house_msg("土星", "土星"),
                "uranus_sign": uranus_sign, "uranus_deg": format_degree(uranus_deg),
                "uranus_house": _house("天王星"), "uranus_message": get_uranus_message(uranus_sign),
                "uranus_house_message": _house_msg("天王星", "天王星"),
                "neptune_sign": neptune_sign, "neptune_deg": format_degree(neptune_deg),
                "neptune_house": _house("海王星"), "neptune_message": get_neptune_message(neptune_sign),
                "neptune_house_message": _house_msg("海王星", "海王星"),
                "pluto_sign": pluto_sign, "pluto_deg": format_degree(pluto_deg),
                "pluto_house": _house("冥王星"), "pluto_message": get_pluto_message(pluto_sign),
                "pluto_house_message": _house_msg("冥王星", "冥王星"),
                "aspects": [
                    {"p1": a["p1"], "p2": a["p2"], "type": a["type"],
                     "message": get_aspect_message(a["p1"], a["p2"], a["type"])}
                    for a in aspects
                ],
                "life_path": life_path,
                "birthday_num": birthday_num,
                "ruler_num": ruler_num,
                "life_path_message": lp_full,
                "birthday_message": bd_json if isinstance(bd_json, str) else "",
                "ruler_message": rl_json if isinstance(rl_json, str) else "",
                "overall_message": "　".join(summary),
                "astrologer_message": astrologer_message,
                "time_unknown": user_info.get("time_unknown", False),
                "tarot_message": _get_tarot_for_pdf(),
                # キーワードサマリー
                "kw_asc":     _gkw("asc", asc_sign),
                "kw_sun":     _gkw("sun", sun_sign),
                "kw_moon":    _gkw("moon", moon_sign),
                "kw_mercury": _gkw("mercury", mercury_sign),
                "kw_venus":   _gkw("venus", venus_sign),
                "kw_mars":    _gkw("mars", mars_sign),
                "grand_trines": detect_special_patterns(natal_longs)["natal_grand_trine"],
                "grand_crosses": detect_special_patterns(natal_longs)["natal_grand_cross"],
            }

            # ===== 通常PDF =====
            pdf_buf = create_reading_pdf(user_data, chart_buf)
            st.download_button(
                label="📄 鑑定書PDFをダウンロード",
                data=pdf_buf,
                file_name=f"luna_reading_{name or 'guest'}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            # ===== AI鑑定文生成 =====
            st.markdown("---")
            st.markdown("### 🤖 AI鑑定文生成")
            st.caption("※ APIキーが設定されている場合のみ動作します。生成後に編集できます。")

            if st.button("🤖 AI鑑定文を生成する", use_container_width=True, key="btn_ai_reading"):
                import os, json as _json
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                if not api_key:
                    st.warning("APIキーが設定されていません。`.env` ファイルに `ANTHROPIC_API_KEY=sk-ant-...` を設定してください。")
                else:
                    with st.spinner("AI鑑定文を生成中..."):
                        import requests as _req
                        # プロンプト組み立て
                        asc_info = f"ASC：{asc_sign} {format_degree(asc_deg_val)}" if not time_unknown else ""
                        house_info = ""
                        if not time_unknown:
                            house_info = f"""
ハウス配置：
- 太陽：{planet_houses['太陽']}ハウス
- 月：{planet_houses['月']}ハウス
- 水星：{planet_houses['水星']}ハウス
- 金星：{planet_houses['金星']}ハウス
- 火星：{planet_houses['火星']}ハウス"""

                        aspect_text = "、".join([f"{a['p1']}×{a['p2']} {a['type']}" for a in aspects[:6]])

                        prompt = f"""あなたはプロの西洋占星術師です。
以下のホロスコープデータをもとに、温かく個人的な日本語の鑑定文を書いてください。

【鑑定対象】
お名前：{name or 'あなた'}
生年月日：{birthday.year}年{birthday.month}月{birthday.day}日
{asc_info}

【天体配置】
太陽：{sun_sign} {format_degree(sun_deg)}
月：{moon_sign} {format_degree(moon_deg)}
水星：{mercury_sign} {format_degree(mercury_deg)}
金星：{venus_sign} {format_degree(venus_deg)}
火星：{mars_sign} {format_degree(mars_deg)}
木星：{jupiter_sign}
土星：{saturn_sign}
{house_info}

【主なアスペクト】
{aspect_text}

【数秘術】
ライフパス：{life_path}

【鑑定文の条件】
- 温かく親しみやすい文体で
- 本人の強みと可能性に焦点を当てて
- 具体的なアドバイスを含めて
- 400〜600文字程度で
- 「あなた」と呼びかける形で書いてください"""

                        try:
                            resp = _req.post(
                                "https://api.anthropic.com/v1/messages",
                                headers={
                                    "x-api-key": api_key,
                                    "anthropic-version": "2023-06-01",
                                    "content-type": "application/json",
                                },
                                json={
                                    "model": "claude-sonnet-4-6",
                                    "max_tokens": 1024,
                                    "messages": [{"role": "user", "content": prompt}]
                                },
                                timeout=30
                            )
                            result = resp.json()
                            ai_text = result["content"][0]["text"]
                            st.session_state["ai_reading_text"] = ai_text
                        except Exception as e:
                            st.error(f"生成エラー：{e}")

            # AI鑑定文の表示・編集・PDF出力
            if "ai_reading_text" in st.session_state and st.session_state["ai_reading_text"]:
                st.markdown("#### ✏️ 生成された鑑定文（編集可能）")
                edited_text = st.text_area(
                    "編集してからPDFに出力できます",
                    value=st.session_state["ai_reading_text"],
                    height=300,
                    key="ai_reading_edit"
                )
                # AI鑑定文をPDFに入れてダウンロード
                ai_user_data = dict(user_data)
                ai_user_data["astrologer_message"] = edited_text
                ai_pdf_buf = create_reading_pdf(ai_user_data, chart_buf)
                st.download_button(
                    label="📄 AI鑑定文入りPDFをダウンロード",
                    data=ai_pdf_buf,
                    file_name=f"luna_reading_AI_{name or 'guest'}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_ai_pdf"
                )


def show(tab, user_info):
    """既存タブ構成からの呼び出し（後方互換）"""
    _render(tab, user_info)


def show_direct(user_info):
    """メニュー画面から直接呼び出す場合（タブなし）"""
    import contextlib

    @contextlib.contextmanager
    def noop():
        yield st

    _render(noop(), user_info)
