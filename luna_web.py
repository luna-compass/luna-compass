import streamlit as st
import datetime
import pandas as pd

# ---------- 起動時キャッシュウォームアップ ----------
# JSONファイルを起動時に読み込んでおくことで、1回目のボタン操作を高速化する
from utils.messages_loader import reload as _reload_messages
_reload_messages()  # 毎回リロードして最新JSONを確実に読み込む

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
.luna-subtitle {
    font-size: 13px;
    color: #7a6a9a;
    margin-top: -8px;
    margin-bottom: 14px;
    font-style: italic;
    line-height: 1.6;
}
.luna-card {
    background: rgba(255, 255, 255, 0.97);
    border-radius: 24px;
    padding: 26px 30px;
    border: 1px solid #d8b4fe;
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.25);
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
.luna-card-box {
    background: #ffffff;
    border-radius: 16px;
    border: 2px solid #a855f7;
    padding: 16px 18px;
    margin-top: 10px;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
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
    .luna-card {
        max-width: 100% !important;
        padding: 14px 14px !important;
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
    "<div style='text-align:center; margin-top:16px; margin-bottom:12px;'>"
    "<div class='luna-header-wrap'>"
    "<div class='luna-title'>Luna 占星術</div>"
    "<div class='luna-caption'>出生時刻対応・トランジット対応  Luna-compass</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True
)

# ---------- session_state 初期化 ----------
if "menu_selected" not in st.session_state:
    st.session_state["menu_selected"] = None

# ---------- メニュー選択前：トップメニュー画面を表示 ----------
if st.session_state["menu_selected"] is None:
    from menu import show as show_menu
    show_menu()
    st.stop()

# ---------- メニュー選択後：戻るボタン ----------
if st.button("← メニューに戻る", key="back_to_menu"):
    st.session_state["menu_selected"] = None
    st.rerun()

st.markdown("---")

# ---------- 総合鑑定 ----------
if st.session_state["menu_selected"] == "general":

    st.markdown("### 🌟 総合鑑定")

    with st.expander("👤 基本情報を入力する", expanded=True):
        mode = st.radio(
            "占う対象",
            ("自分を占う", "別の人を占う"),
            key="mode_general",
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
            name = st.text_input("お名前", value=default_name, key="name_general", help="ニックネームでもOKです")
        with col2:
            birthday = st.date_input(
                "生年月日",
                value=default_date,
                min_value=datetime.date(1800, 1, 1),
                max_value=datetime.date.today(),
                key="birthday_general"
            )

        time_unknown = st.checkbox(
            "出生時刻が不明（ソーラーチャートで計算）",
            value=False,
            key="time_unknown_general"
        )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            birth_hour = st.number_input(
                "出生時（時）", min_value=0, max_value=23, value=default_hour,
                key="hour_general", disabled=time_unknown
            )
        with col_t2:
            birth_minute = st.number_input(
                "出生時（分）", min_value=0, max_value=59, value=default_min,
                key="minute_general", disabled=time_unknown
            )

        tz_label = st.radio(
            "出生地のタイムゾーン",
            ("日本（JST = UTC+9）", "世界時で計算（UTC）"),
            key="tz_general",
            horizontal=True
        )
        tz_offset = 9 if tz_label.startswith("日本") else 0

        cities = pd.read_csv("cities.csv")
        default_city_index = int(cities[cities["city"] == default_city].index[0]) if default_city in cities["city"].values else 0
        city = st.selectbox("出生地", cities["city"], index=default_city_index, key="city_general")
        row = cities[cities["city"] == city].iloc[0]
        lat = float(row["lat"])
        lon_city = float(row["lon"])

    user_info = {
        "name": name,
        "birthday": birthday,
        "birth_hour": 12 if time_unknown else birth_hour,
        "birth_minute": 0 if time_unknown else birth_minute,
        "tz_offset": tz_offset,
        "lat": lat,
        "lon": lon_city,
        "mode": mode,
        "time_unknown": time_unknown,
    }

    from tabs import natal, transit, numerology

    tab1, tab2, tab3 = st.tabs([
        "🌙 ネイタル",
        "🌍 トランジット",
        "🔢 数秘術",
    ])

    natal.show(tab1, user_info)
    transit.show(tab2, user_info)
    numerology.show(tab3, user_info)

# ---------- 相性占い ----------
elif st.session_state["menu_selected"] == "compat":

    from tabs import compatibility
    compatibility.show_direct()

# ---------- タロット ----------
elif st.session_state["menu_selected"] == "tarot":

    from tabs import cards

    tab_tarot1, tab_tarot2, tab_tarot3, tab_tarot4, tab_tarot5 = st.tabs([
        "🔮 1枚引き",
        "🔮 3枚引き（過去・現在・未来）",
        "🔮 ケルト十字（10枚）",
        "🌙 ホロスコープ（12枚）",
        "💕 相性タロット",
    ])

    cards.show_single(tab_tarot1)
    cards.show_three(tab_tarot2)
    cards.show_celtic(tab_tarot3)
    cards.show_horoscope_spread(tab_tarot4)
    cards.show_compat_tarot(tab_tarot5)

# ---------- 易占い ----------
elif st.session_state["menu_selected"] == "iching":

    from tabs import iching
    iching.show_direct()

# ---------- 四柱推命(開発中) ----------
elif st.session_state["menu_selected"] == "shichusuimei":

    from tabs import shichusuimei
    shichusuimei.show_direct()

# ---------- 今年の運勢 ----------
elif st.session_state["menu_selected"] == "kotoshi":

    from tabs import kotoshi_unsei
    kotoshi_unsei.show_direct()
