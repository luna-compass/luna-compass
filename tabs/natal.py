# tabs/natal.py
# タブ1：ネイタル（出生図）

import streamlit as st
import datetime
import io
import swisseph as swe

from utils.astro import (
    make_ts_from_local, get_sun_info, get_moon_info,
    get_planet_signs_ts, get_body_longitudes_ts,
    split_sign_degree, get_aspects, get_sign
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
from utils.messages_loader import get_message, get_aspect_message_json

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
    """PDF用にランダムでタロット1枚を引く"""
    import random
    cards = [
        ("愚者", "新しい始まり。自由な発想で進みましょう。", "assets/tarot/00_fool.png"),
        ("魔術師", "現実を動かす力。行動が結果を引き寄せます。", "assets/tarot/01_magician.png"),
        ("女教皇", "直感が鍵。静かに内面を見つめましょう。", "assets/tarot/02_high_priestess.png"),
        ("女帝", "豊かさと愛。安心できる環境が整います。", "assets/tarot/03_empress.png"),
        ("皇帝", "安定と支配。自分の軸を持ちましょう。", "assets/tarot/04_emperor.png"),
        ("教皇", "伝統と学び。基本に立ち返る時です。", "assets/tarot/05_hierophant.png"),
        ("恋人", "選択と調和。心の声に従いましょう。", "assets/tarot/06_lovers.png"),
        ("戦車", "前進と勝利。迷わず進む力があります。", "assets/tarot/07_chariot.png"),
        ("力", "内なる強さ。優しさが力になります。", "assets/tarot/08_strength.png"),
        ("隠者", "内省の時間。答えは自分の中にあります。", "assets/tarot/09_hermit.png"),
        ("運命の輪", "運命の転換期。流れに乗りましょう。", "assets/tarot/10_wheel_of_fortune.png"),
        ("正義", "公平と判断。冷静な決断が必要です。", "assets/tarot/11_justice.png"),
        ("吊るされた男", "視点の転換。今は待つことも大切。", "assets/tarot/12_hanged_man.png"),
        ("死神", "終わりと再生。新しいステージへ。", "assets/tarot/13_death.png"),
        ("節制", "調和とバランス。整えることが大事。", "assets/tarot/14_temperance.png"),
        ("悪魔", "執着と誘惑。冷静に見極めましょう。", "assets/tarot/15_devil.png"),
        ("塔", "崩壊と覚醒。大きな変化が訪れます。", "assets/tarot/16_tower.png"),
        ("星", "希望と癒し。未来は明るいです。", "assets/tarot/17_star.png"),
        ("月", "不安と幻想。見えない部分に注意。", "assets/tarot/18_moon.png"),
        ("太陽", "成功と喜び。エネルギーが満ちています。", "assets/tarot/19_sun.png"),
        ("審判", "目覚めと再起。過去を超える時。", "assets/tarot/20_judgement.png"),
        ("世界", "完成と達成。大きな区切りです。", "assets/tarot/21_world.png"),
    ]
    is_reversed = random.choice([True, False])
    card_name, card_msg, card_img = random.choice(cards)
    position = "逆位置" if is_reversed else "正位置"
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
            # ===== 天文計算 =====
            time_unknown = user_info.get("time_unknown", False)
            t_natal = make_ts_from_local(birthday, int(birth_hour), int(birth_minute), tz_offset)
            natal_longs = get_body_longitudes_ts(t_natal)

            sun_sign, sun_deg, sun_lon   = get_sun_info(t_natal)
            moon_sign, moon_deg, moon_lon = get_moon_info(t_natal)

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

            sun_text  = f"{sun_sign} {sun_deg:.2f}°"
            moon_text = f"{moon_sign} {moon_deg:.2f}°"

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
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            st.image(buf, use_container_width=True)

            buf2 = io.BytesIO()
            fig.savefig(buf2, format="png", bbox_inches="tight")
            buf2.seek(0)
            st.download_button(
                label="☁ ホロスコープ画像をダウンロード",
                data=buf2,
                file_name="luna_horoscope.png",
                mime="image/png",
            )

            # ===== ②ASC =====
            st.markdown("---")
            st.markdown("### ☺ 第一印象（ASC）")
            st.markdown(f"**{asc_sign} {asc_deg_val:.2f}°**")
            st.markdown(f"<div class='luna-message'>{get_asc_message(asc_sign)}</div>", unsafe_allow_html=True)

            # ===== ③内惑星（太陽・月・水星・金星・火星） =====
            st.markdown("---")
            planets_inner = [
                ("☀ 太陽（本質）", sun_sign, sun_deg, sun_text, get_sun_message, "太陽"),
                ("☽ 月（感情）", moon_sign, moon_deg, moon_text, get_moon_message, "月"),
                ("☿ 水星（思考）", mercury_sign, mercury_deg, f"{mercury_sign} {mercury_deg:.2f}°", get_mercury_message, "水星"),
                ("♀ 金星（愛・好み）", venus_sign, venus_deg, f"{venus_sign} {venus_deg:.2f}°", get_venus_message, "金星"),
                ("♂ 火星（行動）", mars_sign, mars_deg, f"{mars_sign} {mars_deg:.2f}°", get_mars_message, "火星"),
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
                st.markdown(f"**{sign} {deg:.2f}°　{house_num}ハウス**")
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
            aspects = [
                a for a in aspects_raw
                if not (a["p1"] in OUTER_PLANETS and a["p2"] in OUTER_PLANETS)
            ]
            st.markdown("### 🔷 アスペクト（天体の関係性）")
            if aspects:
                for a in aspects:
                    st.markdown(f"**{a['p1']} × {a['p2']}** ：{a['type']}")
                    st.markdown(f"<div class='luna-message'>{get_aspect_message(a['p1'], a['p2'], a['type'])}</div>", unsafe_allow_html=True)
            else:
                st.write("主要アスペクトはありません。")

            # ===== ⑥総合メッセージ =====
            st.markdown("---")
            st.markdown("### 🌟 総合メッセージ")

            # ① 自動生成メッセージ（充実版）
            asc_full = get_asc_message(asc_sign).split("\n")[0]
            sun_full = get_sun_message(sun_sign).split("\n")[0]
            moon_full = get_moon_message(moon_sign).split("\n")[0]
            mercury_full = get_mercury_message(mercury_sign).split("\n")[0]
            venus_full = get_venus_message(venus_sign).split("\n")[0]
            mars_full = get_mars_message(mars_sign).split("\n")[0]

            # シンプルな総合メッセージ
            overall_parts = []
            if not time_unknown:
                overall_parts.append(f"{name or 'あなた'}は{asc_sign}のASCを持ち、{asc_full}")
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

            st.markdown("**⭐ 星が示すあなたのストーリー**")
            st.markdown(f"<div class='luna-message'>{overall_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

            summary = [overall_text]

            # ===== ⑦PDF鑑定書ダウンロード =====
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
                "asc_deg": f"{asc_deg_val:.1f}°",
                "asc_message": get_asc_message(asc_sign),
                "sun_sign": sun_sign, "sun_deg": f"{sun_deg:.1f}°",
                "sun_house": _house("太陽"), "sun_message": get_sun_message(sun_sign),
                "sun_house_message": _house_msg("太陽", "太陽"),
                "moon_sign": moon_sign, "moon_deg": f"{moon_deg:.1f}°",
                "moon_house": _house("月"), "moon_message": get_moon_message(moon_sign),
                "moon_house_message": _house_msg("月", "月"),
                "mercury_sign": mercury_sign, "mercury_deg": f"{mercury_deg:.1f}°",
                "mercury_house": _house("水星"), "mercury_message": get_mercury_message(mercury_sign),
                "mercury_house_message": _house_msg("水星", "水星"),
                "venus_sign": venus_sign, "venus_deg": f"{venus_deg:.1f}°",
                "venus_house": _house("金星"), "venus_message": get_venus_message(venus_sign),
                "venus_house_message": _house_msg("金星", "金星"),
                "mars_sign": mars_sign, "mars_deg": f"{mars_deg:.1f}°",
                "mars_house": _house("火星"), "mars_message": get_mars_message(mars_sign),
                "mars_house_message": _house_msg("火星", "火星"),
                "jupiter_sign": jupiter_sign, "jupiter_deg": f"{jupiter_deg:.1f}°",
                "jupiter_house": _house("木星"), "jupiter_message": get_jupiter_message(jupiter_sign),
                "jupiter_house_message": _house_msg("木星", "木星"),
                "saturn_sign": saturn_sign, "saturn_deg": f"{saturn_deg:.1f}°",
                "saturn_house": _house("土星"), "saturn_message": get_saturn_message(saturn_sign),
                "saturn_house_message": _house_msg("土星", "土星"),
                "uranus_sign": uranus_sign, "uranus_deg": f"{uranus_deg:.1f}°",
                "uranus_house": _house("天王星"), "uranus_message": get_uranus_message(uranus_sign),
                "uranus_house_message": _house_msg("天王星", "天王星"),
                "neptune_sign": neptune_sign, "neptune_deg": f"{neptune_deg:.1f}°",
                "neptune_house": _house("海王星"), "neptune_message": get_neptune_message(neptune_sign),
                "neptune_house_message": _house_msg("海王星", "海王星"),
                "pluto_sign": pluto_sign, "pluto_deg": f"{pluto_deg:.1f}°",
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
            }

            pdf_buf = create_reading_pdf(user_data, chart_buf)
            st.download_button(
                label="📄 鑑定書PDFをダウンロード",
                data=pdf_buf,
                file_name=f"luna_reading_{name or 'guest'}.pdf",
                mime="application/pdf",
                use_container_width=True,
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
