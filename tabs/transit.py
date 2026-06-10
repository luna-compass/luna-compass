# tabs/transit.py
# タブ2：トランジット

import streamlit as st
import datetime
import io
import swisseph as swe

from utils.astro import (
    make_ts_from_local, get_sun_info, get_moon_info,
    get_body_longitudes_ts, get_planet_signs_ts,
    split_sign_degree, get_sign, simple_compare_message
)
from utils.messages import (
    get_transit_aspect_message
)
from utils.chart import plot_horoscope


def get_aspects_transit(natal_planets, transit_planets):
    """トランジット天体×ネイタル天体のアスペクトを計算"""
    aspects = []
    aspect_defs = {
        "コンジャンクション": 0,
        "セクスタイル": 60,
        "スクエア": 90,
        "トライン": 120,
        "オポジション": 180
    }
    orbs = {
        "コンジャンクション": 8,
        "セクスタイル": 4,
        "スクエア": 6,
        "トライン": 6,
        "オポジション": 8
    }

    for t_name, t_deg in transit_planets.items():
        for n_name, n_deg in natal_planets.items():
            diff = abs(t_deg - n_deg) % 360
            if diff > 180:
                diff = 360 - diff
            for asp_name, asp_angle in aspect_defs.items():
                if abs(diff - asp_angle) <= orbs[asp_name]:
                    aspects.append({
                        "transit": t_name,
                        "natal": n_name,
                        "type": asp_name,
                        "orb": abs(diff - asp_angle)
                    })
    # オーブが小さい順（正確な順）にソート
    aspects.sort(key=lambda x: x["orb"])
    return aspects


def show(tab, user_info):
    with tab:

        birthday     = user_info["birthday"]
        birth_hour   = user_info["birth_hour"]
        birth_minute = user_info["birth_minute"]
        tz_offset    = user_info["tz_offset"]
        lat          = user_info["lat"]
        lon          = user_info["lon"]

        st.markdown("### 🌍 トランジット（今日・気になる日の流れ）")

        transit_date = st.date_input(
            "トランジットを見る日",
            value=datetime.date.today(),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            key="transit_date"
        )

        btn_transit = st.button("🌍 トランジットを見る", use_container_width=True, type="primary", key="btn_transit")

        if btn_transit:
            # ===== ネイタル計算 =====
            t_natal = make_ts_from_local(birthday, int(birth_hour), int(birth_minute), tz_offset)
            natal_longs = get_body_longitudes_ts(t_natal)
            sun_sign, sun_deg, _ = get_sun_info(t_natal)
            moon_sign, moon_deg, _ = get_moon_info(t_natal)
            sun_text  = f"{sun_sign} {sun_deg:.2f}°"
            moon_text = f"{moon_sign} {moon_deg:.2f}°"

            # ===== ハウス計算 =====
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

            # ===== トランジット計算 =====
            t_transit = make_ts_from_local(transit_date, 12, 0, tz_offset)
            t_sun_sign, t_sun_deg, _ = get_sun_info(t_transit)
            t_moon_sign, t_moon_deg, _ = get_moon_info(t_transit)
            trans_planets = get_planet_signs_ts(t_transit)
            transit_longs = get_body_longitudes_ts(t_transit)

            trans_sun_text  = f"{t_sun_sign} {t_sun_deg:.2f}°"
            trans_moon_text = f"{t_moon_sign} {t_moon_deg:.2f}°"

            st.write("トランジット日：", transit_date)

            # ===== ①ホロスコープ（ネイタル＋トランジット重ね表示） =====
            st.markdown("### 🌙 ホロスコープ（ネイタル＋トランジット）")
            st.caption("● ネイタル天体　▲ トランジット天体（青）")
            fig = plot_horoscope(natal_longs, houses, transit_longs)
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
                file_name="luna_transit.png",
                mime="image/png",
            )

            # ===== ②今日の太陽・月 =====
            st.markdown("---")
            st.markdown("### ☀ 今日の太陽・月")
            st.write(f"☀ 太陽：{trans_sun_text}")
            st.write(f"☽ 月：{trans_moon_text}")

            # ===== ③今日の流れメッセージ =====
            st.markdown("### ✨ 今日の流れ")
            flow_messages = {
                "牡羊座": "新しいことを始める力が強い日。動くほど流れが開けます。",
                "牡牛座": "お金・安定・現実面を整える日。無駄を削る判断が結果に直結します。",
                "双子座": "情報・会話・発信が鍵。動き回るほどチャンスが増えます。",
                "蟹座": "心・家・安心がテーマ。自分を守る行動が運を上げます。",
                "獅子座": "自分を出す日。主役意識で動くほど評価が上がります。",
                "乙女座": "整理・改善が運気アップ。細かい見直しが大きな差に。",
                "天秤座": "人間関係が鍵。バランスと調和を意識すると流れが良くなります。",
                "蠍座": "深く集中する日。1つに絞ると強い成果が出ます。",
                "射手座": "広げる日。学び・挑戦・遠くに目を向けると運が動きます。",
                "山羊座": "仕事・結果重視。現実的な行動が評価につながる日。",
                "水瓶座": "発想の転換が鍵。いつもと違うやり方で突破できます。",
                "魚座": "感性と流れに乗る日。無理せず委ねると良い方向へ。",
            }
            msg = flow_messages.get(t_sun_sign, "")
            if msg:
                st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)

            # ===== ④ネイタルとの比較 =====
            st.markdown("---")
            st.markdown("### 🔄 ネイタルとの比較")

            st.markdown("**☀ 太陽**")
            st.write(f"ネイタル：{sun_text}　→　トランジット：{trans_sun_text}")
            st.markdown(f"<div class='luna-message'>{simple_compare_message(sun_text, trans_sun_text, '太陽')}</div>", unsafe_allow_html=True)

            st.markdown("**☽ 月**")
            st.write(f"ネイタル：{moon_text}　→　トランジット：{trans_moon_text}")
            st.markdown(f"<div class='luna-message'>{simple_compare_message(moon_text, trans_moon_text, '月')}</div>", unsafe_allow_html=True)

            # ===== ⑤トランジット×ネイタル アスペクト =====
            st.markdown("---")
            st.markdown("### 🔮 トランジット×ネイタル アスペクト")
            st.caption("今この人の星に何が起きているかを示します")

            # 重要な天体に絞る
            natal_key_planets = {
                "太陽": natal_longs.get("太陽", 0),
                "月": natal_longs.get("月", 0),
                "水星": natal_longs.get("水星", 0),
                "金星": natal_longs.get("金星", 0),
                "火星": natal_longs.get("火星", 0),
            }
            transit_key_planets = {
                "木星": transit_longs.get("木星", 0),
                "土星": transit_longs.get("土星", 0),
                "天王星": transit_longs.get("天王星", 0),
                "海王星": transit_longs.get("海王星", 0),
                "冥王星": transit_longs.get("冥王星", 0),
            }

            aspects = get_aspects_transit(natal_key_planets, transit_key_planets)

            if aspects:
                for a in aspects:
                    asp_icon = {
                        "コンジャンクション": "🔴",
                        "トライン": "🟢",
                        "スクエア": "🟠",
                        "セクスタイル": "🔵",
                        "オポジション": "🟣"
                    }.get(a["type"], "⚪")

                    st.markdown(f"**{asp_icon} トランジット{a['transit']} × ネイタル{a['natal']}：{a['type']}**")
                    msg = get_transit_aspect_message(a["transit"], a["natal"], a["type"])
                    st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)
            else:
                st.write("現在、主要なアスペクトはありません。")

            # ===== ⑥注目の外惑星 =====
            st.markdown("---")
            st.markdown("### 🪐 外惑星の動き")
            st.caption("ゆっくり動く惑星は長期的な流れを示します")
            for p in ["木星", "土星", "天王星", "海王星", "冥王星"]:
                if p in transit_longs:
                    sign, d = split_sign_degree(transit_longs[p])
                    st.write(f"**{p}**：{sign} {d:.1f}°")
