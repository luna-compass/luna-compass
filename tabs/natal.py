# tabs/natal.py
# タブ1：ネイタル（出生図）

import streamlit as st
import datetime
import io
import pandas as pd
import swisseph as swe

from utils.astro import (
    make_ts_from_local, get_sun_info, get_moon_info,
    get_planet_signs_ts, get_body_longitudes_ts,
    split_sign_degree, get_aspects, simple_compare_message, get_sign
)
from utils.messages import (
    get_sun_message, get_moon_message, get_mercury_message,
    get_venus_message, get_mars_message, get_jupiter_message,
    get_saturn_message, get_uranus_message, get_neptune_message,
    get_pluto_message, get_planet_message, get_aspect_message, get_asc_message
)
from utils.chart import plot_horoscope


def show(tab):
    with tab:

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
            name = st.text_input("お名前", value=default_name, key="name_natal", help="ニックネームでもOKです")
        with col2:
            birthday = st.date_input(
                "生年月日（ネイタル）",
                value=default_date,
                min_value=datetime.date(1800, 1, 1),
                max_value=datetime.date.today(),
                key="birthday_natal",
                help="出生図を作るために使います"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='luna-section-title'>⏰ 出生時間</div>", unsafe_allow_html=True)

        col_time1, col_time2 = st.columns(2)
        with col_time1:
            birth_hour = st.number_input("時", min_value=0, max_value=23, value=default_hour, key="birth_hour_natal", help="分からなければそのままでOK")
        with col_time2:
            birth_minute = st.number_input("分", min_value=0, max_value=59, value=default_min, key="birth_minute_natal")

        tz_label = st.radio(
            "出生地のタイムゾーン",
            ("日本（JST = UTC+9）", "世界時で計算（UTC・よく分からない場合）"),
            key="tz_label_natal",
            help="海外出生の場合のみ変更してください"
        )
        tz_offset = 9 if tz_label.startswith("日本") else 0

        cities = pd.read_csv("cities.csv")
        city = st.selectbox("出生地", cities["city"])
        row = cities[cities["city"] == city].iloc[0]
        lat = row["lat"]
        lon = row["lon"]

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
            # ===== 天文計算 =====
            t_natal = make_ts_from_local(birthday, int(birth_hour), int(birth_minute), tz_offset)
            natal_longs = get_body_longitudes_ts(t_natal)

            sun_sign, sun_deg, sun_lon = get_sun_info(t_natal)
            moon_sign, moon_deg, moon_lon = get_moon_info(t_natal)
            planets = get_planet_signs_ts(t_natal)

            sun    = natal_longs.get("太陽", sun_lon)
            moon   = natal_longs.get("月", moon_lon)
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
            asc_deg = asc % 30
            asc_sign = get_sign(asc)

            # ===== トランジット =====
            transit_longs = None
            trans_planets = {}
            if btn_transit:
                t_transit = make_ts_from_local(transit_date, 12, 0, tz_offset)
                t_sun_sign, t_sun_deg, _ = get_sun_info(t_transit)
                t_moon_sign, t_moon_deg, _ = get_moon_info(t_transit)
                trans_planets = get_planet_signs_ts(t_transit)
                transit_longs = get_body_longitudes_ts(t_transit)

            # ===== 表示 =====
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
                trans_sun_text  = f"{t_sun_sign} {t_sun_deg:.2f}°"
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
                # ASC
                st.markdown("### ☺ 第一印象（ASC）")
                st.markdown("<div class='luna-subtitle'>あなたが自然に放つ雰囲気</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{asc_sign} {asc_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_asc_message(asc_sign)}</div>", unsafe_allow_html=True)

                # 太陽
                st.markdown("### ☀ 太陽（本質）")
                st.markdown("<div class='luna-subtitle'>あなたらしさの中心</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{sun_text}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_sun_message(sun_sign)}</div>", unsafe_allow_html=True)

                # 月
                st.markdown("### ☽ 月（感情）")
                st.markdown("<div class='luna-subtitle'>心が安心する場所</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{moon_text}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_moon_message(moon_sign)}</div>", unsafe_allow_html=True)

                # 水星
                st.markdown("### ☿ 水星（思考）")
                st.markdown("<div class='luna-subtitle'>考え方と伝え方の特徴</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{mercury_sign} {mercury_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_mercury_message(mercury_sign)}</div>", unsafe_allow_html=True)

                # 金星
                st.markdown("### ♀ 金星（愛・好み）")
                st.markdown("<div class='luna-subtitle'>愛し方と魅力の傾向</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{venus_sign} {venus_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_venus_message(venus_sign)}</div>", unsafe_allow_html=True)

                # 火星
                st.markdown("### ♂ 火星（行動）")
                st.markdown("<div class='luna-subtitle'>エネルギーの使い方</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{mars_sign} {mars_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_mars_message(mars_sign)}</div>", unsafe_allow_html=True)

                # 木星
                st.markdown("### ♃ 木星（拡大・発展）")
                st.markdown("<div class='luna-subtitle'>幸運が広がる方向</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{jupiter_sign} {jupiter_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_jupiter_message(jupiter_sign)}</div>", unsafe_allow_html=True)

                # 土星
                st.markdown("### ♄ 土星（課題・責任）")
                st.markdown("<div class='luna-subtitle'>人生で深めていくテーマ</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-subtext'>{saturn_sign} {saturn_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_saturn_message(saturn_sign)}</div>", unsafe_allow_html=True)

                # 天王星
                uranus_sign, uranus_deg = split_sign_degree(natal_longs["天王星"])
                st.markdown("### ♅ 天王星（覚醒・個性）")
                st.markdown(f"<div class='luna-subtext'>{uranus_sign}座 {uranus_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_uranus_message(uranus_sign)}</div>", unsafe_allow_html=True)

                # 海王星
                neptune_sign, neptune_deg = split_sign_degree(natal_longs["海王星"])
                st.markdown("### ♆ 海王星（夢・直感）")
                st.markdown(f"<div class='luna-subtext'>{neptune_sign}座 {neptune_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_neptune_message(neptune_sign)}</div>", unsafe_allow_html=True)

                # 冥王星
                pluto_sign, pluto_deg = split_sign_degree(natal_longs["冥王星"])
                st.markdown("### ♇ 冥王星（変容・再生）")
                st.markdown(f"<div class='luna-subtext'>{pluto_sign}座 {pluto_deg:.2f}°</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='luna-message'>{get_pluto_message(pluto_sign)}</div>", unsafe_allow_html=True)

                # アスペクト
                st.markdown("<br>", unsafe_allow_html=True)
                aspect_planets = {"太陽": sun, "月": moon, "水星": mercury, "金星": venus, "火星": mars}
                aspects = get_aspects(aspect_planets)
                st.markdown("### 🔷 アスペクト（関係性）")
                if aspects:
                    for a in aspects:
                        st.write(f"{a['p1']} × {a['p2']} ：{a['type']}")
                        st.write(get_aspect_message(a["p1"], a["p2"], a["type"]))
                else:
                    st.write("主要アスペクトはありません。")

                # 性格まとめ
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 🌟 性格まとめ")
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
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="font-size:34px; font-weight:700; margin-top:20px; margin-bottom:18px; color:#2d2d2d;">
            🌙 円形ホロスコープ
            </div>
            """, unsafe_allow_html=True)
            fig = plot_horoscope(natal_longs, houses, transit_longs)
            # st.pyplot(fig)
            # st.pyplot(fig, use_container_width=True)       
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            st.image(buf, use_container_width=True)                 

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            st.download_button(
                label="☁ ホロスコープ画像をダウンロード",
                data=buf,
                file_name="luna_horoscope.png",
                mime="image/png",
            )

            # 詳細一覧
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("### 🔍 ホロスコープ（詳細）")
            st.write("太陽：", sun_text)
            st.markdown(f"<div class='luna-message'>{get_sun_message(sun_sign)}</div>", unsafe_allow_html=True)
            st.write("月　：", moon_text)
            st.markdown(f"<div class='luna-message'>{get_moon_message(moon_sign)}</div>", unsafe_allow_html=True)

            planet_msg_funcs = {
                "水星": get_mercury_message,
                "金星": get_venus_message,
                "火星": get_mars_message,
                "木星": get_jupiter_message,
                "土星": get_saturn_message,
                "天王星": get_uranus_message,
                "海王星": get_neptune_message,
                "冥王星": get_pluto_message,
            }
            for p, v in planets.items():
                st.write(f"{p}:{v}")
                sign = v.split()[0]
                func = planet_msg_funcs.get(p)
                msg = func(sign) if func else get_planet_message(p)
                if msg:
                    st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)
