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
def get_aspects(planets, exclude_moon=False):
    """
    天体同士のアスペクトを計算する。
    exclude_moon=True の場合、渡された planets 辞書から「月」キーを除外してから計算する。
    出生時刻不明で月の度数が不正確なときに使う。
    （トランジットの「今日の月」など、別の月を含む辞書には影響しない）
    """
    if exclude_moon:
        planets = {k: v for k, v in planets.items() if k != "月"}
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

# ---------- グランドトライン・グランドクロス判定 ----------

MODES = {
    "活動": ["牡羊座", "蟹座", "天秤座", "山羊座"],
    "固定": ["牡牛座", "獅子座", "蠍座", "水瓶座"],
    "柔軟": ["双子座", "乙女座", "射手座", "魚座"],
}

def _get_sign_from_lon(lon_deg):
    return SIGNS[int((lon_deg % 360) / 30)]

def detect_grand_trine(planets: dict, orb: float = 8.0, exclude_moon: bool = False) -> list:
    """
    グランドトライン（大三角）を検出する
    同じエレメントの3天体がそれぞれ120°を形成
    同じエレメントが複数ある場合は最初の1つだけ返す
    exclude_moon=True の場合、「月」を検出対象から除外する（出生時刻不明時用）
    返り値：[{"planets": [p1,p2,p3], "element": "火", "signs": [s1,s2,s3]}]
    """
    if exclude_moon:
        planets = {k: v for k, v in planets.items() if k != "月"}
    results = []
    found_elements = {}  # 同じエレメントの重複を防ぐ（dict：エレメント→最優先候補）
    planet_list = list(planets.items())

    for i in range(len(planet_list)):
        for j in range(i+1, len(planet_list)):
            for k in range(j+1, len(planet_list)):
                p1, d1 = planet_list[i]
                p2, d2 = planet_list[j]
                p3, d3 = planet_list[k]

                def diff(a, b):
                    d = abs(a - b) % 360
                    return d if d <= 180 else 360 - d

                d12 = diff(d1, d2)
                d23 = diff(d2, d3)
                d13 = diff(d1, d3)

                if (abs(d12 - 120) <= orb and
                    abs(d23 - 120) <= orb and
                    abs(d13 - 120) <= orb):

                    s1 = _get_sign_from_lon(d1)
                    s2 = _get_sign_from_lon(d2)
                    s3 = _get_sign_from_lon(d3)

                    elems = set([ELEMENTS.get(s1), ELEMENTS.get(s2), ELEMENTS.get(s3)])
                    elem = elems.pop() if len(elems) == 1 else "混合"

                    personal = {"太陽", "月", "水星", "金星", "火星"}
                    personal_count = sum(1 for p in [p1, p2, p3] if p in personal or p.replace("T_","") in personal)

                    if elem not in found_elements:
                        found_elements[elem] = {
                            "planets": [p1, p2, p3],
                            "element": elem,
                            "signs": [s1, s2, s3],
                            "personal_count": personal_count,
                        }
                    else:
                        # 同じエレメントで個人天体が多い方を優先
                        if personal_count > found_elements[elem]["personal_count"]:
                            found_elements[elem] = {
                                "planets": [p1, p2, p3],
                                "element": elem,
                                "signs": [s1, s2, s3],
                                "personal_count": personal_count,
                            }

    results = list(found_elements.values())
    return results


def detect_grand_cross(planets: dict, orb: float = 8.0, exclude_moon: bool = False) -> list:
    """
    グランドクロス（大十字）を検出する
    4天体がスクエア×4＋オポジション×2を形成
    exclude_moon=True の場合、「月」を検出対象から除外する（出生時刻不明時用）
    返り値：[{"planets": [p1,p2,p3,p4], "mode": "活動", "signs": [...]}]
    """
    if exclude_moon:
        planets = {k: v for k, v in planets.items() if k != "月"}
    results = []
    planet_list = list(planets.items())

    for i in range(len(planet_list)):
        for j in range(i+1, len(planet_list)):
            for k in range(j+1, len(planet_list)):
                for l in range(k+1, len(planet_list)):
                    p1, d1 = planet_list[i]
                    p2, d2 = planet_list[j]
                    p3, d3 = planet_list[k]
                    p4, d4 = planet_list[l]

                    def diff(a, b):
                        d = abs(a - b) % 360
                        return d if d <= 180 else 360 - d

                    pairs = [
                        diff(d1, d2), diff(d1, d3), diff(d1, d4),
                        diff(d2, d3), diff(d2, d4), diff(d3, d4)
                    ]

                    # グランドクロス：オポジション×2、スクエア×4
                    opp_count = sum(1 for d in pairs if abs(d - 180) <= orb)
                    sq_count = sum(1 for d in pairs if abs(d - 90) <= orb)

                    if opp_count >= 2 and sq_count >= 4:
                        s1 = _get_sign_from_lon(d1)
                        s2 = _get_sign_from_lon(d2)
                        s3 = _get_sign_from_lon(d3)
                        s4 = _get_sign_from_lon(d4)

                        # モード確認
                        mode_found = "不定"
                        for mode_name, mode_signs in MODES.items():
                            matched = sum(1 for s in [s1,s2,s3,s4] if s in mode_signs)
                            if matched >= 3:
                                mode_found = mode_name
                                break

                        results.append({
                            "planets": [p1, p2, p3, p4],
                            "mode": mode_found,
                            "signs": [s1, s2, s3, s4],
                        })

    # 3天体以上を共有する十字は同一のグランドクロスとみなして統合する
    # （例：月と金星がコンジャンクションの場合、ほぼ同じ十字が2つ検出されるのを防ぐ）
    merged = []
    for r in results:
        target = None
        for m in merged:
            if r["mode"] == m["mode"] and len(set(r["planets"]) & set(m["planets"])) >= 3:
                target = m
                break
        if target is None:
            merged.append({
                "planets": list(r["planets"]),
                "mode": r["mode"],
                "signs": list(r["signs"]),
            })
        else:
            for p, s in zip(r["planets"], r["signs"]):
                if p not in target["planets"]:
                    target["planets"].append(p)
                    target["signs"].append(s)

    return merged


def detect_special_patterns(natal: dict, transit: dict = None, exclude_moon: bool = False) -> dict:
    """
    ネイタル単体＋トランジット込みの両方でグランドトライン・グランドクロスを検出
    exclude_moon=True の場合、ネイタルの「月」を除外する（出生時刻不明時用）。
    トランジット側の「今日の月」（T_月）は度数が正確なので除外されない。
    """
    results = {
        "natal_grand_trine": detect_grand_trine(natal, exclude_moon=exclude_moon),
        "natal_grand_cross": detect_grand_cross(natal, exclude_moon=exclude_moon),
        "transit_grand_trine": [],
        "transit_grand_cross": [],
    }
    if transit:
        combined = {**natal, **{f"T_{k}": v for k, v in transit.items()}}
        results["transit_grand_trine"] = detect_grand_trine(combined, exclude_moon=exclude_moon)
        results["transit_grand_cross"] = detect_grand_cross(combined, exclude_moon=exclude_moon)

    return results
