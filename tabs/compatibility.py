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
    ("火", "火"): ("🔥🔥 情熱的な組み合わせ", "お互いのエネルギーが共鳴。刺激的な関係ですが、競争心が出やすい面も。"),
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
    ("牡羊座", "牡羊座"): "同じ情熱を持つ者同士。刺激的ですが競争心も出やすいです。",
    ("牡羊座", "獅子座"): "火のサイン同士。お互いを輝かせ合える素晴らしい組み合わせです。",
    ("牡羊座", "射手座"): "自由と冒険を共に楽しめる理想的な組み合わせです。",
    ("牡牛座", "乙女座"): "地のサイン同士。安定と信頼を大切にする深い絆が育ちます。",
    ("牡牛座", "山羊座"): "現実的で堅実な価値観を共有できます。",
    ("双子座", "天秤座"): "風のサイン同士。知的な会話が弾む理想的な相性です。",
    ("双子座", "水瓶座"): "自由と知性を共有できる刺激的な関係です。",
    ("蟹座", "蠍座"): "水のサイン同士。感情的な深い絆が生まれます。",
    ("蟹座", "魚座"): "優しさと共感で深くつながれる相性です。",
    ("獅子座", "射手座"): "情熱と自由を共に楽しめる明るい関係です。",
    ("乙女座", "山羊座"): "地のサイン同士。現実的で安定した関係を築けます。",
    ("天秤座", "水瓶座"): "風のサイン同士。対等で知的な関係が理想的です。",
    ("蠍座", "魚座"): "水のサイン同士。深い精神的なつながりがあります。",
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


def show(tab):
    with tab:
        st.markdown("### 💕 相性占い")

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

            # アスペクト数でスコアを出す
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

            # person1のハウスを使ってチャートを表示
            dt_utc1 = datetime.datetime(
                bday1.year, bday1.month, bday1.day,
                int(hour1), int(min1)
            ) - datetime.timedelta(hours=9)
            jd1 = swe.julday(
                dt_utc1.year, dt_utc1.month, dt_utc1.day,
                dt_utc1.hour + dt_utc1.minute / 60.0
            )
            # デフォルト東京
            house_cusps1, _ = swe.houses(jd1, 35.68, 139.69, b'P')

            fig = plot_horoscope(longs1, house_cusps1, longs2)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            st.image(buf, use_container_width=True)

            buf2 = io.BytesIO()
            fig.savefig(buf2, format="png", bbox_inches="tight")
            buf2.seek(0)
            st.download_button(
                label="☁ ホロスコープ画像をダウンロード",
                data=buf2,
                file_name="luna_compatibility.png",
                mime="image/png",
            )
