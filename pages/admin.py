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
.stApp {
    background: radial-gradient(circle at top, #fdf4ff 0%, #f5f3ff 20%, #8a2be2 100%);
}
header[data-testid="stHeader"] { display: none !important; }
.admin-title {
    color: #2b1b4b;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
}
.admin-caption {
    color: #4b5563;
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

# ---------- 管理者パスワード ----------
# Streamlit Cloud: アプリの Settings → Secrets に以下を設定する
#   admin_password = "ここにパスワード"
# ローカル開発: プロジェクト直下に .streamlit/secrets.toml を作り同じ行を書く
#   （.gitignore に .streamlit/secrets.toml を追加してコミットしないこと）
import hmac

def _require_password():
    try:
        expected = st.secrets.get("admin_password", "")
    except Exception:
        expected = ""
    if not expected:
        st.error(
            "⚠️ 管理者パスワードが未設定のため、管理画面をロックしています。\n\n"
            "Streamlit Cloud の Settings → Secrets（ローカルは .streamlit/secrets.toml）に "
            "`admin_password = \"...\"` を設定してください。"
        )
        st.stop()
    if st.session_state.get("_admin_authed"):
        return
    pw = st.text_input("管理者パスワード", type="password", key="_admin_pw_input")
    if st.button("ログイン", type="primary", key="_admin_login_btn"):
        # UTF-8バイト列に変換してから比較する。
        # compare_digest は文字列だとASCII限定のため、日本語パスワードだと
        # TypeError になる。バイト列なら任意の文字が使える。
        if hmac.compare_digest(pw.encode("utf-8"), expected.encode("utf-8")):
            st.session_state["_admin_authed"] = True
            st.rerun()
        else:
            st.error("パスワードが違います。")
    st.stop()

_require_password()

# ---------- パス定義 ----------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES_DIR = os.path.join(_ROOT, "templates")
# 従来のルート直下（後方互換：standardが無い等のフォールバック用）
_DEFAULT_JSON_PATH = os.path.join(_ROOT, "messages_data.json")

# 編集できる鑑定スタイルは templates/ を自動スキャンして取得する。
# templates/<フォルダ>/messages_data.json があれば自動で選択肢に増える。
from utils.messages_loader import (
    discover_styles as _discover_styles,
    reload as _reload_messages,
)

def get_json_path(style):
    """スタイルのJSONパスを返す（templates/<style>/messages_data.json）。"""
    return os.path.join(_TEMPLATES_DIR, style, "messages_data.json")

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

# ---------- 編集スタイルの選択 ----------
# (フォルダ名, 表示名) のリスト。表示名でプルダウンを出し、選択からフォルダ名を引く。
_style_options = _discover_styles()
_style_folders = [f for f, _label in _style_options]
_style_labels = [label for _f, label in _style_options]
_label_to_folder = {label: f for f, label in _style_options}
_folder_to_label = {f: label for f, label in _style_options}

# 実際に編集対象として「反映済み」のスタイル（session_stateで管理）。
# 初回はリストの先頭（standard）を採用する。
if "_admin_active_style" not in st.session_state:
    st.session_state["_admin_active_style"] = _style_folders[0] if _style_folders else "standard"

# プルダウンは「候補の選択」だけ。押すまで反映しない。
_active_folder = st.session_state["_admin_active_style"]
_active_index = _style_folders.index(_active_folder) if _active_folder in _style_folders else 0

col_style, col_apply = st.columns([3, 1])
with col_style:
    _picked_label = st.selectbox(
        "編集する鑑定スタイル",
        _style_labels,
        index=_active_index,
        key="admin_edit_style",
        help="スタイルを選んで、右の「このスタイルを開く」を押すと反映されます。templates/ にフォルダを追加すると、ここに自動で表示されます。",
    )
_picked_folder = _label_to_folder.get(_picked_label, "standard")

with col_apply:
    st.write("")  # ボタンの高さをラベルに合わせる
    _apply_style = st.button(
        "このスタイルを開く",
        type="primary",
        use_container_width=True,
        key="admin_apply_style",
    )

# 「開く」ボタンが押され、かつ選択が現在のアクティブと違うときだけ切り替える。
if _apply_style and _picked_folder != st.session_state["_admin_active_style"]:
    # 前スタイルの編集値・選択（天体選択なども含む）をすべてリセットしてから切り替える。
    # これをしないと、Streamlitがウィジェットキー単位で前の状態を保持し、
    # 選択と表示中の文面がズレる。
    # ※ メインアプリ（luna_web.py）のセッションキーは消さないよう保護する。
    #   同じブラウザセッションで管理画面とアプリを行き来しても状態が壊れない。
    _protected = {
        "admin_edit_style",
        "_admin_active_style",
        "_admin_authed",          # ログイン状態（消すと切替のたびに再ログイン）
        "menu_selected",          # メインアプリのメニュー選択
        "_luna_reading_style",    # メインアプリの鑑定スタイル
    }
    for _k in list(st.session_state.keys()):
        if _k in _protected:
            continue
        st.session_state.pop(_k, None)
    st.session_state["_admin_active_style"] = _picked_folder
    st.rerun()

# 以降は「反映済み」のアクティブスタイルを使う（プルダウンの一時選択ではなく）
CURRENT_STYLE = st.session_state["_admin_active_style"]
_style_label = _folder_to_label.get(CURRENT_STYLE, CURRENT_STYLE)
JSON_PATH = get_json_path(CURRENT_STYLE)

# プルダウンの選択が未反映のときは、その旨を知らせる
if _picked_folder != CURRENT_STYLE:
    st.info(f"「{_picked_label}」を選択中です。「このスタイルを開く」を押すと切り替わります。（現在の編集対象：{_style_label}）")

# ---------- JSONを読み込む ----------
def load_data():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    # スタイル用ファイルが無い場合は、従来のルートJSONにフォールバック
    if os.path.exists(_DEFAULT_JSON_PATH):
        with open(_DEFAULT_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    # スタイルのフォルダが無ければ作成してから保存
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # ローダーのキャッシュをクリアして、アプリ側の次の読み込みで
    # 保存内容が反映されるようにする（これが無いと古い文面が出続ける）
    _reload_messages()

data = load_data()

# ---------- 編集内容のバックアップ（重要） ----------
# Streamlit Cloud のファイルシステムは一時的なので、クラウド上で保存した
# 編集は再デプロイ・再起動で消える（GitHubのファイルで上書きされる）。
# 編集後は必ずここからJSONをダウンロードして、GitHubにコミットすること。
with st.expander("💾 編集中のJSONをダウンロード（バックアップ）", expanded=False):
    st.caption(
        "⚠️ クラウド上で保存した編集は、アプリの再起動や再デプロイで消えます。"
        "編集が終わったら必ずダウンロードして、GitHubリポジトリの "
        f"templates/{CURRENT_STYLE}/messages_data.json に上書きコミットしてください。"
    )
    st.download_button(
        label=f"⬇️ {_style_label} のJSONをダウンロード",
        data=json.dumps(data, ensure_ascii=False, indent=2),
        file_name="messages_data.json",
        mime="application/json",
        use_container_width=True,
        key="download_current_json",
    )

# ---------- 「標準版からコピーして初期化」機能 ----------
if CURRENT_STYLE != "standard":
    with st.expander("このスタイルを標準版から初期化する", expanded=False):
        st.caption(
            "標準版（スタンダード）の全メッセージを、このスタイルにコピーして上書きします。"
            "新しいスタイルの土台づくりや、編集をやり直したいときに使えます。"
            "※ 現在のこのスタイルの内容は上書きされます。"
        )
        _standard_path = get_json_path("standard")
        _standard_exists = os.path.exists(_standard_path)
        if not _standard_exists:
            st.warning("標準版（templates/standard/messages_data.json）が見つかりません。")
        confirm_copy = st.checkbox(
            "内容が上書きされることを理解しました",
            key="admin_confirm_copy",
        )
        if st.button(
            f"標準版から「{_style_label}」へコピーして初期化",
            type="secondary",
            use_container_width=True,
            key="admin_copy_from_standard",
            disabled=(not _standard_exists or not confirm_copy),
        ):
            with open(_standard_path, "r", encoding="utf-8") as f:
                _std_data = json.load(f)
            save_data(_std_data)
            st.success(f"標準版の内容を「{_style_label}」にコピーしました。画面を更新します。")
            st.rerun()

if not data:
    st.error("⚠️ messages_data.json が見つかりません。まず export_messages.py を実行してください。")
    st.code("python export_messages.py", language="bash")
    st.stop()

# ---------- タブ構成 ----------
tab_planets, tab_aspects, tab_house, tab_transit, tab_tarot, tab_numerology, tab_elem, tab_sun, tab_num_tmpl = st.tabs([
    "🌟 天体・ASCメッセージ",
    "🔷 アスペクトメッセージ",
    "🏠 ハウスメッセージ",
    "🌍 トランジットアスペクト",
    "🔮 タロットメッセージ",
    "🔢 数秘術メッセージ",
    "🔥 エレメントテンプレ",
    "☀ 太陽星座テンプレ",
    "🔢 数秘術テンプレ",
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

# ===== タロットメッセージ =====
with tab_tarot:
    st.markdown("### 🔮 タロットメッセージの編集")
    st.caption("各カードの正位置・逆位置メッセージを編集できます。")

    tarot_base = data.get("tarot_base", {})
    tarot_reverse = data.get("tarot_reverse", {})

    TAROT_NAME_JP = {
        "fool":"愚者", "magician":"魔術師", "high_priestess":"女教皇",
        "empress":"女帝", "emperor":"皇帝", "hierophant":"教皇",
        "lovers":"恋人", "chariot":"戦車", "strength":"力",
        "hermit":"隠者", "wheel_of_fortune":"運命の輪", "justice":"正義",
        "hanged_man":"吊るされた男", "death":"死神", "temperance":"節制",
        "devil":"悪魔", "tower":"塔", "star":"星",
        "moon":"月", "sun":"太陽", "judgement":"審判", "world":"世界",
    }

    edited_base = dict(tarot_base)
    edited_reverse = dict(tarot_reverse)

    for card_key, card_name_jp in TAROT_NAME_JP.items():
        st.markdown(f"#### 🃏 {card_name_jp}（{card_key}）")
        col_b, col_r = st.columns(2)
        with col_b:
            edited_base[card_key] = st.text_area(
                "正位置",
                value=tarot_base.get(card_key, ""),
                height=80,
                key=f"tarot_base_{card_key}"
            )
        with col_r:
            edited_reverse[card_key] = st.text_area(
                "逆位置",
                value=tarot_reverse.get(card_key, ""),
                height=80,
                key=f"tarot_rev_{card_key}"
            )
        st.markdown("---")

    if st.button("💾 タロットメッセージを保存", type="primary", use_container_width=True, key="save_tarot"):
        data["tarot_base"] = edited_base
        data["tarot_reverse"] = edited_reverse
        save_data(data)
        st.success("✅ タロットメッセージを保存しました！")
        st.rerun()

# ===== 数秘術メッセージ =====
with tab_numerology:
    st.markdown("### 🔢 数秘術メッセージの編集")

    num_lp = data.get("numerology_life_path", {})
    num_bd = data.get("numerology_birthday", {})
    num_rl = data.get("numerology_ruler", {})

    NUM_KEYS = ["1","2","3","4","5","6","7","8","9","11","22","33"]

    edited_lp = dict(num_lp)
    edited_bd = dict(num_bd)
    edited_rl = dict(num_rl)

    st.markdown("#### 🌟 ライフパスナンバー")
    for k in NUM_KEYS:
        lp = num_lp.get(k, {})
        with st.expander(f"ライフパス {k}：{lp.get('title', '')}"):
            edited_lp[k] = {
                "title": st.text_input("タイトル", value=lp.get("title",""), key=f"lp_title_{k}"),
                "message": st.text_area("メッセージ", value=lp.get("message",""), height=100, key=f"lp_msg_{k}"),
                "talent": st.text_input("才能", value=lp.get("talent",""), key=f"lp_talent_{k}"),
                "challenge": st.text_input("課題", value=lp.get("challenge",""), key=f"lp_challenge_{k}"),
                "keywords": st.text_input("キーワード", value=lp.get("keywords",""), key=f"lp_kw_{k}"),
            }

    st.markdown("---")
    st.markdown("#### 🎂 バースデーナンバー")
    cols_bd = st.columns(2)
    for i, k in enumerate(NUM_KEYS):
        with cols_bd[i % 2]:
            edited_bd[k] = st.text_area(
                f"バースデー {k}",
                value=num_bd.get(k, ""),
                height=80,
                key=f"bd_{k}"
            )

    st.markdown("---")
    st.markdown("#### 👑 ルーラーナンバー")
    cols_rl = st.columns(2)
    for i, k in enumerate(NUM_KEYS):
        with cols_rl[i % 2]:
            edited_rl[k] = st.text_area(
                f"ルーラー {k}",
                value=num_rl.get(k, ""),
                height=80,
                key=f"rl_{k}"
            )

    st.markdown("---")
    if st.button("💾 数秘術メッセージを保存", type="primary", use_container_width=True, key="save_numerology"):
        data["numerology_life_path"] = edited_lp
        data["numerology_birthday"] = edited_bd
        data["numerology_ruler"] = edited_rl
        save_data(data)
        st.success("✅ 数秘術メッセージを保存しました！")
        st.rerun()

st.markdown("---")
st.caption(f"編集中のスタイル：{_style_label}　／　保存先: {JSON_PATH}")

# ===== エレメントテンプレ =====
with tab_elem:
    st.markdown("### 🔥 エレメントテンプレの編集")
    st.caption("占い師からのひとことで使うエレメント別テンプレを編集できます。{name}・{count}・{planets}は自動で置き換わります。")

    elem_data = data.get("element_templates", {})
    ELEMENTS_LIST = ["火", "地", "風", "水"]
    ELEM_LABELS = {"火": "🔥 火のエレメント", "地": "🌍 地のエレメント", "風": "💨 風のエレメント", "水": "💧 水のエレメント"}

    edited_elem = dict(elem_data)
    for elem in ELEMENTS_LIST:
        st.markdown(f"#### {ELEM_LABELS[elem]}")
        st.caption("{name}=お名前、{count}=天体数、{planets}=天体名 が自動で入ります")
        edited_elem[elem] = st.text_area(f"{elem}のテンプレ", value=elem_data.get(elem, ""), height=150, key=f"elem_{elem}")
        st.markdown("---")

    if st.button("💾 エレメントテンプレを保存", type="primary", use_container_width=True, key="save_elem"):
        data["element_templates"] = edited_elem
        save_data(data)
        st.success("✅ エレメントテンプレを保存しました！")
        st.rerun()

# ===== 太陽星座テンプレ =====
with tab_sun:
    st.markdown("### ☀ 太陽星座テンプレの編集")
    st.caption("{name}=お名前、{sign}=星座名 が自動で入ります。")

    sun_tmpl_data = data.get("sun_sign_templates", {})
    SIGNS_LIST = ["牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座","天秤座","蠍座","射手座","山羊座","水瓶座","魚座"]

    edited_sun = dict(sun_tmpl_data)
    cols_sun = st.columns(2)
    for i, sign in enumerate(SIGNS_LIST):
        with cols_sun[i % 2]:
            edited_sun[sign] = st.text_area(f"☀ {sign}", value=sun_tmpl_data.get(sign, ""), height=120, key=f"sun_tmpl_{sign}")

    st.markdown("---")
    if st.button("💾 太陽星座テンプレを保存", type="primary", use_container_width=True, key="save_sun_tmpl"):
        data["sun_sign_templates"] = edited_sun
        save_data(data)
        st.success("✅ 太陽星座テンプレを保存しました！")
        st.rerun()

# ===== 数秘術テンプレ =====
with tab_num_tmpl:
    st.markdown("### 🔢 数秘術テンプレの編集")
    st.caption("{name}=お名前、{lp}=ライフパスナンバー が自動で入ります。")

    num_tmpl_data = data.get("numerology_templates", {})
    NUM_KEYS = ["1","2","3","4","5","6","7","8","9","11","22","33"]

    edited_num_tmpl = dict(num_tmpl_data)
    cols_num = st.columns(2)
    for i, k in enumerate(NUM_KEYS):
        with cols_num[i % 2]:
            edited_num_tmpl[k] = st.text_area(f"🔢 ライフパス{k}", value=num_tmpl_data.get(k, ""), height=120, key=f"num_tmpl_{k}")

    st.markdown("---")
    if st.button("💾 数秘術テンプレを保存", type="primary", use_container_width=True, key="save_num_tmpl"):
        data["numerology_templates"] = edited_num_tmpl
        save_data(data)
        st.success("✅ 数秘術テンプレを保存しました！")
        st.rerun()
