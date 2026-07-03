# -*- coding: utf-8 -*-
"""
utils/shichusuimei.py - 四柱推命 命式計算モジュール v0.2

Luna-compass 用。四柱(年・月・日・時)の干支、蔵干、通変星、五行バランスを算出する。

【v0.2 変更点】
- 節入りを太陽黄経(Meeus略算式)による精密計算に変更。誤差±数分。
  検証: 2021年・2025年の立春が「2月3日」となる稀なケースを正しく再現済み。
- 年柱・月柱を節入り時刻ベース(分単位)で判定。
- 節入り境界±1時間以内の出生には warning フラグを返す(出生時刻の誤差で
  月柱が変わりうるため、鑑定時に確認を促す用途)。

【残課題】
- 蔵干テーブルは流派差あり(特に申・亥の初気)。本気は共通。
- 夜子時(23時以降を翌日の日柱扱い)は未実装。採用流派なら要オプション化。
- 時柱は日本標準時ベース。地方時(経度補正)を使う流派は要調整。
"""
import math
from datetime import datetime, timedelta
from functools import lru_cache

# ============================================================
# 基本テーブル
# ============================================================

JIKKAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JUNISHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

KAN_GOGYO = {
    "甲": ("木", True),  "乙": ("木", False),
    "丙": ("火", True),  "丁": ("火", False),
    "戊": ("土", True),  "己": ("土", False),
    "庚": ("金", True),  "辛": ("金", False),
    "壬": ("水", True),  "癸": ("水", False),
}

SHI_GOGYO = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 蔵干(初気→本気) ※流派差あり。本気(末尾)は共通。
ZOKAN = {
    "子": ["壬", "癸"],
    "丑": ["癸", "辛", "己"],
    "寅": ["戊", "丙", "甲"],
    "卯": ["甲", "乙"],
    "辰": ["乙", "癸", "戊"],
    "巳": ["戊", "庚", "丙"],
    "午": ["丙", "己", "丁"],
    "未": ["丁", "乙", "己"],
    "申": ["戊", "壬", "庚"],
    "酉": ["庚", "辛"],
    "戌": ["辛", "丁", "戊"],
    "亥": ["甲", "壬"],
}

SEI = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KOKU = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 節(月支切替)の太陽黄経と月支
SETSU = [
    (315, "寅", "立春", 2), (345, "卯", "啓蟄", 3), (15, "辰", "清明", 4),
    (45, "巳", "立夏", 5), (75, "午", "芒種", 6), (105, "未", "小暑", 7),
    (135, "申", "立秋", 8), (165, "酉", "白露", 9), (195, "戌", "寒露", 10),
    (225, "亥", "立冬", 11), (255, "子", "大雪", 12), (285, "丑", "小寒", 1),
]

DAY_ANCHOR = datetime(1949, 10, 1)  # 甲子の日(検証: 2000-01-01=戊午と整合)

GOKOTON = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊",
           "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬",
           "戊": "甲", "癸": "甲"}

GOSOTON = {"甲": "甲", "己": "甲", "乙": "丙", "庚": "丙",
           "丙": "戊", "辛": "戊", "丁": "庚", "壬": "庚",
           "戊": "壬", "癸": "壬"}

# ============================================================
# 十二運・空亡
# ============================================================

JUNIUN_SEQ = ["長生", "沐浴", "冠帯", "建禄", "帝旺", "衰",
              "病", "死", "墓", "絶", "胎", "養"]

# 日干ごとの長生の地支(陽干は順行、陰干は逆行)
CHOSEI_START = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",   # 陽干・順行
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",   # 陰干・逆行
}

def juniun(nikkan, shi):
    """日干から見た地支の十二運"""
    start_idx = JUNISHI.index(CHOSEI_START[nikkan])
    shi_idx = JUNISHI.index(shi)
    is_yang = KAN_GOGYO[nikkan][1]
    step = (shi_idx - start_idx) % 12 if is_yang else (start_idx - shi_idx) % 12
    return JUNIUN_SEQ[step]

def kubo(day_index60):
    """日柱の六十干支インデックスから空亡(旬空)の地支2つを返す"""
    jun_start = day_index60 - (day_index60 % 10)  # 旬首(甲〇の日)
    return JUNISHI[(jun_start + 10) % 12], JUNISHI[(jun_start + 11) % 12]

# 節入り境界の警告しきい値
BOUNDARY_WARN = timedelta(hours=1)


# ============================================================
# 太陽黄経による節入り計算 (Meeus略算式, 誤差±数分)
# ============================================================

def _julian_day(dt_utc):
    y, m = dt_utc.year, dt_utc.month
    d = dt_utc.day + (dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5

def _solar_longitude(dt_utc):
    """視太陽黄経(度)"""
    T = (_julian_day(dt_utc) - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M)
         + 0.000289 * math.sin(3 * M))
    omega = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(omega)) % 360.0

@lru_cache(maxsize=512)
def solar_term_jst(year, target_deg, approx_month):
    """指定黄経の通過時刻(JST)を二分法で求める"""
    lo = datetime(year, approx_month, 4) - timedelta(days=7)
    hi = lo + timedelta(days=14)
    def diff(dt):
        return (_solar_longitude(dt) - target_deg + 180) % 360 - 180
    for _ in range(60):
        mid = lo + (hi - lo) / 2
        if diff(mid) < 0:
            lo = mid
        else:
            hi = mid
    return lo + timedelta(hours=9)  # UTC→JST

@lru_cache(maxsize=256)
def _terms_around(year):
    """前年の大雪〜当年の大雪まで、(節入りJST, 月支, 節名, 節年) を時系列で返す。
    節年 = その節が属する四柱推命上の年(立春で切替)。"""
    events = []
    # 前年: 大雪(12月・子月) と 小寒は当年1月
    events.append((solar_term_jst(year - 1, 255, 12), "子", "大雪", year - 1))
    events.append((solar_term_jst(year, 285, 1), "丑", "小寒", year - 1))
    for deg, shi, name, month in SETSU:
        if name in ("大雪", "小寒"):
            continue
        t = solar_term_jst(year, deg, month)
        # 立春以降は当年、それより前(=存在しない)は考慮不要
        events.append((t, shi, name, year))
    events.append((solar_term_jst(year, 255, 12), "子", "大雪", year))
    events.sort(key=lambda e: e[0])
    return events

def find_setsu(birth):
    """出生時刻が属する節を返す: (月支, 節年, 直近節入りとの時間差, 節名)"""
    events = _terms_around(birth.year)
    current = None
    nearest_gap = None
    for t, shi, name, setsu_year in events:
        if t <= birth:
            current = (shi, setsu_year, name, t)
        gap = abs((birth - t).total_seconds())
        if nearest_gap is None or gap < nearest_gap:
            nearest_gap = gap
    if current is None:  # 年初で前年の小寒より前 → さらに前年の大雪(子月)
        prev = _terms_around(birth.year - 1)
        for t, shi, name, setsu_year in prev:
            if t <= birth:
                current = (shi, setsu_year, name, t)
    shi, setsu_year, name, t = current
    return shi, setsu_year, timedelta(seconds=nearest_gap), name


# ============================================================
# 四柱算出
# ============================================================

def _kanshi(index60):
    return JIKKAN[index60 % 10], JUNISHI[index60 % 12]

def year_pillar(setsu_year):
    """節年(立春切替済み)から年柱"""
    return _kanshi((setsu_year - 4) % 60)

def month_pillar(month_shi, year_kan):
    tora_idx = JIKKAN.index(GOKOTON[year_kan])
    shi_order = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    offset = shi_order.index(month_shi)
    return JIKKAN[(tora_idx + offset) % 10], month_shi

def day_pillar(birth):
    delta = (birth.date() - DAY_ANCHOR.date()).days
    return _kanshi(delta % 60)

def hour_pillar(birth, day_kan):
    shi_idx = ((birth.hour + 1) // 2) % 12
    hour_shi = JUNISHI[shi_idx]
    hour_kan = JIKKAN[(JIKKAN.index(GOSOTON[day_kan]) + shi_idx) % 10]
    return hour_kan, hour_shi


# ============================================================
# 通変星・五行バランス
# ============================================================

def tsuhensei(nikkan, target_kan):
    e1, y1 = KAN_GOGYO[nikkan]
    e2, y2 = KAN_GOGYO[target_kan]
    same_pol = (y1 == y2)
    if e1 == e2:
        return "比肩" if same_pol else "劫財"
    if SEI[e1] == e2:
        return "食神" if same_pol else "傷官"
    if KOKU[e1] == e2:
        return "偏財" if same_pol else "正財"
    if KOKU[e2] == e1:
        return "偏官" if same_pol else "正官"
    if SEI[e2] == e1:
        return "偏印" if same_pol else "印綬"
    return "?"


def build_meishiki(birth: datetime):
    """命式一式を dict で返す。birth は JST naive datetime。"""
    month_shi, setsu_year, boundary_gap, setsu_name = find_setsu(birth)
    y_kan, y_shi = year_pillar(setsu_year)
    m_kan, m_shi = month_pillar(month_shi, y_kan)
    d_kan, d_shi = day_pillar(birth)
    h_kan, h_shi = hour_pillar(birth, d_kan)

    pillars = {
        "年柱": (y_kan, y_shi),
        "月柱": (m_kan, m_shi),
        "日柱": (d_kan, d_shi),
        "時柱": (h_kan, h_shi),
    }

    stars = {}
    for name, (kan, shi) in pillars.items():
        honki = ZOKAN[shi][-1]
        if name == "日柱":
            stars[name] = {"天干": "日主(日干)", "蔵干本気": tsuhensei(d_kan, honki)}
        else:
            stars[name] = {"天干": tsuhensei(d_kan, kan), "蔵干本気": tsuhensei(d_kan, honki)}

    gogyo_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for kan, shi in pillars.values():
        gogyo_count[KAN_GOGYO[kan][0]] += 1
        gogyo_count[SHI_GOGYO[shi]] += 1
        gogyo_count[KAN_GOGYO[ZOKAN[shi][-1]][0]] += 1

    # 十二運(日干から見た各柱の地支)
    juniun_map = {name: juniun(d_kan, shi) for name, (kan, shi) in pillars.items()}

    # 空亡(日柱の旬から)
    day_delta = (birth.date() - DAY_ANCHOR.date()).days
    kubo_pair = kubo(day_delta % 60)
    # 命式中で空亡に当たる柱
    kubo_hit = [name for name, (kan, shi) in pillars.items()
                if shi in kubo_pair and name != "日柱"]

    return {
        "四柱": pillars,
        "日干": d_kan,
        "日干五行": KAN_GOGYO[d_kan],
        "蔵干": {name: ZOKAN[shi] for name, (kan, shi) in pillars.items()},
        "通変星": stars,
        "十二運": juniun_map,
        "空亡": kubo_pair,
        "空亡該当柱": kubo_hit,
        "五行バランス": gogyo_count,
        "換算年(立春基準)": setsu_year,
        "節入り境界警告": boundary_gap <= BOUNDARY_WARN,
        "直近節入りとの差": boundary_gap,
    }


# ============================================================
# 大運
# ============================================================

KANSHI_60 = [(JIKKAN[i % 10], JUNISHI[i % 12]) for i in range(60)]

def _kanshi_index(kan, shi):
    """干支から六十干支インデックス(0-59)を求める"""
    ki, si = JIKKAN.index(kan), JUNISHI.index(shi)
    for i in range(60):
        if i % 10 == ki and i % 12 == si:
            return i
    raise ValueError(f"あり得ない干支: {kan}{shi}")

def _neighbor_terms(birth):
    """出生時刻の直前・直後の節入り時刻(JST)を返す"""
    events = _terms_around(birth.year) + _terms_around(birth.year + 1)
    events = sorted(set((t, shi, name, y) for t, shi, name, y in events))
    prev_t, next_t = None, None
    for t, shi, name, y in events:
        if t <= birth:
            prev_t = t
        elif next_t is None:
            next_t = t
    if prev_t is None:  # 年初など
        for t, shi, name, y in sorted(_terms_around(birth.year - 1)):
            if t <= birth:
                prev_t = t
    return prev_t, next_t

def calc_daiun(birth, gender, n_cycles=10):
    """大運を計算する。

    gender: "男" or "女"
    戻り値: {
        "順逆": "順行"/"逆行",
        "立運": (年, 月),          # 満年齢ベース
        "大運": [ {開始年齢, 干支, 天干, 地支, 通変星, 十二運}, ... ]
    }

    【流派メモ】立運は「節入りまでの日数÷3(1日=4ヶ月)」で算出。
    端数の丸めは流派差があるため、月数は round() で処理している。
    """
    m = build_meishiki(birth)
    y_kan, _ = m["四柱"]["年柱"]
    d_kan = m["日干"]
    m_kan, m_shi = m["四柱"]["月柱"]

    year_is_yang = KAN_GOGYO[y_kan][1]
    forward = (year_is_yang and gender == "男") or (not year_is_yang and gender == "女")

    prev_t, next_t = _neighbor_terms(birth)
    if forward:
        span_days = (next_t - birth).total_seconds() / 86400.0
    else:
        span_days = (birth - prev_t).total_seconds() / 86400.0

    # 3日=1年、1日=4ヶ月
    total_months = span_days * 4.0
    ritsuun_years = int(total_months // 12)
    ritsuun_months = int(round(total_months - ritsuun_years * 12))
    if ritsuun_months == 12:
        ritsuun_years += 1
        ritsuun_months = 0

    # 大運の干支: 月柱から順行/逆行
    base_idx = _kanshi_index(m_kan, m_shi)
    daiun_list = []
    for i in range(1, n_cycles + 1):
        idx = (base_idx + i) % 60 if forward else (base_idx - i) % 60
        kan, shi = KANSHI_60[idx]
        start_age = ritsuun_years + (i - 1) * 10
        daiun_list.append({
            "開始年齢": start_age,
            "干支": f"{kan}{shi}",
            "天干": kan,
            "地支": shi,
            "通変星": tsuhensei(d_kan, kan),
            "十二運": juniun(d_kan, shi),
        })

    return {
        "順逆": "順行" if forward else "逆行",
        "立運": (ritsuun_years, ritsuun_months),
        "大運": daiun_list,
    }


# ============================================================
# 納音・月令・年運
# ============================================================

NATCHIN = [
    "海中金", "炉中火", "大林木", "路傍土", "剣鋒金",
    "山頭火", "澗下水", "城頭土", "白鑞金", "楊柳木",
    "泉中水", "屋上土", "霹靂火", "松柏木", "長流水",
    "沙中金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大駅土", "釵釧金", "桑柘木",
    "大渓水", "沙中土", "天上火", "石榴木", "大海水",
]

def natchin(kan, shi):
    """干支の納音(2干支で1つ、全30種)"""
    return NATCHIN[_kanshi_index(kan, shi) // 2]

def getsurei(nikkan, month_shi):
    """月令: 日干が生まれ月の季節から受ける力(旺相休囚死)。
    旺・相なら「得令」、それ以外は「失令」。"""
    e = KAN_GOGYO[nikkan][0]          # 日干の五行
    s = SHI_GOGYO[month_shi]          # 月支(季節)の五行
    if e == s:
        state = "旺"
    elif SEI[s] == e:                 # 季節が日干を生じる
        state = "相"
    elif SEI[e] == s:                 # 日干が季節を生じる(漏らす)
        state = "休"
    elif KOKU[e] == s:                # 日干が季節を剋す
        state = "囚"
    else:                             # 季節が日干を剋す
        state = "死"
    return state, state in ("旺", "相")

def calc_nenun(birth, gender, start_year=None, n_years=10):
    """年運(歳運)を計算する。

    各年について: 年干支(立春基準)・通変星・十二運・納音・
    空亡該当・その年に属する大運 を返す。
    ※各年の年齢は「その年に迎える満年齢」の目安表示。
    """
    m = build_meishiki(birth)
    d_kan = m["日干"]
    day_delta = (birth.date() - DAY_ANCHOR.date()).days
    kubo_pair = kubo(day_delta % 60)

    daiun = calc_daiun(birth, gender)
    ritsuun_y = daiun["立運"][0]

    if start_year is None:
        start_year = datetime.now().year

    result = []
    for y in range(start_year, start_year + n_years):
        kan, shi = _kanshi((y - 4) % 60)
        age = y - birth.year  # その年に迎える満年齢(目安)
        # その年齢が属する大運
        current_daiun = None
        for dx in daiun["大運"]:
            if dx["開始年齢"] <= age < dx["開始年齢"] + 10:
                current_daiun = dx["干支"]
                break
        if current_daiun is None and age < ritsuun_y:
            current_daiun = "(立運前)"
        result.append({
            "西暦": y,
            "年齢": age,
            "干支": f"{kan}{shi}",
            "通変星": tsuhensei(d_kan, kan),
            "十二運": juniun(d_kan, shi),
            "納音": natchin(kan, shi),
            "空亡": shi in kubo_pair,
            "大運": current_daiun or "-",
        })
    return result


# ============================================================
# 干支の関係(干合・支合・三合・刑・冲・害・破)
# ============================================================

KANGO = {frozenset(["甲", "己"]): "土", frozenset(["乙", "庚"]): "金",
         frozenset(["丙", "辛"]): "水", frozenset(["丁", "壬"]): "木",
         frozenset(["戊", "癸"]): "火"}

SHIGO = [frozenset(p) for p in
         [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]]

SANGO = {frozenset(["申", "子", "辰"]): "水局", frozenset(["寅", "午", "戌"]): "火局",
         frozenset(["巳", "酉", "丑"]): "金局", frozenset(["亥", "卯", "未"]): "木局"}

SHICHICHU = [frozenset(p) for p in
             [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]]

ROKUGAI = [frozenset(p) for p in
           [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]]

HA = [frozenset(p) for p in
      [("子", "酉"), ("丑", "辰"), ("寅", "亥"), ("卯", "午"), ("巳", "申"), ("戌", "未")]]

# 三刑: 寅巳申 / 丑戌未 のペア、子卯の刑、自刑(辰午酉亥)
SANKEI_GROUPS = [("寅", "巳", "申"), ("丑", "戌", "未")]
SHIKEI_PAIR = frozenset(["子", "卯"])
JIKEI = ["辰", "午", "酉", "亥"]

def detect_kankei(pillars):
    """四柱間の干合・支合・三合・刑・冲・害・破を検出する。
    pillars: {"年柱": (干, 支), ...}
    戻り値: [{"種類", "内容", "柱"}] のリスト
    """
    names = list(pillars.keys())
    findings = []

    # --- 干合(天干のペア) ---
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            k1, k2 = pillars[names[i]][0], pillars[names[j]][0]
            pair = frozenset([k1, k2])
            if pair in KANGO:
                findings.append({"種類": "干合", "内容": f"{k1}と{k2}(化{KANGO[pair]})",
                                 "柱": f"{names[i]}×{names[j]}"})

    # --- 地支のペア関係 ---
    pair_defs = [("支合", SHIGO), ("七冲", SHICHICHU), ("六害", ROKUGAI), ("破", HA)]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            s1, s2 = pillars[names[i]][1], pillars[names[j]][1]
            pair = frozenset([s1, s2])
            if len(pair) == 1:
                if s1 in JIKEI:
                    findings.append({"種類": "刑(自刑)", "内容": f"{s1}と{s2}",
                                     "柱": f"{names[i]}×{names[j]}"})
                continue
            for label, table in pair_defs:
                if pair in table:
                    findings.append({"種類": label, "内容": f"{s1}と{s2}",
                                     "柱": f"{names[i]}×{names[j]}"})
            if pair == SHIKEI_PAIR:
                findings.append({"種類": "刑", "内容": f"{s1}と{s2}",
                                 "柱": f"{names[i]}×{names[j]}"})
            for g in SANKEI_GROUPS:
                if s1 in g and s2 in g:
                    findings.append({"種類": "刑", "内容": f"{s1}と{s2}",
                                     "柱": f"{names[i]}×{names[j]}"})

    # --- 三合(3支そろい) ---
    branches = [pillars[n][1] for n in names]
    for group, kyoku in SANGO.items():
        if group.issubset(set(branches)):
            hit = [n for n in names if pillars[n][1] in group]
            findings.append({"種類": "三合", "内容": f"{'・'.join(sorted(group, key=JUNISHI.index))}({kyoku})",
                             "柱": "×".join(hit)})

    return findings


# ============================================================
# 神殺(データ定義方式)
# ============================================================
# 各ルール: {"基準": "日干"|"年支"|"日支"|"月支三合"|"日柱",
#            "表": {基準の値: 該当する支(文字列 or リスト)},
#            "説明": 短い説明}
#
# ★「表」が空({})のものは流派差が大きいため未実装。
#   泰子さんの資料の定表を入れれば、そのまま動きます。
#   基準の種類が足りない場合は言ってください(追加します)。

SHINSATSU_RULES = {
    # ---- 古典の定表で実装済み ----
    "天乙貴人": {"基準": "日干", "説明": "最上の貴人星。困難のとき助けが得られる",
        "表": {"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申",
               "丙": "亥酉", "丁": "亥酉", "壬": "巳卯", "癸": "巳卯", "辛": "午寅"}},
    "月徳貴人": {"基準": "月支三合天干", "説明": "月から授かる徳。穏やかな福徳の星",
        "表": {"火局": "丙", "水局": "壬", "木局": "甲", "金局": "庚"}},
    "文昌貴人": {"基準": "日干", "説明": "学問・文才の星",
        "表": {"甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
               "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}},
    "咸池(桃花)": {"基準": "年支日支三合", "説明": "魅力・人気の星。恋愛面の華やかさ",
        "表": {"水局": "酉", "火局": "卯", "金局": "午", "木局": "子"}},
    "駅馬": {"基準": "年支日支三合", "説明": "移動・変化の星。旅や転居と縁が深い",
        "表": {"水局": "寅", "火局": "申", "金局": "亥", "木局": "巳"}},
    "劫殺": {"基準": "年支日支三合", "説明": "急激な変化を示す星。勝負強さの裏返し",
        "表": {"水局": "巳", "火局": "亥", "金局": "寅", "木局": "申"}},
    "亡神": {"基準": "年支日支三合", "説明": "内側からの変化を示す星。計略・深謀",
        "表": {"水局": "亥", "火局": "巳", "金局": "申", "木局": "寅"}},
    "羊刃": {"基準": "日干", "説明": "強すぎる力の星。使いこなせば大きな武器",
        "表": {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}},
    "金輿禄": {"基準": "日干", "説明": "玉の輿・良縁の星",
        "表": {"甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
               "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅"}},
    "流霞": {"基準": "日干", "説明": "酒食・情に流れやすい暗示の星",
        "表": {"甲": "酉", "乙": "戌", "丙": "未", "丁": "申", "戊": "巳",
               "己": "午", "庚": "辰", "辛": "卯", "壬": "亥", "癸": "寅"}},

    # ---- 流派差が大きいため空枠(泰子さんの定表で埋めてください) ----
    "福星貴人": {"基準": "日干", "説明": "福徳の星", "表": {}},
    "太極貴人": {"基準": "日干", "説明": "探究・宗教性の星", "表": {}},
    "夾禄": {"基準": "日干", "説明": "禄を挟む配置", "表": {}},
    "垣城": {"基準": "年支", "説明": "", "表": {}},
    "推命殺": {"基準": "年支", "説明": "", "表": {}},
    "墳苗": {"基準": "年支", "説明": "", "表": {}},
    "天哭": {"基準": "年支", "説明": "", "表": {}},
    "披頭": {"基準": "年支", "説明": "", "表": {}},
    "年殺": {"基準": "年支", "説明": "咸池と同表の流派もあり", "表": {}},
    "大禍": {"基準": "年支", "説明": "", "表": {}},
    "破砕": {"基準": "年支", "説明": "", "表": {}},
    "病符": {"基準": "年支", "説明": "", "表": {}},
    "飛符": {"基準": "年支", "説明": "", "表": {}},
    "隔角": {"基準": "日支", "説明": "", "表": {}},
    "旌旗": {"基準": "年支", "説明": "", "表": {}},
    "指背": {"基準": "年支", "説明": "", "表": {}},
    "勾神": {"基準": "年支", "説明": "", "表": {}},
    "絞神": {"基準": "年支", "説明": "", "表": {}},
    "呻吟": {"基準": "年支", "説明": "", "表": {}},
    "下情殺": {"基準": "年支", "説明": "", "表": {}},
    "暴敗殺": {"基準": "年支", "説明": "", "表": {}},
}

def _sango_kyoku(shi):
    """支が属する三合局名"""
    for group, kyoku in SANGO.items():
        if shi in group:
            return kyoku
    return None

def detect_shinsatsu(meishiki):
    """命式から神殺を検出する。
    戻り値: [{"神殺", "該当", "説明"}] のリスト
    """
    pillars = meishiki["四柱"]
    d_kan = meishiki["日干"]
    y_shi = pillars["年柱"][1]
    d_shi = pillars["日柱"][1]
    names = list(pillars.keys())
    findings = []

    for name, rule in SHINSATSU_RULES.items():
        table = rule["表"]
        if not table:
            continue  # 未定義はスキップ
        basis = rule["基準"]

        if basis == "日干":
            targets = table.get(d_kan, "")
            for pname in names:
                if pillars[pname][1] in targets:
                    findings.append({"神殺": name, "該当": f"{pname}({pillars[pname][1]})",
                                     "説明": rule["説明"]})

        elif basis == "年支日支三合":
            hit_pillars = set()
            for base_shi, base_label in [(y_shi, "年支"), (d_shi, "日支")]:
                kyoku = _sango_kyoku(base_shi)
                target = table.get(kyoku, "")
                for pname in names:
                    if pillars[pname][1] in target and pname not in hit_pillars:
                        hit_pillars.add(pname)
                        findings.append({"神殺": name,
                                         "該当": f"{pname}({pillars[pname][1]}) [{base_label}基準]",
                                         "説明": rule["説明"]})

        elif basis == "月支三合天干":
            kyoku = _sango_kyoku(pillars["月柱"][1])
            target_kan = table.get(kyoku, "")
            for pname in names:
                if pillars[pname][0] in target_kan:
                    findings.append({"神殺": name, "該当": f"{pname}(天干{pillars[pname][0]})",
                                     "説明": rule["説明"]})

        elif basis in ("年支", "日支"):
            base = y_shi if basis == "年支" else d_shi
            targets = table.get(base, "")
            for pname in names:
                if pillars[pname][1] in targets:
                    findings.append({"神殺": name, "該当": f"{pname}({pillars[pname][1]})",
                                     "説明": rule["説明"]})

    # 魁罡(日柱そのもので判定)
    d_kanshi = pillars["日柱"][0] + pillars["日柱"][1]
    if d_kanshi in ("庚辰", "庚戌", "壬辰", "戊戌"):
        findings.append({"神殺": "魁罡", "該当": f"日柱({d_kanshi})",
                         "説明": "極端な強運の星。頭領運とも"})

    return findings


# ============================================================
# 格局(普通格局: 建禄格・月刃格・八格)
# ============================================================

# 日干の禄(建禄)
ROKU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
        "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}

# 陽干の刃(羊刃)
JIN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}

def calc_kakukyoku(meishiki):
    """普通格局を判定する(子平法の標準方式)。

    優先順:
    1. 月支が日干の禄 → 建禄格
    2. 月支が陽干の刃 → 月刃格
    3. 月支蔵干の透干(本気→中気→初気の順に、年干・月干・時干を確認)
       → その干の通変星を格とする(比劫は格にしないため次候補へ)
    4. 透干なし → 月支本気の通変星を格とする

    ※従格・化気格などの特別格局は未実装(身強身弱の判定方式を要相談)。
    """
    pillars = meishiki["四柱"]
    d_kan = meishiki["日干"]
    m_shi = pillars["月柱"][1]

    # 1. 建禄格
    if ROKU.get(d_kan) == m_shi:
        return {"格局": "建禄格", "根拠": f"月支{m_shi}が日干{d_kan}の禄にあたる"}

    # 2. 月刃格
    if JIN.get(d_kan) == m_shi:
        return {"格局": "月刃格(羊刃格)", "根拠": f"月支{m_shi}が日干{d_kan}の刃にあたる"}

    # 3. 蔵干の透干(本気→中気→初気)
    zokan_list = list(reversed(ZOKAN[m_shi]))  # [本気, (中気,) 初気]
    other_kans = [pillars[p][0] for p in ("年柱", "月柱", "時柱")]
    labels = ["本気", "中気", "初気"]
    for i, zk in enumerate(zokan_list):
        if zk in other_kans:
            star = tsuhensei(d_kan, zk)
            if star in ("比肩", "劫財"):
                continue  # 比劫は格にしない
            return {"格局": f"{star}格",
                    "根拠": f"月支{m_shi}の{labels[i]}{zk}が天干に透っている"}

    # 4. 透干なし → 本気の通変星
    honki = zokan_list[0]
    star = tsuhensei(d_kan, honki)
    if star in ("比肩", "劫財"):
        # 本気が比劫(禄刃に該当しない稀ケース)は中気・初気で代替
        for i, zk in enumerate(zokan_list[1:], start=1):
            s2 = tsuhensei(d_kan, zk)
            if s2 not in ("比肩", "劫財"):
                return {"格局": f"{s2}格",
                        "根拠": f"月支{m_shi}の{labels[i]}{zk}の通変星を採用(本気は比劫のため)"}
    return {"格局": f"{star}格",
            "根拠": f"月支{m_shi}の蔵干は透干せず、本気{honki}の通変星を採用"}


def format_meishiki(m):
    lines = ["=" * 56, "【命式】",
             f"{'':6} {'天干':4} {'地支':4} {'蔵干(初→本気)':16} {'十二運':6} 通変星(天干/蔵干本気)"]
    for name, (kan, shi) in m["四柱"].items():
        zk = "→".join(m["蔵干"][name])
        st = m["通変星"][name]
        ju = m["十二運"][name]
        lines.append(f"{name:6} {kan:4} {shi:4} {zk:16} {ju:6} {st['天干']} / {st['蔵干本気']}")
    e, yang = m["日干五行"]
    lines.append("-" * 56)
    lines.append(f"日干: {m['日干']} ({e}の{'陽' if yang else '陰'})")
    kubo_s = "・".join(m["空亡"])
    hit = f" ← {'/'.join(m['空亡該当柱'])}が該当" if m["空亡該当柱"] else ""
    lines.append(f"空亡: {kubo_s}{hit}")
    lines.append("五行バランス: " + " ".join(f"{k}{v}" for k, v in m["五行バランス"].items()))
    if m["節入り境界警告"]:
        gap_min = int(m["直近節入りとの差"].total_seconds() // 60)
        lines.append(f"⚠ 節入り境界まで約{gap_min}分。出生時刻の誤差で月柱が変わる可能性があります。")
    lines.append("=" * 56)
    return "\n".join(lines)


if __name__ == "__main__":
    tests = [
        ("星川るな(壬子日→帝旺・空亡は寅卯のはず)", datetime(1982, 5, 29, 2, 0)),
        ("甲子日チェック(→沐浴・空亡は戌亥のはず)", datetime(2000, 1, 7, 12, 0)),
    ]
    for name, dt in tests:
        m = build_meishiki(dt)
        print(f"\n■ {name} {dt}")
        print(format_meishiki(m))
