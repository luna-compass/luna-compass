# utils/messages_loader.py
# messages_data.json からメッセージを読み込む
# messages.py のフォールバックとして使用
#
# 【v2 変更点】マルチユーザー対応
# - 「現在のスタイル」を st.session_state に保持（ユーザーごとに独立）
#   → 従来のモジュール変数だと Streamlit Cloud 上で全ユーザーが
#     同じスタイルを共有してしまい、文面が混ざる事故が起きるため。
# - キャッシュをスタイル別の辞書に変更（読み取り専用なのでプロセス共有でOK）
#   → スタイル切替のたびにキャッシュを捨てる必要がなくなり、高速化。
# - get_message() 等の呼び出し側インターフェースは変更なし。

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 従来どおりのルート直下 messages_data.json（デフォルト・後方互換）
_DEFAULT_JSON_PATH = os.path.join(_ROOT, "messages_data.json")

# テンプレート（鑑定スタイル）の置き場所： templates/<style>/messages_data.json
_TEMPLATES_DIR = os.path.join(_ROOT, "templates")

# session_state に「現在のスタイル」を保存するキー。
# 画面ウィジェットの key（例: reading_style_general）と衝突しないよう
# アンダースコア始まりの専用キーを使う。
_SESSION_KEY = "_luna_reading_style"

# スタイル別キャッシュ： {スタイル名: JSONデータ}
# JSONは読み取り専用なので、全セッションで共有しても安全。
_caches = {}

# Streamlit のセッションが使えない環境（テストスクリプト等）向けの
# フォールバック用スタイル保持変数。
_fallback_style = None

# フォルダ名 → 画面表示名。ここに無いフォルダはフォルダ名がそのまま表示される。
# 新しいスタイルを追加したいだけなら、templates/ にフォルダを作れば自動で選べる。
# 表示名をきれいにしたいときだけ、ここに1行足す。
STYLE_DISPLAY_NAMES = {
    "standard": "スタンダード（総合）",
    "love": "恋愛・相性",
}


def _session_state_or_none():
    """Streamlit 実行中なら st.session_state を返す。
    それ以外（単体テスト等）では None を返す。"""
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            return None  # Streamlit 外から呼ばれている
        return st.session_state
    except Exception:
        return None


def discover_styles():
    """templates/ 内の messages_data.json を持つフォルダを自動検出し、
    [(フォルダ名, 表示名), ...] のリストを返す。
    standard を先頭にし、残りはフォルダ名順で並べる。
    templates/standard/ が無くても、ルート直下 messages_data.json があれば
    standard を必ず選択肢に含める（後方互換）。"""
    found = []
    if os.path.isdir(_TEMPLATES_DIR):
        for entry in sorted(os.listdir(_TEMPLATES_DIR)):
            style_dir = os.path.join(_TEMPLATES_DIR, entry)
            if not os.path.isdir(style_dir):
                continue
            if os.path.exists(os.path.join(style_dir, "messages_data.json")):
                found.append(entry)
    # standard を必ず先頭に。
    ordered = []
    if "standard" in found:
        found.remove("standard")
        ordered.append("standard")
    elif os.path.exists(_DEFAULT_JSON_PATH):
        ordered.append("standard")
    ordered.extend(found)
    # 何も無い場合の最終保険
    if not ordered:
        ordered = ["standard"]
    return [(name, STYLE_DISPLAY_NAMES.get(name, name)) for name in ordered]


def set_style(style_name):
    """鑑定スタイルを切り替える（このユーザーのセッションのみ）。
    style_name: 例 'standard', 'love'。None または '' でデフォルトに戻る。"""
    global _fallback_style
    new_style = style_name or None
    ss = _session_state_or_none()
    if ss is not None:
        ss[_SESSION_KEY] = new_style
    else:
        _fallback_style = new_style


def get_style():
    """現在選択中のスタイル名を返す（未指定なら None）。"""
    ss = _session_state_or_none()
    if ss is not None:
        return ss.get(_SESSION_KEY)
    return _fallback_style


def _resolve_json_path(style):
    """スタイルに応じて読み込むJSONのパスを返す。
    スタイル未指定、またはスタイル用ファイルが存在しない場合は
    従来のルート messages_data.json にフォールバックする（後方互換）。"""
    if style:
        style_path = os.path.join(_TEMPLATES_DIR, style, "messages_data.json")
        if os.path.exists(style_path):
            return style_path
        # スタイル指定はあるがファイルが無い → デフォルトにフォールバック
    return _DEFAULT_JSON_PATH


def _load():
    """現在のセッションのスタイルに対応するJSONデータを返す。
    スタイル別にキャッシュするので、複数ユーザーが別スタイルを
    同時に使ってもキャッシュの捨て合いは起きない。"""
    style = get_style()
    path = _resolve_json_path(style)
    return _load_path(path)


def _load_path(path):
    """パス指定でJSONを読み込む（パス単位でキャッシュ）。"""
    if path not in _caches:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _caches[path] = json.load(f)
        else:
            _caches[path] = {}
    return _caches[path]


def _load_base():
    """フォールバック用の基準（標準）データを返す。
    templates/standard/messages_data.json があればそれ、
    無ければルート直下 messages_data.json。"""
    return _load_path(_resolve_json_path("standard"))


def _with_fallback(value, base_getter, fallback):
    """スタイルの値が空のとき、標準の値 → 引数fallback の順で補う。
    「準備中の項目は標準文面で表示されます」という仕様を
    項目単位で実現するためのヘルパー。"""
    if value:
        return value
    base_value = base_getter()
    return base_value if base_value else fallback


def get_message(planet_key, sign, fallback=""):
    """天体+星座のメッセージをJSONから取得。
    スタイルで空欄の項目は標準文面にフォールバックする。"""
    value = _load().get(planet_key, {}).get(sign, "")
    return _with_fallback(
        value,
        lambda: _load_base().get(planet_key, {}).get(sign, ""),
        fallback,
    )


def get_aspect_message_json(p1, p2, aspect):
    """アスペクトメッセージをJSONから取得（スタイル→標準の順で補完）"""
    key1 = f"{p1}|{p2}|{aspect}"
    key2 = f"{p2}|{p1}|{aspect}"

    def _pick(data):
        aspects = data.get("aspects", {})
        return aspects.get(key1) or aspects.get(key2) or ""

    return _with_fallback(_pick(_load()), lambda: _pick(_load_base()), "")


def get_summary_keyword(planet, sign):
    """summary_masterからキーワードを取得（スタイル→標準の順で補完）"""
    value = _load().get("summary_master", {}).get(planet, {}).get(sign, "")
    return _with_fallback(
        value,
        lambda: _load_base().get("summary_master", {}).get(planet, {}).get(sign, ""),
        "",
    )


def get_house_planet_message(house_num, planet_name):
    """ハウス×惑星のメッセージをJSONから取得（スタイル→標準の順で補完）
    house_num: int（例: 1）
    planet_name: str（例: '太陽'）
    """
    key = f"{house_num}|{planet_name}"
    value = _load().get("house_planet", {}).get(key, "")
    return _with_fallback(
        value,
        lambda: _load_base().get("house_planet", {}).get(key, ""),
        "",
    )


def get_transit_aspect_message(transit_planet, natal_planet, aspect):
    """トランジットアスペクトメッセージをJSONから取得（スタイル→標準の順で補完）
    transit_planet: str（例: '木星'）
    natal_planet: str（例: '太陽'）
    aspect: str（例: 'コンジャンクション'）
    """
    key = f"{transit_planet}|{natal_planet}|{aspect}"
    value = _load().get("transit_aspects", {}).get(key, "")
    return _with_fallback(
        value,
        lambda: _load_base().get("transit_aspects", {}).get(key, ""),
        "",
    )


def get_tarot_message(card_name, position):
    """タロットメッセージをJSONから取得（正位置・逆位置対応。
    スタイルに無いカードは標準にフォールバック）"""
    value = _load().get("tarot", {}).get(card_name, {}).get(position, {})
    if value:
        return value
    return _load_base().get("tarot", {}).get(card_name, {}).get(position, {})


def reload():
    """全スタイルのキャッシュをリセットする。
    管理画面でJSONを編集・保存した後に呼べば、次の読み込みで反映される。"""
    global _caches
    _caches = {}
