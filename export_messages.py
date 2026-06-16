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

# ===== タロットメッセージ =====
TAROT_BASE = {
    "fool": "新しい始まり。自由な発想で進みましょう。",
    "magician": "現実を動かす力。行動が結果を引き寄せます。",
    "high_priestess": "直感が鍵。静かに内面を見つめましょう。",
    "empress": "豊かさと愛。安心できる環境が整います。",
    "emperor": "安定と支配。自分の軸を持ちましょう。",
    "hierophant": "伝統と学び。基本に立ち返る時です。",
    "lovers": "選択と調和。心の声に従いましょう。",
    "chariot": "前進と勝利。迷わず進む力があります。",
    "strength": "内なる強さ。優しさが力になります。",
    "hermit": "内省の時間。答えは自分の中にあります。",
    "wheel_of_fortune": "運命の転換期。流れに乗りましょう。",
    "justice": "公平と判断。冷静な決断が必要です。",
    "hanged_man": "視点の転換。今は待つことも大切。",
    "death": "終わりと再生。新しいステージへ。",
    "temperance": "調和とバランス。整えることが大事。",
    "devil": "執着と誘惑。冷静に見極めましょう。",
    "tower": "崩壊と覚醒。大きな変化が訪れます。",
    "star": "希望と癒し。未来は明るいです。",
    "moon": "不安と幻想。見えない部分に注意。",
    "sun": "成功と喜び。エネルギーが満ちています。",
    "judgement": "目覚めと再起。過去を超える時。",
    "world": "完成と達成。大きな区切りです。",
}
TAROT_REVERSE = {
    "fool": "無計画さに注意。慎重さが必要です。",
    "magician": "力が空回り。焦らず整えましょう。",
    "high_priestess": "直感が鈍る。情報を見直しましょう。",
    "empress": "甘えすぎに注意。自立がテーマです。",
    "emperor": "支配的になりすぎ。柔軟さを持ちましょう。",
    "hierophant": "常識に縛られすぎ。視野を広げて。",
    "lovers": "迷い・不一致。決断が必要です。",
    "chariot": "暴走注意。コントロールが必要。",
    "strength": "自信不足。内面を整えて。",
    "hermit": "孤立しすぎ。外との繋がりを。",
    "wheel_of_fortune": "流れが停滞。無理に動かない。",
    "justice": "判断ミス。冷静さを取り戻す。",
    "hanged_man": "停滞しすぎ。行動のタイミング。",
    "death": "変化を拒否。手放すことが必要。",
    "temperance": "バランス崩壊。整える意識を。",
    "devil": "依存・執着。距離を取るべき。",
    "tower": "混乱長引く。冷静な立て直しを。",
    "star": "希望薄れる。小さな光を見て。",
    "moon": "不安増大。事実を確認する。",
    "sun": "空回り。無理しすぎに注意。",
    "judgement": "決断遅れ。覚悟が必要。",
    "world": "未完成。もう一歩が必要。",
}

# ===== 数秘術メッセージ =====
LIFE_PATH_MSG = {
    1: {"title":"1：リーダー・開拓者","message":"自分の力で道を切り開く、先駆者の魂を持っています。","talent":"独立心・リーダーシップ・創造力","challenge":"頑固さや孤独感に注意。人の意見も取り入れながら進みましょう。","keywords":"独立・創造・先駆者・自信・行動"},
    2: {"title":"2：調和・協力者","message":"人と人をつなぐ、調和の橋渡し役です。","talent":"協調性・共感力・外交力","challenge":"優柔不断や依存心に注意。自分の気持ちも大切にしましょう。","keywords":"調和・協力・共感・平和"},
    3: {"title":"3：表現者・クリエイター","message":"喜びと創造性を周囲に広げる、表現の天才です。","talent":"表現力・創造性・コミュニケーション力","challenge":"散漫になりやすい面も。一つのことを深めましょう。","keywords":"表現・創造・喜び・芸術"},
    4: {"title":"4：建設者・職人","message":"地道な努力と誠実さで、確かなものを築き上げる魂です。","talent":"忍耐力・誠実さ・組織力","challenge":"頑固さや融通のなさに注意。柔軟性を持ちましょう。","keywords":"安定・努力・誠実・信頼"},
    5: {"title":"5：自由人・冒険者","message":"自由と変化を愛する、冒険の魂です。","talent":"適応力・好奇心・行動力・多才さ","challenge":"落ち着きのなさや飽き性に注意。","keywords":"自由・変化・冒険・好奇心"},
    6: {"title":"6：愛情・奉仕者","message":"愛と調和を大切にする、奉仕の魂です。","talent":"愛情深さ・責任感・美的センス","challenge":"自己犠牲になりすぎる面も。自分も大切に。","keywords":"愛・奉仕・家族・美・責任"},
    7: {"title":"7：探求者・哲学者","message":"真実と知恵を探求する、内省の魂です。","talent":"分析力・直感・探求心・精神性","challenge":"孤立感や完璧主義に注意。","keywords":"探求・知恵・内省・直感"},
    8: {"title":"8：達成者・実力者","message":"物質的な成功と権力を手にする、達成の魂です。","talent":"実行力・リーダーシップ・ビジネス感覚","challenge":"権力欲や物質主義に注意。","keywords":"成功・権力・達成・ビジネス"},
    9: {"title":"9：完成者・人道主義者","message":"すべてを包み込む、博愛の魂です。","talent":"慈悲心・芸術性・知恵・包容力","challenge":"自己犠牲や感情的になりすぎる面も。","keywords":"博愛・完成・芸術・慈悲"},
    11: {"title":"11：直感の達人・マスターナンバー","message":"霊的な直感と啓示を持つ、マスターナンバーの魂です。","talent":"直感・霊感・インスピレーション","challenge":"神経質になりやすい面も。地に足をつけて。","keywords":"直感・啓示・精神性・マスター"},
    22: {"title":"22：マスタービルダー・マスターナンバー","message":"大きな夢を現実に変える、最強のマスターナンバーです。","talent":"ビジョン・実行力・組織力","challenge":"プレッシャーを感じやすい面も。","keywords":"夢・現実化・マスター・建設"},
    33: {"title":"33：マスターティーチャー・マスターナンバー","message":"愛と奉仕の最高形、マスターティーチャーの魂です。","talent":"愛・癒し・教え・慈悲・奉仕","challenge":"自己犠牲になりすぎる面も。","keywords":"愛・癒し・教師・慈悲・マスター"},
}
BIRTHDAY_MSG = {
    1:"生まれた日の才能：新しいことを始める力・リーダーシップ・独立心が強い",
    2:"生まれた日の才能：協調性・共感力・パートナーシップを大切にする",
    3:"生まれた日の才能：表現力・コミュニケーション力・楽しむ才能",
    4:"生まれた日の才能：誠実さ・忍耐力・コツコツ積み上げる力",
    5:"生まれた日の才能：適応力・好奇心・変化を楽しむ力",
    6:"生まれた日の才能：愛情深さ・責任感・人を大切にする力",
    7:"生まれた日の才能：分析力・直感・深く考える力",
    8:"生まれた日の才能：実行力・ビジネス感覚・目標達成力",
    9:"生まれた日の才能：包容力・慈悲心・大きな視野",
    11:"生まれた日の才能：高い直感・インスピレーション・精神性（マスターナンバー）",
    22:"生まれた日の才能：大きな夢を現実にする力（マスターナンバー）",
    33:"生まれた日の才能：愛と癒しの才能（マスターナンバー）",
}
RULER_MSG = {
    1:"生まれた年の使命：自分らしい道を切り開くこと",
    2:"生まれた年の使命：人との調和とパートナーシップ",
    3:"生まれた年の使命：表現と創造で喜びを広げること",
    4:"生まれた年の使命：地道な努力で確かな基盤を築くこと",
    5:"生まれた年の使命：自由と変化の中で経験を積むこと",
    6:"生まれた年の使命：愛と奉仕で周囲を幸せにすること",
    7:"生まれた年の使命：真実と知恵を探求すること",
    8:"生まれた年の使命：大きな成功と社会貢献",
    9:"生まれた年の使命：博愛と完成に向けて歩むこと",
    11:"生まれた年の使命：直感と霊感で人々を導くこと（マスターナンバー）",
    22:"生まれた年の使命：大きなビジョンを現実に変えること（マスターナンバー）",
    33:"生まれた年の使命：愛と癒しで人々を導くこと（マスターナンバー）",
}

# ===== JSONに書き出す =====
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
    "tarot_base": TAROT_BASE,
    "tarot_reverse": TAROT_REVERSE,
    "numerology_life_path": {str(k): v for k, v in LIFE_PATH_MSG.items()},
    "numerology_birthday": {str(k): v for k, v in BIRTHDAY_MSG.items()},
    "numerology_ruler": {str(k): v for k, v in RULER_MSG.items()},
}

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "messages_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ messages_data.json を作成しました: {output_path}")
