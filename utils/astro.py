# utils/astro.py
# 天文計算関連の関数

import datetime
from skyfield.api import load
from skyfield.framelib import ecliptic_frame

# ---------- 定数 ----------
SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]

ELEMENTS = {
    "牡羊座": "火", "獅子座": "火", "射手座": "火",
    "牡牛座": "地", "乙女座": "地", "山羊座": "地",
    "双子座": "風", "天秤座": "風", "水瓶座": "風",
    "蟹座": "水", "蠍座": "水", "魚座": "水"
}

# ---------- 天文準備 ----------
TS = load.timescale()

try:
    EPH = load("de406.bsp")
except:
    EPH = load("de421.bsp")    

# ---------- ヘルパー：度数 → サイン＋度 ----------
def split_sign_degree(lon_deg: float):
    lon_norm = lon_deg % 360.0
    index = int(lon_norm // 30)
    degree = lon_norm % 30
    return SIGNS[index], degree

def get_sign(deg):
    return SIGNS[int((deg % 360) / 30)]

# ---------- ローカル時刻 → UTC ----------
def make_ts_from_local(date_obj: datetime.date, hour: int, minute: int, tz_offset_hours: int):
    local_dt = datetime.datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)
    utc_dt = local_dt - datetime.timedelta(hours=tz_offset_hours)
    return TS.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)

# ---------- 太陽・月・惑星情報 ----------
def get_sun_info(t):
    earth = EPH["earth"]
    sun_pos = earth.at(t).observe(EPH["sun"])
    _, lon, _ = sun_pos.frame_latlon(ecliptic_frame)
    lon_deg = lon.degrees
    sign, deg = split_sign_degree(lon_deg)
    return sign, deg, lon_deg % 360.0

def get_moon_info(t):
    earth = EPH["earth"]
    moon_pos = earth.at(t).observe(EPH["moon"])
    _, lon, _ = moon_pos.frame_latlon(ecliptic_frame)
    lon_deg = lon.degrees
    sign, deg = split_sign_degree(lon_deg)
    return sign, deg, lon_deg % 360.0

def get_planet_signs_ts(t):
    earth = EPH["earth"]
    planet_keys = {
        "水星": "mercury",
        "金星": "venus",
        "火星": "mars",
        "木星": "jupiter barycenter",
        "土星": "saturn barycenter",
        "天王星": "uranus barycenter",
        "海王星": "neptune barycenter",
        "冥王星": "pluto barycenter"
    }
    result = {}
    for name, key in planet_keys.items():
        pos = earth.at(t).observe(EPH[key])
        _, lon, _ = pos.frame_latlon(ecliptic_frame)
        lon_deg = lon.degrees
        sign, deg = split_sign_degree(lon_deg)
        result[name] = f"{sign} {deg:.2f}°"
    return result

def get_body_longitudes_ts(t):
    earth = EPH["earth"]
    bodies = {}

    sun_pos = earth.at(t).observe(EPH["sun"])
    _, sun_lon, _ = sun_pos.frame_latlon(ecliptic_frame)
    bodies["太陽"] = sun_lon.degrees % 360.0

    moon_pos = earth.at(t).observe(EPH["moon"])
    _, moon_lon, _ = moon_pos.frame_latlon(ecliptic_frame)
    bodies["月"] = moon_lon.degrees % 360.0

    planet_keys = {
        "水星": "mercury",
        "金星": "venus",
        "火星": "mars",
        "木星": "jupiter barycenter",
        "土星": "saturn barycenter",
        "天王星": "uranus barycenter",
        "海王星": "neptune barycenter",
        "冥王星": "pluto barycenter"
    }
    for name, key in planet_keys.items():
        pos = earth.at(t).observe(EPH[key])
        _, lon, _ = pos.frame_latlon(ecliptic_frame)
        bodies[name] = lon.degrees % 360.0

    return bodies

# ---------- ハウス（簡易イコールハウス） ----------
def get_equal_houses():
    houses = {}
    for i in range(12):
        cusp_deg = i * 30.0
        sign_name = SIGNS[i]
        houses[i + 1] = {
            "cusp_deg": cusp_deg,
            "sign": sign_name
        }
    return houses

# ---------- アスペクト ----------
def get_aspects(planets):
    aspects = []
    aspect_defs = {
        "コンジャンクション": 0,
        "セクスタイル": 60,
        "スクエア": 90,
        "トライン": 120,
        "オポジション": 180
    }
    for p1_name, p1_deg in planets.items():
        for p2_name, p2_deg in planets.items():
            if p1_name >= p2_name:
                continue
            diff = abs(p1_deg - p2_deg)
            if diff > 180:
                diff = 360 - diff
            for aspect_name, angle in aspect_defs.items():
                if abs(diff - angle) < 5:
                    aspects.append({
                        "p1": p1_name,
                        "p2": p2_name,
                        "type": aspect_name
                    })
    return aspects

def simple_compare_message(natal_text, transit_text, label):
    if natal_text == transit_text:
        return f"{label}はネイタル・トランジットともに『{natal_text}』。<br>自分らしさと、その日の流れが重なりやすい配置です。"
    else:
        return (
            f"{label}のネイタルは『{natal_text}』、トランジットは『{transit_text}』。<br>"
            "ふだんの傾向に、期間限定で別のテーマが重なっているタイミングです。"
        )
