# tabs/transit.py
# タブ2：トランジット

import streamlit as st
import datetime as dt
from utils.astro import make_ts_from_local, get_sun_info, get_moon_info, get_body_longitudes_ts, split_sign_degree


def show(tab):
    with tab:
        st.subheader("🌍 トランジット")

        transit_date = st.date_input(
            "トランジットを見る日",
            value=dt.date.today(),
            key="transit_date_only"
        )

        if st.button("🌍 トランジットを見る", key="btn_transit_only"):

            t_transit = make_ts_from_local(transit_date, 12, 0, 9)

            t_sun_sign, t_sun_deg, _ = get_sun_info(t_transit)
            t_moon_sign, t_moon_deg, _ = get_moon_info(t_transit)
            transit_longs = get_body_longitudes_ts(t_transit)

            st.markdown(
                "<div class='luna-section-title'>トランジット（その日の星の配置）</div>",
                unsafe_allow_html=True
            )

            st.write("日付：", transit_date)
            st.write("☉ 太陽：", f"{t_sun_sign} {t_sun_deg:.2f}°")
            st.write("☽ 月：", f"{t_moon_sign} {t_moon_deg:.2f}°")

            st.markdown("### 🪐 各天体")

            for name_body, deg in transit_longs.items():
                sign, d = split_sign_degree(deg)
                st.markdown(f"""
                <div class="luna-card">
                    <div class="luna-section-title">{name_body}</div>
                    <div>{sign} {d:.1f}°</div>
                </div>
                """, unsafe_allow_html=True)

            # ===== 今日の流れメッセージ =====
            st.markdown("### ✨ 今日の流れ")

            flow_messages = {
                "牡羊座": "👉 新しいことを始める力が強い日。動くほど流れが開けます。",
                "牡牛座": "👉 お金・安定・現実面を整える日。無駄を削る判断がそのまま結果に直結します。",
                "双子座": "👉 情報・会話・発信が鍵。動き回るほどチャンスが増えます。",
                "蟹座": "👉 心・家・安心がテーマ。自分を守る行動が運を上げます。",
                "獅子座": "👉 自分を出す日。主役意識で動くほど評価が上がります。",
                "乙女座": "👉 整理・改善が運気アップ。細かい見直しが大きな差に。",
                "天秤座": "👉 人間関係が鍵。バランスと調和を意識すると流れが良くなる。",
                "蠍座": "👉 深く集中する日。1つに絞ると強い成果が出ます。",
                "射手座": "👉 広げる日。学び・挑戦・遠くに目を向けると運が動く。",
                "山羊座": "👉 仕事・結果重視。現実的な行動が評価につながる日。",
                "水瓶座": "👉 発想の転換が鍵。いつもと違うやり方で突破できます。",
                "魚座": "👉 感性と流れに乗る日。無理せず委ねると良い方向へ。",
            }
            msg = flow_messages.get(t_sun_sign, "")
            if msg:
                st.write(msg)
