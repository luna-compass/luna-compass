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

def reload():
    """キャッシュをリセットして再読み込み"""
    global _cache
    _cache = None
    _load()
