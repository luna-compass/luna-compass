# export_messages.py
# 既存のmessages.pyからJSONファイルを生成するスクリプト
# 一度だけ実行してください

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.messages import (
    get_sun_message, get_moon_message, get_mercury_message,
    get_venus_message, get_mars_message, get_jupiter_message,
    get_saturn_message, get_uranus_message, get_neptune_message,
    get_pluto_message, get_asc_message, NATAL_ASPECT_MESSAGES,
    HOUSE_PLANET_MESSAGES, TRANSIT_ASPECT_MESSAGES
)

SIGNS = ["牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座",
         "天秤座","蠍座","射手座","山羊座","水瓶座","魚座"]

data = {
    "sun": {s: get_sun_message(s) for s in SIGNS},
    "moon": {s: get_moon_message(s) for s in SIGNS},
    "mercury": {s: get_mercury_message(s) for s in SIGNS},
    "venus": {s: get_venus_message(s) for s in SIGNS},
    "mars": {s: get_mars_message(s) for s in SIGNS},
    "jupiter": {s: get_jupiter_message(s) for s in SIGNS},
    "saturn": {s: get_saturn_message(s) for s in SIGNS},
    "uranus": {s: get_uranus_message(s) for s in SIGNS},
    "neptune": {s: get_neptune_message(s) for s in SIGNS},
    "pluto": {s: get_pluto_message(s) for s in SIGNS},
    "asc": {s: get_asc_message(s) for s in SIGNS},
    "aspects": {
        f"{k[0]}|{k[1]}|{k[2]}": v
        for k, v in NATAL_ASPECT_MESSAGES.items()
    },
    "house_planet": {
        f"{house}|{planet}": msg
        for house, planets in HOUSE_PLANET_MESSAGES.items()
        for planet, msg in planets.items()
    },
    "transit_aspects": {
        f"{k[0]}|{k[1]}|{k[2]}": v
        for k, v in TRANSIT_ASPECT_MESSAGES.items()
    },
}

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "messages_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ messages_data.json を作成しました: {output_path}")
