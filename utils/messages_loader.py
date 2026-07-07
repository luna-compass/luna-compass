# utils/messages_loader.py
# messages_data.json からメッセージを読み込む
# messages.py のフォールバックとして使用

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 従来どおりのルート直下 messages_data.json（デフォルト・後方互換）
_DEFAULT_JSON_PATH = os.path.join(_ROOT, "messages_data.json")

# テンプレート（鑑定スタイル）の置き場所： templates/<style>/messages_data.json
_TEMPLATES_DIR = os.path.join(_ROOT, "templates")

# 現在選択中のスタイル名。None のときは従来どおりルートのJSONを読む。
_current_style = None
_cache = None


def _resolve_json_path():
    """現在のスタイルに応じて読み込むJSONのパスを返す。
    スタイル未指定、またはスタイル用ファイルが存在しない場合は
    従来のルート messages_data.json にフォールバックする（後方互換）。"""
    if _current_style:
        style_path = os.path.join(_TEMPLATES_DIR, _current_style, "messages_data.json")
        if os.path.exists(style_path):
            return style_path
        # スタイル指定はあるがファイルが無い → デフォルトにフォールバック
    return _DEFAULT_JSON_PATH


def set_style(style_name):
    """鑑定スタイルを切り替える。
    style_name: 例 'standard', 'love'。None または '' でデフォルトに戻る。
    切り替え時はキャッシュを破棄して次回読み込みで反映する。"""
    global _current_style, _cache
    new_style = style_name or None
    if new_style != _current_style:
        _current_style = new_style
        _cache = None  # スタイルが変わったらキャッシュを捨てる


def get_style():
    """現在選択中のスタイル名を返す（未指定なら None）。"""
    return _current_style


def _load():
    global _cache
    if _cache is None:
        path = _resolve_json_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache

def get_message(planet_key, sign, fallback=""):
    """天体+星座のメッセージをJSONから取得"""
    data = _load()
    return data.get(planet_key, {}).get(sign, fallback)

def get_aspect_message_json(p1, p2, aspect):
    """アスペクトメッセージをJSONから取得"""
    data = _load()
    aspects = data.get("aspects", {})
    key1 = f"{p1}|{p2}|{aspect}"
    key2 = f"{p2}|{p1}|{aspect}"
    return aspects.get(key1) or aspects.get(key2) or ""

def get_summary_keyword(planet, sign):
    """summary_masterからキーワードを取得"""
    data = _load()
    return data.get("summary_master", {}).get(planet, {}).get(sign, "")

def get_house_planet_message(house_num, planet_name):
    """ハウス×惑星のメッセージをJSONから取得
    house_num: int（例: 1）
    planet_name: str（例: '太陽'）
    """
    data = _load()
    house_planet = data.get("house_planet", {})
    key = f"{house_num}|{planet_name}"
    return house_planet.get(key, "")

def get_transit_aspect_message(transit_planet, natal_planet, aspect):
    """トランジットアスペクトメッセージをJSONから取得
    transit_planet: str（例: '木星'）
    natal_planet: str（例: '太陽'）
    aspect: str（例: 'コンジャンクション'）
    """
    data = _load()
    transit = data.get("transit_aspects", {})
    key = f"{transit_planet}|{natal_planet}|{aspect}"
    return transit.get(key, "")

def get_tarot_message(card_name, position):
    """タロットメッセージをJSONから取得（正位置・逆位置対応）"""
    data = _load()
    tarot = data.get("tarot", {})
    card = tarot.get(card_name, {})
    return card.get(position, {})

def reload():
    """キャッシュをリセットして再読み込み"""
    global _cache
    _cache = None
    _load()
