# utils/messages_loader.py
# messages_data.json からメッセージを読み込む
# messages.py のフォールバックとして使用

import json
import os

_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "messages_data.json")
_cache = None

def _load():
    global _cache
    if _cache is None:
        if os.path.exists(_JSON_PATH):
            with open(_JSON_PATH, "r", encoding="utf-8") as f:
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
