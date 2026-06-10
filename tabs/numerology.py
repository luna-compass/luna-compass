# tabs/numerology.py
# タブ4：数秘術

import datetime
import streamlit as st


# ===== 数秘術計算 =====

def reduce_number(n):
    """数字を1桁（またはマスターナンバー11・22・33）に還元"""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def calc_life_path(birthday):
    """ライフパスナンバー：生年月日の全数字を足す"""
    digits = (
        str(birthday.year) +
        str(birthday.month).zfill(2) +
        str(birthday.day).zfill(2)
    )
    total = sum(int(d) for d in digits)
    return reduce_number(total)


def calc_birthday_number(birthday):
    """バースデーナンバー：生まれた日の数字"""
    return reduce_number(birthday.day)


def calc_ruler_number(birthday):
    """ルーラーナンバー：生まれた年の数字"""
    total = sum(int(d) for d in str(birthday.year))
    return reduce_number(total)


# ===== メッセージ辞書 =====

LIFE_PATH_MESSAGES = {
    1: {
        "title": "1：リーダー・開拓者",
        "message": "自分の力で道を切り開く、先駆者の魂を持っています。独立心が強く、リーダーシップを発揮することで人生が輝きます。自分を信じて一歩踏み出すことが大切です。",
        "talent": "独立心・リーダーシップ・創造力・パイオニア精神",
        "challenge": "頑固さや孤独感に注意。人の意見も取り入れながら進みましょう。",
        "keywords": "独立・創造・先駆者・自信・行動"
    },
    2: {
        "title": "2：調和・協力者",
        "message": "人と人をつなぐ、調和の橋渡し役です。繊細な感受性と共感力で、周囲を和ませる力があります。パートナーシップや協力関係の中で才能が最大限に発揮されます。",
        "talent": "協調性・共感力・外交力・細やかな気配り",
        "challenge": "優柔不断や依存心に注意。自分の気持ちも大切にしましょう。",
        "keywords": "調和・協力・共感・パートナーシップ・平和"
    },
    3: {
        "title": "3：表現者・クリエイター",
        "message": "喜びと創造性を周囲に広げる、表現の天才です。言葉・芸術・コミュニケーションを通して世界を豊かにします。楽しむことが才能を開花させる鍵です。",
        "talent": "表現力・創造性・コミュニケーション力・ユーモア",
        "challenge": "散漫になりやすい面も。一つのことを深めることで大きな成果が出ます。",
        "keywords": "表現・創造・喜び・コミュニケーション・芸術"
    },
    4: {
        "title": "4：建設者・職人",
        "message": "地道な努力と誠実さで、確かなものを築き上げる魂です。コツコツと積み重ねることで、誰よりも安定した基盤を作ります。信頼と実績があなたの財産です。",
        "talent": "忍耐力・誠実さ・組織力・実務能力",
        "challenge": "頑固さや融通のなさに注意。柔軟性を持つとさらに成長できます。",
        "keywords": "安定・努力・誠実・建設・信頼"
    },
    5: {
        "title": "5：自由人・冒険者",
        "message": "自由と変化を愛する、冒険の魂です。好奇心旺盛で多才、変化の中にチャンスを見つける力があります。新しい経験と出会いがあなたを輝かせます。",
        "talent": "適応力・好奇心・行動力・多才さ",
        "challenge": "落ち着きのなさや飽き性に注意。一つの道を深める経験も大切です。",
        "keywords": "自由・変化・冒険・多才・好奇心"
    },
    6: {
        "title": "6：愛情・奉仕者",
        "message": "愛と調和を大切にする、奉仕の魂です。家族や大切な人への愛情が深く、周囲を美しく整える力があります。愛を与えることがあなたの使命です。",
        "talent": "愛情深さ・責任感・美的センス・奉仕精神",
        "challenge": "自己犠牲になりすぎる面も。自分自身も大切にしましょう。",
        "keywords": "愛・奉仕・家族・美・責任"
    },
    7: {
        "title": "7：探求者・哲学者",
        "message": "真実と知恵を探求する、内省の魂です。深い思考力と直感で、物事の本質を見抜く力があります。一人の時間と内省が才能を磨きます。",
        "talent": "分析力・直感・探求心・精神性",
        "challenge": "孤立感や完璧主義に注意。人とのつながりも大切にしましょう。",
        "keywords": "探求・知恵・内省・直感・精神性"
    },
    8: {
        "title": "8：達成者・実力者",
        "message": "物質的な成功と権力を手にする、達成の魂です。強い意志と実行力で、大きな目標を実現します。お金・地位・影響力を通して世界に貢献できます。",
        "talent": "実行力・リーダーシップ・ビジネス感覚・意志力",
        "challenge": "権力欲や物質主義に注意。精神的なバランスも大切にしましょう。",
        "keywords": "成功・権力・達成・ビジネス・影響力"
    },
    9: {
        "title": "9：完成者・人道主義者",
        "message": "すべてを包み込む、博愛の魂です。広い視野と深い慈悲心で、人類全体への貢献を使命とします。手放すことで新しいものが入ってくる人生です。",
        "talent": "慈悲心・芸術性・知恵・包容力",
        "challenge": "自己犠牲や感情的になりすぎる面も。境界線を大切にしましょう。",
        "keywords": "博愛・完成・芸術・慈悲・手放し"
    },
    11: {
        "title": "11：直感の達人・マスターナンバー",
        "message": "霊的な直感と啓示を持つ、マスターナンバーの魂です。高い精神性と直感で人々を導く力があります。2の要素も持ちながら、より高い次元で活躍します。",
        "talent": "直感・霊感・インスピレーション・カリスマ性",
        "challenge": "神経質になりやすい面も。地に足をつけたバランスが大切です。",
        "keywords": "直感・啓示・精神性・インスピレーション・マスター"
    },
    22: {
        "title": "22：マスタービルダー・マスターナンバー",
        "message": "大きな夢を現実に変える、最強のマスターナンバーです。理想と現実を結びつける力で、世界に影響を与える大きな何かを築きます。",
        "talent": "ビジョン・実行力・組織力・大きなスケール",
        "challenge": "プレッシャーを感じやすい面も。一歩一歩着実に進みましょう。",
        "keywords": "夢・現実化・大きなスケール・マスター・建設"
    },
    33: {
        "title": "33：マスターティーチャー・マスターナンバー",
        "message": "愛と奉仕の最高形、マスターティーチャーの魂です。純粋な愛と慈悲で人々を癒し、教え導く使命があります。",
        "talent": "愛・癒し・教え・慈悲・奉仕",
        "challenge": "自己犠牲になりすぎる面も。自分への愛も忘れずに。",
        "keywords": "愛・癒し・教師・慈悲・マスター"
    },
}

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

COMPATIBILITY_NUMBERS = {
    (1, 1): "同じエネルギーを持つ者同士。共に高め合えますが、競争心が出やすいです。",
    (1, 2): "リーダーとサポーターの理想的な組み合わせ。",
    (1, 5): "自由と独立を尊重し合える相性です。",
    (1, 9): "リーダーと博愛主義者。大きな目標を共有できます。",
    (2, 6): "愛と調和を大切にする、穏やかな相性です。",
    (2, 8): "協力者と達成者。補い合える関係です。",
    (3, 5): "表現と自由を共に楽しめる相性です。",
    (3, 9): "創造性と博愛。芸術的なつながりがあります。",
    (4, 8): "地道な努力と達成。安定した強い絆です。",
    (6, 9): "愛と博愛。深い精神的なつながりがあります。",
    (7, 11): "探求者と直感者。精神的な深いつながりがあります。",
}

def get_number_compat(n1, n2):
    key1 = (min(n1, n2), max(n1, n2))
    if key1 in COMPATIBILITY_NUMBERS:
        return COMPATIBILITY_NUMBERS[key1]
    diff = abs(n1 - n2)
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

        # ===== 計算 =====
        life_path = calc_life_path(birthday)
        birthday_num = calc_birthday_number(birthday)
        ruler_num = calc_ruler_number(birthday)

        # ===== 計算式の表示 =====
        st.markdown("---")
        st.markdown("### 📊 あなたの数字")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ライフパス", life_path)
        with col2:
            st.metric("バースデー", birthday_num)
        with col3:
            st.metric("ルーラー", ruler_num)

        # 計算過程
        with st.expander("計算方法を見る"):
            digits_year = str(birthday.year)
            digits_month = str(birthday.month).zfill(2)
            digits_day = str(birthday.day).zfill(2)
            total = sum(int(d) for d in digits_year + digits_month + digits_day)
            st.write(f"ライフパス：{digits_year} + {digits_month} + {digits_day} = {total} → {life_path}")
            st.write(f"バースデー：{birthday.day} → {birthday_num}")
            ruler_total = sum(int(d) for d in str(birthday.year))
            st.write(f"ルーラー：{birthday.year} = {ruler_total} → {ruler_num}")

        # ===== ①ライフパスナンバー =====
        st.markdown("---")
        st.markdown(f"### 🌟 ライフパスナンバー：{life_path}")
        st.caption("人生全体のテーマ・使命・歩むべき道")

        lp = LIFE_PATH_MESSAGES.get(life_path, {})
        if lp:
            st.markdown(f"**{lp['title']}**")
            st.markdown(f"<div class='luna-message'>{lp['message']}</div>", unsafe_allow_html=True)
            st.markdown(f"**✨ 才能：** {lp['talent']}")
            st.markdown(f"**⚡ 課題：** {lp['challenge']}")
            st.markdown(f"**🔑 キーワード：** {lp['keywords']}")

        # ===== ②バースデーナンバー =====
        st.markdown("---")
        st.markdown(f"### 🎂 バースデーナンバー：{birthday_num}")
        st.caption("生まれ持った才能・自然に発揮できる力")

        bd_msg = BIRTHDAY_MESSAGES.get(birthday_num, "")
        if bd_msg:
            st.markdown(f"<div class='luna-message'>{bd_msg}</div>", unsafe_allow_html=True)

        # ===== ③ルーラーナンバー =====
        st.markdown("---")
        st.markdown(f"### 👑 ルーラーナンバー：{ruler_num}")
        st.caption("生まれた年が示す使命・人生のテーマ")

        ruler_msg = RULER_MESSAGES.get(ruler_num, "")
        if ruler_msg:
            st.markdown(f"<div class='luna-message'>{ruler_msg}</div>", unsafe_allow_html=True)

        # ===== ④3つの数字の総合メッセージ =====
        st.markdown("---")
        st.markdown("### 🌙 総合メッセージ")

        lp_data = LIFE_PATH_MESSAGES.get(life_path, {})
        summary = f"{name or 'あなた'}の数字は ライフパス{life_path}・バースデー{birthday_num}・ルーラー{ruler_num} です。\n\n"

        if lp_data:
            summary += f"人生のテーマは「{lp_data.get('keywords', '')}」。{lp_data.get('message', '')}"

        st.markdown(f"<div class='luna-message'>{summary}</div>", unsafe_allow_html=True)

        # ===== ⑤相性を見る（オプション） =====
        st.markdown("---")
        st.markdown("### 💕 数字の相性を見る")
        st.caption("相手の生年月日を入力するとライフパスナンバーで相性を確認できます")

        other_birthday = st.date_input(
            "相手の生年月日",
            value=datetime.date(1990, 1, 1),
            min_value=datetime.date(1800, 1, 1),
            max_value=datetime.date.today(),
            key="numerology_other_birthday"
        )

        if st.button("🔢 数字の相性を見る", key="btn_num_compat"):
            other_lp = calc_life_path(other_birthday)
            st.write(f"あなたのライフパス：**{life_path}**　相手のライフパス：**{other_lp}**")
            compat_msg = get_number_compat(life_path, other_lp)
            st.markdown(f"<div class='luna-message'>{compat_msg}</div>", unsafe_allow_html=True)
