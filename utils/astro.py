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
    degree_float = lon_norm % 30
    degree_int = int(degree_float)
    minute_int = int((degree_float - degree_int) * 60)
    return SIGNS[index], degree_float

def format_degree(degree_float: float) -> str:
    """度数を 05°24' 形式にフォーマット（小数部分を60倍して分に変換）"""
    degree_int = int(degree_float)
    minute_int = int((degree_float - degree_int) * 60)
    return f"{degree_int:02d}°{minute_int:02d}'"

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

# サインの短いキーワード（比較メッセージ用）
SIGN_KEYWORDS = {
    "牡羊座": "行動力と情熱",
    "牡牛座": "安定と豊かさ",
    "双子座": "知性と柔軟さ",
    "蟹座": "感情と共感",
    "獅子座": "表現力と自信",
    "乙女座": "分析と誠実さ",
    "天秤座": "調和とバランス",
    "蠍座": "深さと集中力",
    "射手座": "自由と探究心",
    "山羊座": "努力と現実感",
    "水瓶座": "独自性と未来志向",
    "魚座": "感性と優しさ",
}

# サイン×サインの組み合わせメッセージ（同じ元素・モード）
ELEMENT_MAP = {
    "牡羊座": "火", "獅子座": "火", "射手座": "火",
    "牡牛座": "地", "乙女座": "地", "山羊座": "地",
    "双子座": "風", "天秤座": "風", "水瓶座": "風",
    "蟹座": "水", "蠍座": "水", "魚座": "水",
}

def _extract_sign(text):
    """'双子座 5.4°' などからサイン名だけ取り出す"""
    for s in SIGNS:
        if text.startswith(s):
            return s
    return None

def simple_compare_message(natal_text, transit_text, label):
    natal_sign = _extract_sign(natal_text)
    transit_sign = _extract_sign(transit_text)

    natal_kw = SIGN_KEYWORDS.get(natal_sign, "あなたらしさ")
    transit_kw = SIGN_KEYWORDS.get(transit_sign, "今日のテーマ")

    if natal_sign == transit_sign:
        return (
            f"{label}はネイタル・トランジットともに{natal_sign}。"
            f"「{natal_kw}」というあなた本来のテーマが今の流れとぴったり重なっています。"
            f"自分らしさを素直に出しやすい時期です。"
        )

    natal_elem = ELEMENT_MAP.get(natal_sign, "")
    transit_elem = ELEMENT_MAP.get(transit_sign, "")

    if natal_elem == transit_elem:
        elem_msg = f"同じ{natal_elem}のサイン同士で、エネルギーの方向性が共鳴しやすい組み合わせです。"
    else:
        elem_msg = f"{natal_elem}と{transit_elem}のエネルギーが混ざり合い、新しい視点が生まれやすい時期です。"

    return (
        f"{label}のネイタルは{natal_sign}（{natal_kw}）、今日のトランジットは{transit_sign}（{transit_kw}）。"
        f"{elem_msg}"
        f"ふだんとは少し違うアプローチで動くと、新しい流れが開けます。"
    )
