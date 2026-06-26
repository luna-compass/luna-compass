# pages/dev.py
# 開発用：元のタブ画面（全機能確認用）

import streamlit as st
import datetime
import pandas as pd

st.set_page_config(
    page_title="Luna 開発用",
    page_icon="🔧",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #fdf4ff 0%, #f5f3ff 20%, #8a2be2 100%);
}
.block-container {
    padding-top: 20px !important;
}
.stMainBlockContainer {
    padding-top: 10px !important;
}
header[data-testid="stHeader"] {
    display: none !important;
}
.luna-header-wrap {
    background: rgba(255, 255, 255, 0.92);
    border-radius: 18px;
    padding: 10px 20px 14px 20px;
    display: inline-block;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
}
.luna-title {
    font-size: 20px !important;
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
.luna-section-title {
    font-size: 20px;
    margin-top: 20px;
    margin-bottom: 10px;
    color: #2b1b4b;
    border-left: 4px solid #d8b4fe;
    padding-left: 10px;
    font-weight: 600;
}
.luna-message {
    background: #f9f5ff;
    padding: 14px 18px;
    border-radius: 14px;
    margin: 10px 0 18px 0;
    color: #1f1437;
    line-height: 1.7em;
    border: 1px solid #a855f7;
}
.stTextInput input, .stDateInput input, .stNumberInput input {
    background: #ffffff !important;
    border: 1px solid #c4b5fd !important;
    border-radius: 8px !important;
    color: #111827 !important;
    padding: 6px 8px !important;
}
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 5px !important;
    }
    .luna-title {
        font-size: 20px !important;
        letter-spacing: 0.18em !important;
    }
}
button[kind="primary"] {
    width: 100% !important;
    height: 48px !important;
    font-size: 16px !important;
    border-radius: 999px !important;
    margin-bottom: 12px !important;
}
button[kind="secondary"] {
    border-radius: 999px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- タイトル ----------
st.markdown(
    "<div style='text-align:center; margin-top:16px; margin-bottom:4px;'>"
    "<div class='luna-header-wrap'>"
    "<div class='luna-title'>Luna 占星術　🔧 開発用</div>"
    "<div class='luna-caption'>全機能タブ表示　※開発・確認用画面</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True
)

st.caption("⚠️ この画面は開発・動作確認用です。お客様への共有にはトップページをご利用ください。")
st.markdown("---")

# ---------- 共通入力フォーム ----------
with st.expander("👤 基本情報を入力する", expanded=True):

    mode = st.radio(
        "占う対象",
        ("自分を占う", "別の人を占う"),
        key="mode_dev",
        horizontal=True
    )

    if mode == "自分を占う":
        default_name = "Luna"
        default_date = datetime.date(1968, 5, 27)
        default_hour = 0
        default_min = 0
        default_city = "北九州"
    else:
        default_name = ""
        default_date = datetime.date(1990, 1, 1)
        default_hour = 12
        default_min = 0
        default_city = "東京"

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("お名前", value=default_name, key="name_dev")
    with col2:
        birthday = st.date_input(
            "生年月日",
            value=default_date,
            min_value=datetime.date(1800, 1, 1),
            max_value=datetime.date.today(),
            key="birthday_dev"
        )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        birth_hour = st.number_input("出生時（時）", min_value=0, max_value=23, value=default_hour, key="hour_dev")
    with col_t2:
        birth_minute = st.number_input("出生時（分）", min_value=0, max_value=59, value=default_min, key="minute_dev")

    tz_label = st.radio(
        "出生地のタイムゾーン",
        ("日本（JST = UTC+9）", "世界時で計算（UTC）"),
        key="tz_dev",
        horizontal=True
    )
    tz_offset = 9 if tz_label.startswith("日本") else 0

    cities = pd.read_csv("cities.csv")
    default_city_index = int(cities[cities["city"] == default_city].index[0]) if default_city in cities["city"].values else 0
    city = st.selectbox("出生地", cities["city"], index=default_city_index, key="city_dev")
    row = cities[cities["city"] == city].iloc[0]
    lat = float(row["lat"])
    lon_city = float(row["lon"])

st.markdown("---")

# ---------- タブ構成（全機能） ----------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌙 ネイタル",
    "🌍 トランジット",
    "💕 相性",
    "🔢 数秘術",
    "🔮 カード",
    "📖 詳細説明"
])

from tabs import natal, transit, compatibility, numerology, cards, guide

user_info = {
    "name": name,
    "birthday": birthday,
    "birth_hour": birth_hour,
    "birth_minute": birth_minute,
    "tz_offset": tz_offset,
    "lat": lat,
    "lon": lon_city,
    "mode": mode,
}

natal.show(tab1, user_info)
transit.show(tab2, user_info)
compatibility.show(tab3)
numerology.show(tab4, user_info)

with tab5:
    tab_tarot1, tab_tarot2, tab_tarot3, tab_tarot4 = st.tabs([
        "🔮 1枚引き",
        "🔮 3枚引き（過去・現在・未来）",
        "🔮 ケルト十字（10枚）",
        "🌙 ホロスコープ（12枚）",
    ])
    cards.show_single(tab_tarot1)
    cards.show_three(tab_tarot2)
    cards.show_celtic(tab_tarot3)
    cards.show_horoscope_spread(tab_tarot4)

guide.show(tab6)
