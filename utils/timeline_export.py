# -*- coding: utf-8 -*-
"""
utils/timeline_export.py
========================
Luna-compass → 宇宙タイムライン(cosmic-timeline)連携モジュール。

出生データから skyfield(de406)で木星回帰・サターンリターンの
正確な日付を計算し、タイムラインの「👤 あなた」レイヤー用
events.json を生成する。

生成されるJSONは mode:"append" 形式なので、タイムライン側の
内蔵28イベント(宇宙・占星術・神話・日本史)に自動で合流する。
index.html と同じフォルダに events.json として置くだけでよい。
"""
import datetime
import json

import numpy as np
from skyfield.framelib import ecliptic_frame

from utils import astro

# ============================================================
# 天体計算
# ============================================================
_BODY_KEYS = {
    "jupiter": "jupiter barycenter",
    "saturn": "saturn barycenter",
}


def _angdiff(a, b):
    """黄経差を -180〜+180 に正規化"""
    return ((a - b + 180.0) % 360.0) - 180.0


def _lon_series(body_key: str, t):
    """指定天体の黄経(配列対応)"""
    earth = astro.EPH["earth"]
    pos = earth.at(t).observe(astro.EPH[body_key])
    _, lon, _ = pos.frame_latlon(ecliptic_frame)
    return np.atleast_1d(lon.degrees) % 360.0


def _times_from_offsets(base: datetime.datetime, day_offsets):
    """基準日時 + 経過日数(配列)から skyfield 時刻配列を作る"""
    day_offsets = np.asarray(day_offsets, dtype=float)
    return astro.TS.utc(
        base.year, base.month, base.day + day_offsets, base.hour, base.minute
    )


def _find_returns(body: str, birth_utc: datetime.datetime,
                  until: datetime.datetime, coarse_days: float = 5.0):
    """
    出生時の黄経に天体が戻る日付リストを返す(日精度)。
    逆行による複数回通過は1つの回帰にまとめる(最初の通過日を採用)。
    """
    key = _BODY_KEYS[body]

    # 出生時の黄経
    t0 = _times_from_offsets(birth_utc, [0.0])
    natal_lon = float(_lon_series(key, t0)[0])

    # 粗いスキャン(出生180日後〜現在)
    start_off = 180.0
    total_days = (until - birth_utc).days
    if total_days <= start_off:
        return []
    offsets = np.arange(start_off, total_days, coarse_days)
    t = _times_from_offsets(birth_utc, offsets)
    diffs = _angdiff(_lon_series(key, t), natal_lon)

    # 0度を上向きに横切る点を検出(±180の巻き戻りは除外)
    crossings = []
    for i in range(len(diffs) - 1):
        if diffs[i] < 0 <= diffs[i + 1] and abs(diffs[i]) < 45 and abs(diffs[i + 1]) < 45:
            # 日単位で精密化
            fine = np.arange(offsets[i], offsets[i + 1] + 1.0, 1.0)
            tf = _times_from_offsets(birth_utc, fine)
            fd = np.abs(_angdiff(_lon_series(key, tf), natal_lon))
            best = fine[int(np.argmin(fd))]
            crossings.append(birth_utc + datetime.timedelta(days=float(best)))

    # 逆行由来の近接クロスをクラスタリング(3年以内は同一回帰とみなす)
    returns = []
    for d in crossings:
        if returns and (d - returns[-1]).days < 365 * 3:
            continue
        returns.append(d)
    return returns


# ============================================================
# イベント生成
# ============================================================
def _ybp(d: datetime.date, today: datetime.date) -> float:
    return (today - d).days / 365.2425


def generate_personal_events(user_info: dict, today: datetime.date = None) -> list:
    """
    user_info(luna_web.pyの辞書そのまま)からパーソナルイベントを生成。
    必要キー: birthday, birth_hour, birth_minute, tz_offset, name(任意)
    """
    today = today or datetime.date.today()
    birthday: datetime.date = user_info["birthday"]
    name = (user_info.get("name") or "").strip()
    who = f"{name}さん" if name else "あなた"

    birth_utc = datetime.datetime(
        birthday.year, birthday.month, birthday.day,
        user_info.get("birth_hour", 12), user_info.get("birth_minute", 0),
    ) - datetime.timedelta(hours=user_info.get("tz_offset", 9))
    until = datetime.datetime(today.year, today.month, today.day)

    events = []

    # --- 誕生(出生時の太陽サイン入り) ---
    t_birth = astro.make_ts_from_local(
        birthday, user_info.get("birth_hour", 12),
        user_info.get("birth_minute", 0), user_info.get("tz_offset", 9),
    )
    sun_sign, _, _ = astro.get_sun_info(t_birth)
    events.append({
        "ybp": _ybp(birthday, today),
        "when": f"{birthday.year}年{birthday.month}月{birthday.day}日",
        "layer": "personal", "era": f"{who}の物語",
        "title": "誕生", "icon": "🌟", "hue": 160, "sat": 55,
        "text": f"138億年の物語の続きとして、{who}が生まれました。"
                f"この日、太陽は{sun_sign}にありました。"
                "この瞬間の空の配置が、あなたのネイタルチャートです。",
        "trivia": "あなたの体を作る原子は、かつて星の中心で作られたものです。"
                  "文字通り、星のかけらがこの物語を読んでいます。",
    })

    # --- 木星回帰(skyfieldによる正確な日付) ---
    for n, d in enumerate(_find_returns("jupiter", birth_utc, until), start=1):
        age = int((d.date() - birthday).days / 365.2425)
        events.append({
            "ybp": _ybp(d.date(), today),
            "when": f"{d.year}年{d.month}月{d.day}日({age}歳)",
            "layer": "personal", "era": "拡大と幸運のサイクル",
            "title": f"第{n}回 木星回帰", "icon": "🪐", "hue": 45, "sat": 55,
            "text": "木星が出生位置に正確に戻った日。視野が広がり、"
                    "新しいチャンスが巡ってくる約12年に一度の節目です。",
            "trivia": "木星は太陽系最大の惑星。占星術では「大吉星(グレーター・ベネフィック)」と呼ばれます。",
        })

    # --- サターンリターン(skyfieldによる正確な日付) ---
    for n, d in enumerate(_find_returns("saturn", birth_utc, until), start=1):
        age = int((d.date() - birthday).days / 365.2425)
        events.append({
            "ybp": _ybp(d.date(), today),
            "when": f"{d.year}年{d.month}月{d.day}日({age}歳)",
            "layer": "personal", "era": "試練と成熟のサイクル",
            "title": f"第{n}回 サターンリターン", "icon": "🪨", "hue": 230, "sat": 40,
            "text": "土星が出生位置に正確に戻った日。人生の土台を見直し、"
                    "本当に大切なものを選び直す約29.5年に一度の大きな節目です。",
            "trivia": "土星の環は主に氷の粒でできていて、厚さはわずか数十メートル。"
                      "巨大に見えるものが、実は繊細な構造でできています。",
        })

    events.sort(key=lambda e: -e["ybp"])
    return events


def build_export_json(user_info: dict) -> str:
    """タイムラインに置く events.json の中身(文字列)を返す"""
    data = {
        "layers": {
            "personal": {"label": "あなた", "symbol": "👤", "color": "#7ee8c9"}
        },
        "mode": "append",   # タイムライン内蔵の28イベントに追記合流する
        "events": generate_personal_events(user_info),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
