# pages/admin.py
# 🔧 メッセージ管理画面（管理者用）

import streamlit as st
import json
import os

st.set_page_config(
    page_title="Luna 管理画面",
    page_icon="⚙️",
    layout="wide"
)

st.markdown("""
<style>
.stApp { background: #f5f3ff; }
header[data-testid="stHeader"] { display: none !important; }
.admin-title {
    color: #4c1d95;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
}
.admin-caption {
    color: #6b7280;
    font-size: 12px;
    margin-bottom: 20px;
}
textarea {
    font-size: 13px !important;
    line-height: 1.6 !important;
    background: #ffffff !important;
    color: #1f1437 !important;
    border: 1px solid #c4b5fd !important;
    border-radius: 8px !important;
}
label {
    color: #2b1b4b !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='admin-title'>⚙️ Luna メッセージ管理画面</div>", unsafe_allow_html=True)
st.markdown("<div class='admin-caption'>鑑定メッセージを編集・保存できます。保存後すぐにアプリに反映されます。</div>", unsafe_allow_html=True)

# ---------- JSONファイルパス ----------
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "messages_data.json")

SIGNS = ["牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座",
         "天秤座","蠍座","射手座","山羊座","水瓶座","魚座"]

PLANET_LABELS = {
    "sun": "☀ 太陽",
    "moon": "☽ 月",
    "mercury": "☿ 水星",
    "venus": "♀ 金星",
    "mars": "♂ 火星",
    "jupiter": "♃ 木星",
    "saturn": "♄ 土星",
    "uranus": "♅ 天王星",
    "neptune": "♆ 海王星",
    "pluto": "♇ 冥王星",
    "asc": "☺ ASC（アセンダント）",
}

# ---------- JSONを読み込む ----------
def load_data():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

if not data:
    st.error("⚠️ messages_data.json が見つかりません。まず export_messages.py を実行してください。")
    st.code("python export_messages.py", language="bash")
    st.stop()

# ---------- タブ構成 ----------
tab_planets, tab_aspects, tab_house, tab_transit = st.tabs([
    "🌟 天体・ASCメッセージ",
    "🔷 アスペクトメッセージ",
    "🏠 ハウスメッセージ",
    "🌍 トランジットアスペクト",
])

# ===== 天体メッセージ =====
with tab_planets:
    st.markdown("### 🌟 天体・ASCメッセージの編集")
    st.caption("星座ごとのメッセージを編集できます。編集後「保存」ボタンを押してください。")

    # 天体を選択
    planet_key = st.selectbox(
        "編集する天体を選んでください",
        list(PLANET_LABELS.keys()),
        format_func=lambda x: PLANET_LABELS[x],
        key="planet_select"
    )

    st.markdown("---")
    st.markdown(f"#### {PLANET_LABELS[planet_key]} のメッセージ編集")

    planet_data = data.get(planet_key, {})
    edited = {}

    # 星座を2列で表示
    cols = st.columns(2)
    for i, sign in enumerate(SIGNS):
        with cols[i % 2]:
            current_msg = planet_data.get(sign, "")
            new_msg = st.text_area(
                f"**{sign}**",
                value=current_msg,
                height=120,
                key=f"{planet_key}_{sign}"
            )
            edited[sign] = new_msg

    st.markdown("---")
    if st.button(f"💾 {PLANET_LABELS[planet_key]} のメッセージを保存", type="primary", use_container_width=True, key="save_planet"):
        data[planet_key] = edited
        save_data(data)
        st.success(f"✅ {PLANET_LABELS[planet_key]} のメッセージを保存しました！")
        st.rerun()

# ===== アスペクトメッセージ =====
with tab_aspects:
    st.markdown("### 🔷 アスペクトメッセージの編集")
    st.caption("天体の組み合わせごとのアスペクトメッセージを編集できます。")

    aspects_data = data.get("aspects", {})

    # キーを解析してフィルタリング
    all_keys = list(aspects_data.keys())

    # 天体フィルター
    planet_names = ["太陽","月","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]
    aspect_names = ["コンジャンクション","トライン","スクエア","オポジション","セクスタイル"]

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_planet = st.selectbox("天体でフィルター", ["すべて"] + planet_names, key="filter_planet")
    with col_f2:
        filter_aspect = st.selectbox("アスペクトでフィルター", ["すべて"] + aspect_names, key="filter_aspect")

    # フィルタリング
    filtered_keys = []
    for k in all_keys:
        parts = k.split("|")
        if len(parts) != 3:
            continue
        p1, p2, asp = parts
        if filter_planet != "すべて" and filter_planet not in [p1, p2]:
            continue
        if filter_aspect != "すべて" and asp != filter_aspect:
            continue
        filtered_keys.append(k)

    st.markdown(f"**{len(filtered_keys)} 件のアスペクトメッセージ**")
    st.markdown("---")

    edited_aspects = dict(aspects_data)

    for k in filtered_keys:
        parts = k.split("|")
        p1, p2, asp = parts
        current_msg = aspects_data.get(k, "")
        new_msg = st.text_area(
            f"**{p1} × {p2}：{asp}**",
            value=current_msg,
            height=100,
            key=f"asp_{k}"
        )
        edited_aspects[k] = new_msg

    st.markdown("---")
    if st.button("💾 アスペクトメッセージを保存", type="primary", use_container_width=True, key="save_aspects"):
        data["aspects"] = edited_aspects
        save_data(data)
        st.success("✅ アスペクトメッセージを保存しました！")
        st.rerun()

# ===== ハウスメッセージ =====
with tab_house:
    st.markdown("### 🏠 ハウス×天体メッセージの編集")
    st.caption("各ハウスに天体が入った時のメッセージを編集できます。")

    house_data = data.get("house_planet", {})

    PLANET_NAMES = ["太陽","月","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]
    HOUSE_NAMES = {
        1:"1ハウス（自分・第一印象）", 2:"2ハウス（お金・価値観）",
        3:"3ハウス（コミュニケーション）", 4:"4ハウス（家庭・ルーツ）",
        5:"5ハウス（恋愛・創造）", 6:"6ハウス（仕事・健康）",
        7:"7ハウス（パートナー）", 8:"8ハウス（変容・深い絆）",
        9:"9ハウス（哲学・海外）", 10:"10ハウス（キャリア）",
        11:"11ハウス（仲間・未来）", 12:"12ハウス（潜在意識）",
    }

    selected_house = st.selectbox(
        "編集するハウスを選んでください",
        list(range(1, 13)),
        format_func=lambda x: HOUSE_NAMES[x],
        key="house_select"
    )

    st.markdown(f"#### {HOUSE_NAMES[selected_house]} のメッセージ編集")
    st.markdown("---")

    edited_house = dict(house_data)
    cols_h = st.columns(2)
    for i, planet in enumerate(PLANET_NAMES):
        key = f"{selected_house}|{planet}"
        current = house_data.get(key, "")
        with cols_h[i % 2]:
            new_msg = st.text_area(
                f"**{planet}**",
                value=current,
                height=100,
                key=f"house_{selected_house}_{planet}"
            )
            edited_house[key] = new_msg

    st.markdown("---")
    if st.button(f"💾 {HOUSE_NAMES[selected_house]} のメッセージを保存", type="primary", use_container_width=True, key="save_house"):
        data["house_planet"] = edited_house
        save_data(data)
        st.success(f"✅ {HOUSE_NAMES[selected_house]} のメッセージを保存しました！")
        st.rerun()

# ===== トランジットアスペクト =====
with tab_transit:
    st.markdown("### 🌍 トランジットアスペクトメッセージの編集")
    st.caption("トランジット天体×ネイタル天体のメッセージを編集できます。")

    transit_data = data.get("transit_aspects", {})

    TRANSIT_PLANETS = ["木星","土星","天王星","海王星","冥王星","火星"]
    NATAL_PLANETS = ["太陽","月","水星","金星","火星","木星","土星"]
    ASPECT_TYPES = ["コンジャンクション","トライン","スクエア","オポジション","セクスタイル"]

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        filter_t = st.selectbox("トランジット天体", ["すべて"] + TRANSIT_PLANETS, key="filter_transit")
    with col_t2:
        filter_n = st.selectbox("ネイタル天体", ["すべて"] + NATAL_PLANETS, key="filter_natal")

    filtered_t_keys = []
    for k in transit_data.keys():
        parts = k.split("|")
        if len(parts) != 3:
            continue
        tp, np_, asp = parts
        if filter_t != "すべて" and tp != filter_t:
            continue
        if filter_n != "すべて" and np_ != filter_n:
            continue
        filtered_t_keys.append(k)

    st.markdown(f"**{len(filtered_t_keys)} 件のメッセージ**")
    st.markdown("---")

    edited_transit = dict(transit_data)
    for k in filtered_t_keys:
        parts = k.split("|")
        tp, np_, asp = parts
        current = transit_data.get(k, "")
        new_msg = st.text_area(
            f"**トランジット{tp} × ネイタル{np_}：{asp}**",
            value=current,
            height=100,
            key=f"transit_{k}"
        )
        edited_transit[k] = new_msg

    st.markdown("---")
    if st.button("💾 トランジットメッセージを保存", type="primary", use_container_width=True, key="save_transit"):
        data["transit_aspects"] = edited_transit
        save_data(data)
        st.success("✅ トランジットメッセージを保存しました！")
        st.rerun()

st.markdown("---")
st.caption(f"📁 保存先: {JSON_PATH}")
