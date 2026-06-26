# tabs/compatibility.py
# タブ3：相性占い

import streamlit as st
import datetime
import io
import swisseph as swe

from utils.astro import (
    make_ts_from_local, get_sun_info, get_moon_info,
    get_body_longitudes_ts, split_sign_degree, get_sign, ELEMENTS
)
from utils.chart import plot_horoscope


# ===== 相性メッセージ辞書 =====

ELEMENT_COMPAT = {
    ("火", "火"): ("🔥🔥 情熱的な組み合わせ", "お互いのエネルギーが共鳴し、刺激的で情熱的な関係です。共に高め合えますが、衝突も起きやすいので、冷静さも大切にしましょう。"),
    ("火", "風"): ("🔥💨 最高の相性", "火を燃やすのは風。お互いを活かし合う最高の組み合わせです。会話が弾み、一緒にいると自然と元気になれます。"),
    ("風", "火"): ("💨🔥 最高の相性", "火を燃やすのは風。お互いを活かし合う最高の組み合わせです。会話が弾み、一緒にいると自然と元気になれます。"),
    ("地", "水"): ("🌍💧 深く安定した相性", "地を潤すのは水。安心感と深い絆が育つ組み合わせです。長期的に支え合える、安定した関係が築けます。"),
    ("水", "地"): ("💧🌍 深く安定した相性", "地を潤すのは水。安心感と深い絆が育つ組み合わせです。長期的に支え合える、安定した関係が築けます。"),
    ("火", "地"): ("🔥🌍 補い合う相性", "情熱と現実感覚の組み合わせ。最初は違いを感じますが、お互いの強みが補い合えます。"),
    ("地", "火"): ("🌍🔥 補い合う相性", "情熱と現実感覚の組み合わせ。最初は違いを感じますが、お互いの強みが補い合えます。"),
    ("風", "水"): ("💨💧 感性が合う相性", "知性と感性の組み合わせ。会話が豊かで、お互いの世界を広げ合えます。"),
    ("水", "風"): ("💧💨 感性が合う相性", "知性と感性の組み合わせ。会話が豊かで、お互いの世界を広げ合えます。"),
    ("火", "水"): ("🔥💧 ドラマチックな相性", "情熱と感情が激しくぶつかり合います。魅力的ですが、感情的になりやすい面も。理解し合えれば深い絆になります。"),
    ("水", "火"): ("💧🔥 ドラマチックな相性", "情熱と感情が激しくぶつかり合います。魅力的ですが、感情的になりやすい面も。理解し合えれば深い絆になります。"),
    ("風", "地"): ("💨🌍 刺激し合う相性", "自由と安定の組み合わせ。考え方が違いますが、だからこそ学び合えます。"),
    ("地", "風"): ("🌍💨 刺激し合う相性", "自由と安定の組み合わせ。考え方が違いますが、だからこそ学び合えます。"),
    ("地", "地"): ("🌍🌍 安定した組み合わせ", "価値観が似ており、安心感のある関係です。堅実に長期的な絆を育てます。"),
    ("風", "風"): ("💨💨 知的な組み合わせ", "会話が弾み、知的な刺激を与え合います。自由を尊重し合える関係です。"),
    ("水", "水"): ("💧💧 深く共感する組み合わせ", "感情的な共鳴が深く、言葉がなくても通じ合えます。ただし感情的になりすぎる面も。"),
}

ASPECT_COMPAT = {
    "コンジャンクション": ("🔴 コンジャンクション（合）", "強いエネルギーが重なります。似た者同士で共鳴しやすく、強い引き合いがあります。"),
    "トライン": ("🟢 トライン（120°）", "自然な調和と流れがあります。一緒にいると楽で、お互いを高め合えます。"),
    "セクスタイル": ("🔵 セクスタイル（60°）", "穏やかな調和があります。協力しやすく、良い刺激を与え合えます。"),
    "スクエア": ("🟠 スクエア（90°）", "緊張感がありますが、成長のエネルギーです。乗り越えることで深い絆になります。"),
    "オポジション": ("🟣 オポジション（180°）", "引き合う力があります。違いがあるからこそ惹かれ合い、補い合えます。"),
}

SUN_COMPAT = {
    # ===== 牡羊座 =====
    ("牡羊座", "牡羊座"): "同じ情熱を持つ者同士。刺激的ですが競争心も出やすいです。お互いの個性を尊重することで高め合える関係になります。",
    ("牡羊座", "牡牛座"): "スピード感の違いが出やすい組み合わせです。牡羊座の情熱と牡牛座の安定感が補い合えると、バランスの良い関係になります。",
    ("牡羊座", "双子座"): "活発で楽しい組み合わせ。お互いに刺激し合い、新しいことへの挑戦を共に楽しめます。会話が弾む明るい関係です。",
    ("牡羊座", "蟹座"): "行動派と感情派の組み合わせ。価値観の違いを認め合うことで、お互いの弱点を補い合える関係になれます。",
    ("牡羊座", "獅子座"): "火のサイン同士。お互いの情熱と輝きを高め合える素晴らしい組み合わせです。明るく刺激的な関係が続きます。",
    ("牡羊座", "乙女座"): "スピードと丁寧さが対照的な組み合わせ。違いを活かし合うことで、行動力と完成度を兼ね備えた関係になれます。",
    ("牡羊座", "天秤座"): "正反対のサイン同士。引き合う力が強く、お互いに持っていないものを補い合える魅力的な組み合わせです。",
    ("牡羊座", "蠍座"): "どちらも情熱的で強い意志を持つ組み合わせ。ぶつかることもありますが、深い絆が生まれる可能性があります。",
    ("牡羊座", "射手座"): "火のサイン同士。自由と冒険を共に楽しめる理想的な組み合わせです。共に広い世界を目指せます。",
    ("牡羊座", "山羊座"): "行動力と計画性が組み合わさる関係。最初は違いを感じますが、お互いの強みを活かし合えます。",
    ("牡羊座", "水瓶座"): "革新的なエネルギーが共鳴する組み合わせ。新しいことへの挑戦と自由な発想で刺激し合える関係です。",
    ("牡羊座", "魚座"): "行動力と感受性の組み合わせ。牡羊座が引っ張り、魚座が深みを与えることで、バランスの良い関係になれます。",
    # ===== 牡牛座 =====
    ("牡牛座", "牡牛座"): "価値観が似ており、安定した深い絆が育ちます。同じペースで歩める安心感のある関係です。",
    ("牡牛座", "双子座"): "安定と変化が交わる組み合わせ。違いはありますが、お互いに新鮮な刺激を与え合える関係です。",
    ("牡牛座", "蟹座"): "地と水の組み合わせ。安心感と温かさが深く重なり、家庭的で安定した幸せな関係が育ちます。",
    ("牡牛座", "獅子座"): "こだわりと主張が強い者同士。最初は違いを感じますが、お互いの本物志向が理解し合えると深い絆になります。",
    ("牡牛座", "乙女座"): "地のサイン同士。安定と信頼を大切にする深い絆が育ちます。現実的で誠実な関係が長続きします。",
    ("牡牛座", "天秤座"): "どちらも金星が支配星の組み合わせ。美と調和を共に愛し、優雅で心地よい関係が育ちます。",
    ("牡牛座", "蠍座"): "正反対のサイン同士。引き合う力が強く、深い絆と強い情熱が生まれる組み合わせです。",
    ("牡牛座", "射手座"): "安定と自由が対照的な組み合わせ。違いを認め合うことで、お互いの視野を広げ合える関係になれます。",
    ("牡牛座", "山羊座"): "地のサイン同士。現実的で堅実な価値観を共有し、長期的に安定した関係を築けます。",
    ("牡牛座", "水瓶座"): "安定と革新が交わる組み合わせ。違いは大きいですが、お互いから多くを学び合える刺激的な関係です。",
    ("牡牛座", "魚座"): "地と水の組み合わせ。牡牛座の安定感と魚座の優しさが深く共鳴し、温かく穏やかな関係が育ちます。",
    # ===== 双子座 =====
    ("双子座", "双子座"): "知的な刺激と会話が尽きない組み合わせ。自由を尊重し合える楽しい関係ですが、深みを育てる意識も大切です。",
    ("双子座", "蟹座"): "知性と感情が交わる組み合わせ。違いはありますが、お互いの弱点を補い合える深みのある関係になれます。",
    ("双子座", "獅子座"): "知性と輝きが組み合わさる関係。双子座の発想と獅子座の表現力が高め合える、明るく楽しい組み合わせです。",
    ("双子座", "乙女座"): "どちらも水星が支配星の組み合わせ。知性と分析力が共鳴し、会話が深まる知的な関係が育ちます。",
    ("双子座", "天秤座"): "風のサイン同士。知的な会話が弾む理想的な相性です。対等で自由なパートナーシップが育ちます。",
    ("双子座", "蠍座"): "表面と深層が出会う組み合わせ。最初は違いを感じますが、お互いの知らない世界を広げ合える関係になれます。",
    ("双子座", "射手座"): "正反対のサイン同士。知識と哲学が引き合い、お互いに世界を広げ合える刺激的な関係です。",
    ("双子座", "山羊座"): "自由と計画性が交わる組み合わせ。違いを活かし合うことで、発想と現実化を兼ね備えた関係になれます。",
    ("双子座", "水瓶座"): "風のサイン同士。自由と知性を共有できる刺激的な関係です。革新的なアイデアで共鳴できます。",
    ("双子座", "魚座"): "知性と感性が交わる組み合わせ。お互いの世界観が異なりますが、だからこそ豊かな刺激を与え合えます。",
    # ===== 蟹座 =====
    ("蟹座", "蟹座"): "深い共感と温かさで結ばれる組み合わせ。感情的なつながりが深く、家庭的な幸せを共に育てられます。",
    ("蟹座", "獅子座"): "感情と表現が交わる組み合わせ。蟹座の深い愛情と獅子座の温かさが重なり、豊かな関係が育ちます。",
    ("蟹座", "乙女座"): "水と地の組み合わせ。蟹座の感受性と乙女座の丁寧さが共鳴し、思いやりのある安定した関係が育ちます。",
    ("蟹座", "天秤座"): "感情と調和が交わる組み合わせ。蟹座の深い愛情と天秤座の美しい関係性への憧れが共鳴します。",
    ("蟹座", "蠍座"): "水のサイン同士。感情的な深い絆が生まれます。言葉がなくても通じ合える深い関係です。",
    ("蟹座", "射手座"): "安心感と自由が交わる組み合わせ。違いはありますが、お互いに新しい世界を見せ合える関係になれます。",
    ("蟹座", "山羊座"): "正反対のサイン同士。家庭と社会、感情と現実が引き合い、補い合える深い関係です。",
    ("蟹座", "水瓶座"): "感情と知性が交わる組み合わせ。理解し合うのに時間がかかりますが、深く尊重し合える関係になれます。",
    ("蟹座", "魚座"): "水のサイン同士。優しさと共感で深くつながれる相性です。互いの感受性が深く共鳴します。",
    # ===== 獅子座 =====
    ("獅子座", "獅子座"): "どちらも輝きたい者同士。お互いを尊重し合えれば、二人でより大きく輝ける素晴らしい組み合わせです。",
    ("獅子座", "乙女座"): "輝きと丁寧さが交わる組み合わせ。獅子座の華やかさと乙女座の細やかさが補い合える関係です。",
    ("獅子座", "天秤座"): "どちらも美と愛を大切にする組み合わせ。華やかで美しい関係が育ち、お互いを引き立て合えます。",
    ("獅子座", "蠍座"): "強い意志と情熱を持つ者同士。ぶつかることもありますが、深い絆と強い信頼が生まれます。",
    ("獅子座", "射手座"): "火のサイン同士。情熱と自由を共に楽しめる明るく活力あふれる関係です。",
    ("獅子座", "山羊座"): "輝きと実力が組み合わさる関係。獅子座の表現力と山羊座の達成力が高め合える組み合わせです。",
    ("獅子座", "水瓶座"): "正反対のサイン同士。個性と人類愛が引き合い、お互いの視野を広げ合える刺激的な関係です。",
    ("獅子座", "魚座"): "輝きと感性が交わる組み合わせ。獅子座の明るさと魚座の深みが共鳴し、豊かな関係が育ちます。",
    # ===== 乙女座 =====
    ("乙女座", "乙女座"): "誠実さと丁寧さが共鳴する組み合わせ。価値観が似ており、真面目で安定した信頼関係が育ちます。",
    ("乙女座", "天秤座"): "丁寧さと調和が交わる組み合わせ。乙女座の誠実さと天秤座の美意識が高め合える関係です。",
    ("乙女座", "蠍座"): "地と水の組み合わせ。乙女座の丁寧さと蠍座の深さが共鳴し、信頼と深みのある関係が育ちます。",
    ("乙女座", "射手座"): "細部と大局が交わる組み合わせ。違いはありますが、お互いの見方を広げ合える刺激的な関係です。",
    ("乙女座", "山羊座"): "地のサイン同士。現実的で安定した関係を築けます。共に着実に積み上げていける信頼の関係です。",
    ("乙女座", "水瓶座"): "分析と革新が交わる組み合わせ。お互いの知性が共鳴し、高め合える知的な関係が育ちます。",
    ("乙女座", "魚座"): "正反対のサイン同士。現実と夢が引き合い、お互いの弱点を補い合える深い関係です。",
    # ===== 天秤座 =====
    ("天秤座", "天秤座"): "調和と美を共に愛する組み合わせ。美しく穏やかな関係が育ちますが、決断力を意識することも大切です。",
    ("天秤座", "蠍座"): "調和と深さが交わる組み合わせ。天秤座の美しさと蠍座の情熱が引き合い、豊かな絆が育ちます。",
    ("天秤座", "射手座"): "調和と自由が交わる組み合わせ。風と火が共鳴し、楽しく明るい関係が広がります。",
    ("天秤座", "山羊座"): "美と現実が交わる組み合わせ。天秤座の感性と山羊座の実力が高め合える関係です。",
    ("天秤座", "水瓶座"): "風のサイン同士。対等で知的な関係が理想的です。自由と調和を共に大切にできます。",
    ("天秤座", "魚座"): "美と感性が深く共鳴する組み合わせ。お互いの感受性が豊かに響き合う、優しい関係が育ちます。",
    # ===== 蠍座 =====
    ("蠍座", "蠍座"): "深い情熱と強い意志を持つ者同士。激しくぶつかることもありますが、誰にも負けない深い絆が生まれます。",
    ("蠍座", "射手座"): "深さと広さが交わる組み合わせ。蠍座の集中力と射手座の自由が引き合い、成長し合える関係です。",
    ("蠍座", "山羊座"): "水と地の組み合わせ。蠍座の情熱と山羊座の達成力が深く共鳴し、強い絆が育ちます。",
    ("蠍座", "水瓶座"): "深さと広さが交わる組み合わせ。理解し合うのに時間がかかりますが、深く尊重し合える関係になれます。",
    ("蠍座", "魚座"): "水のサイン同士。深い精神的なつながりがあります。言葉を超えた深い共鳴が生まれる関係です。",
    # ===== 射手座 =====
    ("射手座", "射手座"): "自由と冒険を共に愛する者同士。広い世界を共に探求できる明るく楽しい関係が続きます。",
    ("射手座", "山羊座"): "自由と責任が交わる組み合わせ。射手座の視野と山羊座の実行力が高め合える関係です。",
    ("射手座", "水瓶座"): "火と風の組み合わせ。自由と革新が共鳴し、お互いの可能性を広げ合える刺激的な関係です。",
    ("射手座", "魚座"): "自由と感性が交わる組み合わせ。どちらも理想を大切にし、精神的なつながりが深まる関係です。",
    # ===== 山羊座 =====
    ("山羊座", "山羊座"): "現実的で堅実な価値観を共有する組み合わせ。共に着実に積み上げていける信頼と安定の関係です。",
    ("山羊座", "水瓶座"): "伝統と革新が交わる組み合わせ。山羊座の実力と水瓶座の発想が高め合える知的な関係です。",
    ("山羊座", "魚座"): "現実と夢が交わる組み合わせ。山羊座の安定感と魚座の感性が深く共鳴し、補い合える関係です。",
    # ===== 水瓶座 =====
    ("水瓶座", "水瓶座"): "自由と革新を共に愛する者同士。独自の価値観を尊重し合える、対等で知的な関係が育ちます。",
    ("水瓶座", "魚座"): "革新と感性が交わる組み合わせ。水瓶座の知性と魚座の直感が共鳴し、独自の深みのある関係です。",
    # ===== 魚座 =====
    ("魚座", "魚座"): "深い共感と感受性が共鳴する組み合わせ。言葉がなくても通じ合える、魂レベルの深いつながりがあります。",
}

def get_sun_compat_message(sign1, sign2):
    key1 = (sign1, sign2)
    key2 = (sign2, sign1)
    if key1 in SUN_COMPAT:
        return SUN_COMPAT[key1]
    if key2 in SUN_COMPAT:
        return SUN_COMPAT[key2]
    e1 = ELEMENTS.get(sign1, "")
    e2 = ELEMENTS.get(sign2, "")
    compat = ELEMENT_COMPAT.get((e1, e2))
    if compat:
        return compat[1]
    return f"{sign1}と{sign2}の組み合わせです。お互いの違いを尊重することで良い関係が育ちます。"


def calc_aspect(deg1, deg2):
    """2天体間のアスペクトを計算"""
    diff = abs(deg1 - deg2) % 360
    if diff > 180:
        diff = 360 - diff
    aspects = [
        ("コンジャンクション", 0, 8),
        ("セクスタイル", 60, 5),
        ("スクエア", 90, 7),
        ("トライン", 120, 7),
        ("オポジション", 180, 8),
    ]
    for name, angle, orb in aspects:
        if abs(diff - angle) <= orb:
            return name
    return None


def get_house_num(planet_deg, house_cusps):
    for i in range(12):
        cusp_start = house_cusps[i]
        cusp_end = house_cusps[(i + 1) % 12]
        if cusp_end < cusp_start:
            if planet_deg >= cusp_start or planet_deg < cusp_end:
                return i + 1
        else:
            if cusp_start <= planet_deg < cusp_end:
                return i + 1
    return 1


def _render(container):
    """相性占いの共通描画処理"""
    with container:
        st.markdown("### 💑 相性占い")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**👤 お相手1**")
            name1 = st.text_input("お名前", value="Luna", key="compat_name1")
            bday1 = st.date_input(
                "生年月日",
                key="bday1",
                value=datetime.date(1968, 5, 27),
                min_value=datetime.date(1800, 1, 1),
                max_value=datetime.date.today()
            )
            hour1 = st.number_input("出生時（時）", min_value=0, max_value=23, value=0, key="hour1")
            min1  = st.number_input("出生時（分）", min_value=0, max_value=59, value=0, key="min1")

        with col2:
            st.markdown("**👤 お相手2**")
            name2 = st.text_input("お名前", value="", placeholder="お名前", key="compat_name2")
            bday2 = st.date_input(
                "生年月日",
                key="bday2",
                value=datetime.date(1990, 1, 1),
                min_value=datetime.date(1800, 1, 1),
                max_value=datetime.date.today()
            )
            hour2 = st.number_input("出生時（時）", min_value=0, max_value=23, value=12, key="hour2")
            min2  = st.number_input("出生時（分）", min_value=0, max_value=59, value=0, key="min2")

        btn_compat = st.button("💕 相性を見る", use_container_width=True, type="primary", key="btn_compat")

        if btn_compat:
            disp1 = name1 or "Aさん"
            disp2 = name2 or "Bさん"

            # ===== 天文計算 =====
            t1 = make_ts_from_local(bday1, int(hour1), int(min1), 9)
            t2 = make_ts_from_local(bday2, int(hour2), int(min2), 9)

            longs1 = get_body_longitudes_ts(t1)
            longs2 = get_body_longitudes_ts(t2)

            sun_sign1, sun_deg1, _ = get_sun_info(t1)
            moon_sign1, moon_deg1, _ = get_moon_info(t1)
            sun_sign2, sun_deg2, _ = get_sun_info(t2)
            moon_sign2, moon_deg2, _ = get_moon_info(t2)

            venus1 = longs1.get("金星", 0.0)
            mars1  = longs1.get("火星", 0.0)
            venus2 = longs2.get("金星", 0.0)
            mars2  = longs2.get("火星", 0.0)

            venus_sign1, venus_deg1 = split_sign_degree(venus1)
            venus_sign2, venus_deg2 = split_sign_degree(venus2)
            mars_sign1, mars_deg1   = split_sign_degree(mars1)
            mars_sign2, mars_deg2   = split_sign_degree(mars2)

            e1 = ELEMENTS.get(sun_sign1, "")
            e2 = ELEMENTS.get(sun_sign2, "")

            # ===== ①基本情報 =====
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**{disp1}**")
                st.write(f"☀ 太陽：{sun_sign1} {sun_deg1:.1f}°")
                st.write(f"☽ 月：{moon_sign1} {moon_deg1:.1f}°")
                st.write(f"♀ 金星：{venus_sign1} {venus_deg1:.1f}°")
                st.write(f"♂ 火星：{mars_sign1} {mars_deg1:.1f}°")
            with col_b:
                st.markdown(f"**{disp2}**")
                st.write(f"☀ 太陽：{sun_sign2} {sun_deg2:.1f}°")
                st.write(f"☽ 月：{moon_sign2} {moon_deg2:.1f}°")
                st.write(f"♀ 金星：{venus_sign2} {venus_deg2:.1f}°")
                st.write(f"♂ 火星：{mars_sign2} {mars_deg2:.1f}°")

            # ===== ②エレメント相性 =====
            st.markdown("---")
            st.markdown("### 🌟 エレメント相性")
            compat_info = ELEMENT_COMPAT.get((e1, e2))
            if compat_info:
                st.markdown(f"**{compat_info[0]}**")
                st.markdown(f"<div class='luna-message'>{compat_info[1]}</div>", unsafe_allow_html=True)
            else:
                st.write(f"{disp1}（{e1}）×{disp2}（{e2}）の組み合わせです。")

            # ===== ③太陽×太陽の相性 =====
            st.markdown("---")
            st.markdown("### ☀ 太陽の相性（本質の相性）")
            st.write(f"{disp1}：{sun_sign1}　×　{disp2}：{sun_sign2}")
            sun_aspect = calc_aspect(longs1.get("太陽", 0), longs2.get("太陽", 0))
            if sun_aspect:
                asp_info = ASPECT_COMPAT.get(sun_aspect)
                if asp_info:
                    st.markdown(f"**{asp_info[0]}**")
                    st.markdown(f"<div class='luna-message'>{asp_info[1]}</div>", unsafe_allow_html=True)
            sun_msg = get_sun_compat_message(sun_sign1, sun_sign2)
            st.markdown(f"<div class='luna-message'>{sun_msg}</div>", unsafe_allow_html=True)

            # ===== ④月×月の相性 =====
            st.markdown("---")
            st.markdown("### ☽ 月の相性（感情・安心感の相性）")
            st.write(f"{disp1}：{moon_sign1}　×　{disp2}：{moon_sign2}")
            moon_aspect = calc_aspect(longs1.get("月", 0), longs2.get("月", 0))
            me1 = ELEMENTS.get(moon_sign1, "")
            me2 = ELEMENTS.get(moon_sign2, "")
            moon_compat = ELEMENT_COMPAT.get((me1, me2))
            if moon_aspect:
                asp_info = ASPECT_COMPAT.get(moon_aspect)
                if asp_info:
                    st.markdown(f"**{asp_info[0]}**")
                    st.markdown(f"<div class='luna-message'>{asp_info[1]}</div>", unsafe_allow_html=True)
            if moon_compat:
                st.markdown(f"<div class='luna-message'>感情面：{moon_compat[1]}</div>", unsafe_allow_html=True)

            # ===== ⑤金星×火星の相性 =====
            st.markdown("---")
            st.markdown("### ♀♂ 金星×火星の相性（愛情・魅力の相性）")
            vm_aspect1 = calc_aspect(venus1, mars2)
            vm_aspect2 = calc_aspect(venus2, mars1)

            st.write(f"{disp1}の金星（{venus_sign1}）× {disp2}の火星（{mars_sign2}）")
            if vm_aspect1:
                asp_info = ASPECT_COMPAT.get(vm_aspect1)
                if asp_info:
                    st.markdown(f"**{asp_info[0]}**")
                    st.markdown(f"<div class='luna-message'>{asp_info[1]}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='luna-message'>直接的なアスペクトはありませんが、それぞれの愛情表現が個性的に輝きます。</div>", unsafe_allow_html=True)

            st.write(f"{disp2}の金星（{venus_sign2}）× {disp1}の火星（{mars_sign1}）")
            if vm_aspect2:
                asp_info = ASPECT_COMPAT.get(vm_aspect2)
                if asp_info:
                    st.markdown(f"**{asp_info[0]}**")
                    st.markdown(f"<div class='luna-message'>{asp_info[1]}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='luna-message'>直接的なアスペクトはありませんが、それぞれの魅力が独自に輝きます。</div>", unsafe_allow_html=True)

            # ===== ⑥総合相性メッセージ =====
            st.markdown("---")
            st.markdown("### 🌙 総合相性メッセージ")

            good_aspects = ["トライン", "セクスタイル", "コンジャンクション"]
            score = 0
            for asp in [sun_aspect, moon_aspect, vm_aspect1, vm_aspect2]:
                if asp in good_aspects:
                    score += 1

            if score >= 3:
                overall = "とても良い相性です✨ 自然な流れでお互いを高め合える、素晴らしい組み合わせです。"
            elif score == 2:
                overall = "良い相性です😊 共鳴する部分が多く、理解し合いやすい関係です。"
            elif score == 1:
                overall = "個性的な相性です🌟 違いはありますが、だからこそ学び合い、成長できる関係です。"
            else:
                overall = "刺激的な相性です💫 違いが多い分、お互いに深く理解し合うことで本物の絆が育ちます。"

            st.markdown(f"<div class='luna-message'>{overall}</div>", unsafe_allow_html=True)

            # ===== ⑦ホロスコープ重ね表示 =====
            st.markdown("---")
            st.markdown("### 🌙 ホロスコープ（2人の重ね表示）")
            st.caption(f"● {disp1}のネイタル　▲ {disp2}の天体（青）")

            dt_utc1 = datetime.datetime(
                bday1.year, bday1.month, bday1.day,
                int(hour1), int(min1)
            ) - datetime.timedelta(hours=9)
            jd1 = swe.julday(
                dt_utc1.year, dt_utc1.month, dt_utc1.day,
                dt_utc1.hour + dt_utc1.minute / 60.0
            )
            house_cusps1, _ = swe.houses(jd1, 35.68, 139.69, b'P')

            fig = plot_horoscope(longs1, house_cusps1, longs2)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")  # 表示用はdpi=150で十分
            buf.seek(0)
            st.image(buf, use_container_width=True)

            buf2 = io.BytesIO()
            fig.savefig(buf2, format="png", dpi=150, bbox_inches="tight")  # ダウンロード用もdpi=150
            buf2.seek(0)
            st.download_button(
                label="☁ ホロスコープ画像をダウンロード",
                data=buf2,
                file_name="luna_compatibility.png",
                mime="image/png",
            )

            # ===== ⑧相性鑑定書PDF =====
            st.markdown("---")
            st.markdown("### 📄 相性鑑定書PDFをダウンロード")

            chart_buf = io.BytesIO()
            fig.savefig(chart_buf, format="png", dpi=150, bbox_inches="tight")
            chart_buf.seek(0)

            compat_note = (
                f"【エレメント相性】{compat_info[0] if compat_info else '—'}\n"
                f"{compat_info[1] if compat_info else ''}\n\n"
                f"【太陽の相性】{disp1}（{sun_sign1}）× {disp2}（{sun_sign2}）\n"
                f"{sun_msg}\n\n"
                f"【総合】{overall}"
            )

            from utils.pdf_report import create_compatibility_pdf
            pdf_buf = create_compatibility_pdf(
                name1=disp1, birthday1=bday1,
                sun_sign1=sun_sign1, moon_sign1=moon_sign1,
                venus_sign1=venus_sign1, mars_sign1=mars_sign1,
                name2=disp2, birthday2=bday2,
                sun_sign2=sun_sign2, moon_sign2=moon_sign2,
                venus_sign2=venus_sign2, mars_sign2=mars_sign2,
                overall=overall,
                compat_note=compat_note,
                chart_image_bytes=chart_buf,
            )
            st.download_button(
                label="📄 相性鑑定書PDFをダウンロード",
                data=pdf_buf,
                file_name=f"luna_compat_{disp1}_{disp2}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


def show(tab):
    """既存タブ構成からの呼び出し（後方互換）"""
    _render(tab)


def show_direct():
    """メニュー画面から直接呼び出す場合（タブなし）"""
    import contextlib

    @contextlib.contextmanager
    def noop():
        yield st

    _render(noop())
