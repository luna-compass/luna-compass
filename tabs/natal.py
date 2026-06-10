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
    get_sun_message, get_moon_message, get_mercury_message,
    get_venus_message, get_mars_message, get_jupiter_message,
    get_saturn_message, get_uranus_message, get_neptune_message,
    get_pluto_message, get_aspect_message, get_asc_message,
    get_house_planet_message
)
from utils.chart import plot_horoscope


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


def show(tab, user_info):
    with tab:

        name         = user_info["name"]
        birthday     = user_info["birthday"]
        birth_hour   = user_info["birth_hour"]
        birth_minute = user_info["birth_minute"]
        tz_offset    = user_info["tz_offset"]
        lat          = user_info["lat"]
        lon          = user_info["lon"]
        mode         = user_info["mode"]

        btn_natal = st.button("🌙 ネイタルを見る", use_container_width=True, type="primary", key="btn_natal")

        if btn_natal:
            # ===== 天文計算 =====
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
            fig = plot_horoscope(natal_longs, houses)
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
            aspect_planets = {"太陽": sun, "月": moon, "水星": mercury, "金星": venus, "火星": mars}
            aspects = get_aspects(aspect_planets)
            st.markdown("### 🔷 アスペクト（天体の関係性）")
            if aspects:
                for a in aspects:
                    st.markdown(f"**{a['p1']} × {a['p2']}** ：{a['type']}")
                    st.markdown(f"<div class='luna-message'>{get_aspect_message(a['p1'], a['p2'], a['type'])}</div>", unsafe_allow_html=True)
            else:
                st.write("主要アスペクトはありません。")

            # ===== ⑥性格まとめ =====
            st.markdown("---")
            st.markdown("### 🌟 性格まとめ")
            summary = [
                f"☀ 太陽（{sun_sign}・{planet_houses['太陽']}ハウス）：{get_sun_message(sun_sign)}",
                f"☽ 月（{moon_sign}・{planet_houses['月']}ハウス）：{get_moon_message(moon_sign)}",
                f"♀ 金星（{venus_sign}・{planet_houses['金星']}ハウス）：{get_venus_message(venus_sign)}",
                f"♂ 火星（{mars_sign}・{planet_houses['火星']}ハウス）：{get_mars_message(mars_sign)}",
            ]
            for s in summary:
                st.markdown(f"<div class='luna-message'>{s}</div>", unsafe_allow_html=True)
