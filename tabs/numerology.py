# tabs/numerology.py
# タブ4：数秘術

import datetime
import streamlit as st
from utils.messages_loader import get_message


def reduce_number(n):
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n

def calc_life_path(birthday):
    digits = str(birthday.year) + str(birthday.month).zfill(2) + str(birthday.day).zfill(2)
    return reduce_number(sum(int(d) for d in digits))

def calc_birthday_number(birthday):
    return reduce_number(birthday.day)

def calc_ruler_number(birthday):
    return reduce_number(sum(int(d) for d in str(birthday.year)))


# フォールバック用（JSONになければこちらを使う）
from utils.messages import LIFE_PATH_MESSAGES as _LP_MESSAGES

BIRTHDAY_MESSAGES = {
    1: "生まれた日の才能：新しいことを始める力・リーダーシップ・独立心が強い",
    2: "生まれた日の才能：協調性・共感力・パートナーシップを大切にする",
    3: "生まれた日の才能：表現力・コミュニケーション力・楽しむ才能",
    4: "生まれた日の才能：誠実さ・忍耐力・コツコツ積み上げる力",
    5: "生まれた日の才能：適応力・好奇心・変化を楽しむ力",
    6: "生まれた日の才能：愛情深さ・責任感・人を大切にする力",
    7: "生まれた日の才能：分析力・直感・深く考える力",
    8: "生まれた日の才能：実行力・ビジネス感覚・目標達成力",
    9: "生まれた日の才能：包容力・慈悲心・大きな視野",
    11: "生まれた日の才能：高い直感・インスピレーション・精神性（マスターナンバー）",
    22: "生まれた日の才能：大きな夢を現実にする力（マスターナンバー）",
    33: "生まれた日の才能：愛と癒しの才能（マスターナンバー）",
}

RULER_MESSAGES = {
    1: "生まれた年の使命：自分らしい道を切り開くこと",
    2: "生まれた年の使命：人との調和とパートナーシップ",
    3: "生まれた年の使命：表現と創造で喜びを広げること",
    4: "生まれた年の使命：地道な努力で確かな基盤を築くこと",
    5: "生まれた年の使命：自由と変化の中で経験を積むこと",
    6: "生まれた年の使命：愛と奉仕で周囲を幸せにすること",
    7: "生まれた年の使命：真実と知恵を探求すること",
    8: "生まれた年の使命：大きな成功と社会貢献",
    9: "生まれた年の使命：博愛と完成に向けて歩むこと",
    11: "生まれた年の使命：直感と霊感で人々を導くこと（マスターナンバー）",
    22: "生まれた年の使命：大きなビジョンを現実に変えること（マスターナンバー）",
    33: "生まれた年の使命：愛と癒しで人々を導くこと（マスターナンバー）",
}

NUM_TITLES = {
    1: "リーダー・開拓者",
    2: "調和・協力者",
    3: "表現者・クリエイター",
    4: "誠実・建設者",
    5: "自由・冒険者",
    6: "愛・奉仕者",
    7: "探求・思想家",
    8: "達成・実業家",
    9: "博愛・完成者",
    11: "直感・インスピレーター（マスターナンバー）",
    22: "夢実現・マスタービルダー（マスターナンバー）",
    33: "愛と癒しの師（マスターナンバー）",
}

def _get_lp_data(num):
    """ライフパスデータをJSONから取得（なければデフォルト）"""
    json_data = get_message("numerology_life_path", str(num))
    if json_data and isinstance(json_data, dict):
        return json_data
    return _LP_MESSAGES.get(num, {})

def _get_birthday_msg(num):
    return get_message("numerology_birthday", str(num)) or BIRTHDAY_MESSAGES.get(num, "")

def _get_ruler_msg(num):
    return get_message("numerology_ruler", str(num)) or RULER_MESSAGES.get(num, "")


COMPATIBILITY_NUMBERS = {
    (1,1):"同じエネルギーを持つ者同士。共に高め合えますが、競争心が出やすいです。",
    (1,2):"リーダーとサポーターの理想的な組み合わせ。",
    (1,5):"自由と独立を尊重し合える相性です。",
    (1,9):"リーダーと博愛主義者。大きな目標を共有できます。",
    (2,6):"愛と調和を大切にする、穏やかな相性です。",
    (2,8):"協力者と達成者。補い合える関係です。",
    (3,5):"表現と自由を共に楽しめる相性です。",
    (3,9):"創造性と博愛。芸術的なつながりがあります。",
    (4,8):"地道な努力と達成。安定した強い絆です。",
    (6,9):"愛と博愛。深い精神的なつながりがあります。",
    (7,11):"探求者と直感者。精神的な深いつながりがあります。",
}

def get_number_compat(n1, n2):
    key1 = (min(n1,n2), max(n1,n2))
    if key1 in COMPATIBILITY_NUMBERS:
        return COMPATIBILITY_NUMBERS[key1]
    diff = abs(n1-n2)
    if diff == 0:
        return "同じナンバー同士。価値観が似ており、理解し合いやすい相性です。"
    elif diff <= 2:
        return "近いナンバー同士。共通点が多く、自然に調和できる相性です。"
    else:
        return "異なるナンバー同士。違いを尊重することで、お互いを成長させる相性です。"


def show(tab, user_info):
    with tab:
        st.markdown("### 🔢 数秘術")
        st.caption("ピタゴラス式数秘術で生年月日からあなたの数字を読み解きます")

        birthday = user_info["birthday"]
        name = user_info["name"]

        life_path = calc_life_path(birthday)
        birthday_num = calc_birthday_number(birthday)
        ruler_num = calc_ruler_number(birthday)

        st.markdown("---")
        st.markdown("### 📊 あなたの数字")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("ライフパス", life_path)
        with col2: st.metric("バースデー", birthday_num)
        with col3: st.metric("ルーラー", ruler_num)

        with st.expander("計算方法を見る"):
            digits_year = str(birthday.year)
            digits_month = str(birthday.month).zfill(2)
            digits_day = str(birthday.day).zfill(2)
            total = sum(int(d) for d in digits_year+digits_month+digits_day)
            st.write(f"ライフパス：{digits_year} + {digits_month} + {digits_day} = {total} → {life_path}")
            st.write(f"バースデー：{birthday.day} → {birthday_num}")
            ruler_total = sum(int(d) for d in str(birthday.year))
            st.write(f"ルーラー：{birthday.year} = {ruler_total} → {ruler_num}")

        st.markdown("---")
        st.markdown(f"""
<div style='background: linear-gradient(135deg, #7c3aed, #a855f7); 
     border-radius: 14px; padding: 14px 20px; margin: 10px 0;'>
<span style='color: white; font-size: 20px; font-weight: 700;'>
🌟 ライフパスナンバー：{life_path}
</span><br>
<span style='color: #e9d5ff; font-size: 12px;'>人生全体のテーマ・使命・歩むべき道</span>
</div>
""", unsafe_allow_html=True)
        lp = _get_lp_data(life_path)
        if lp:
            st.markdown(f"**{lp.get('title','')}**")
            st.markdown(f"<div class='luna-message'>{lp.get('message','')}</div>", unsafe_allow_html=True)
            st.markdown(f"**✨ 才能：** {lp.get('talent','')}")
            st.markdown(f"**⚡ 課題：** {lp.get('challenge','')}")
            st.markdown(f"**🔑 キーワード：** {lp.get('keywords','')}")

        st.markdown("---")
        bd_title = NUM_TITLES.get(birthday_num, "")
        st.markdown(f"""
<div style='background: linear-gradient(135deg, #7c3aed, #a855f7); 
     border-radius: 14px; padding: 14px 20px; margin: 10px 0;'>
<span style='color: white; font-size: 20px; font-weight: 700;'>
🎂 バースデーナンバー：{birthday_num}
</span><br>
<span style='color: #e9d5ff; font-size: 12px;'>生まれ持った才能・自然に発揮できる力</span>
</div>
""", unsafe_allow_html=True)
        if bd_title:
            st.markdown(f"**{birthday_num}：{bd_title}**")
        bd_msg = _get_birthday_msg(birthday_num)
        if bd_msg:
            st.markdown(f"<div class='luna-message'>{bd_msg}</div>", unsafe_allow_html=True)

        st.markdown("---")
        rl_title = NUM_TITLES.get(ruler_num, "")
        st.markdown(f"""
<div style='background: linear-gradient(135deg, #7c3aed, #a855f7); 
     border-radius: 14px; padding: 14px 20px; margin: 10px 0;'>
<span style='color: white; font-size: 20px; font-weight: 700;'>
👑 ルーラーナンバー：{ruler_num}
</span><br>
<span style='color: #e9d5ff; font-size: 12px;'>生まれた年が示す使命・人生のテーマ</span>
</div>
""", unsafe_allow_html=True)
        if rl_title:
            st.markdown(f"**{ruler_num}：{rl_title}**")
        ruler_msg = _get_ruler_msg(ruler_num)
        if ruler_msg:
            st.markdown(f"<div class='luna-message'>{ruler_msg}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🌙 総合メッセージ")
        lp_data = _get_lp_data(life_path)
        name_display = (name + "さん") if name else "あなた"
        summary = f"{name_display}の数字は ライフパス{life_path}・バースデー{birthday_num}・ルーラー{ruler_num} です。\n\n"
        if lp_data:
            summary += f"人生のテーマは「{lp_data.get('keywords','')}」。{lp_data.get('message','')}"
        st.markdown(f"<div class='luna-message'>{summary}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 💕 数字の相性を見る")
        other_birthday = st.date_input(
            "相手の生年月日",
            value=datetime.date(1990,1,1),
            min_value=datetime.date(1800,1,1),
            max_value=datetime.date.today(),
            key="numerology_other_birthday"
        )
        if st.button("🔢 数字の相性を見る", key="btn_num_compat"):
            other_lp = calc_life_path(other_birthday)
            other_bd = calc_birthday_number(other_birthday)
            other_rl = calc_ruler_number(other_birthday)

            st.markdown("#### 📊 2人の数字")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**あなた**")
                st.metric("ライフパス", life_path)
                st.metric("バースデー", birthday_num)
                st.metric("ルーラー", ruler_num)
            with col_b:
                st.markdown("**相手**")
                st.metric("ライフパス", other_lp)
                st.metric("バースデー", other_bd)
                st.metric("ルーラー", other_rl)

            st.markdown("---")
            st.markdown("#### 🌟 ライフパスの相性（人生テーマの相性）")
            lp_msg = get_number_compat(life_path, other_lp)
            st.write(f"あなた：**{life_path}**　×　相手：**{other_lp}**")
            st.markdown(f"<div class='luna-message'>{lp_msg}</div>", unsafe_allow_html=True)

            st.markdown("#### 🎂 バースデーの相性（才能・個性の相性）")
            bd_msg = get_number_compat(birthday_num, other_bd)
            st.write(f"あなた：**{birthday_num}**　×　相手：**{other_bd}**")
            st.markdown(f"<div class='luna-message'>{bd_msg}</div>", unsafe_allow_html=True)

            st.markdown("#### 👑 ルーラーの相性（使命・エネルギーの相性）")
            rl_msg = get_number_compat(ruler_num, other_rl)
            st.write(f"あなた：**{ruler_num}**　×　相手：**{other_rl}**")
            st.markdown(f"<div class='luna-message'>{rl_msg}</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 💫 総合数秘術相性メッセージ")
            good_count = sum([
                1 for n1, n2 in [(life_path, other_lp), (birthday_num, other_bd), (ruler_num, other_rl)]
                if n1 == n2 or abs(n1-n2) <= 2 or (min(n1,n2), max(n1,n2)) in COMPATIBILITY_NUMBERS
            ])
            if good_count == 3:
                overall = "3つの数字すべてが調和しています✨ 魂レベルで深くつながれる、非常に稀な組み合わせです。"
            elif good_count == 2:
                overall = "2つの数字が調和しています😊 共鳴する部分が多く、自然に理解し合える相性です。"
            elif good_count == 1:
                overall = "1つの数字が調和しています🌟 違いを活かし合うことで、お互いを高め合える関係です。"
            else:
                overall = "数字の個性が異なります💫 違いが多い分、刺激し合い、共に成長できる関係です。"
            st.markdown(f"<div class='luna-message'>{overall}</div>", unsafe_allow_html=True)
