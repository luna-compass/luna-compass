# tabs/cards.py
# タブ4：タロットカードメッセージ

import streamlit as st
import random
from pathlib import Path
from PIL import Image
from utils.messages_loader import get_message, get_tarot_message as _get_tarot_msg

# ---------- カードデータ ----------
ASSET_DIR = Path("assets/tarot")

@st.cache_data
def load_card_image(img_path, is_reversed):
    """カード画像をキャッシュして読み込む"""
    try:
        img = Image.open(img_path)
        if is_reversed:
            img = img.rotate(180)
        return img
    except Exception:
        return None

cards = [
    ("fool", "00_fool.png"), ("magician", "01_magician.png"),
    ("high_priestess", "02_high_priestess.png"), ("empress", "03_empress.png"),
    ("emperor", "04_emperor.png"), ("hierophant", "05_hierophant.png"),
    ("lovers", "06_lovers.png"), ("chariot", "07_chariot.png"),
    ("strength", "08_strength.png"), ("hermit", "09_hermit.png"),
    ("wheel_of_fortune", "10_wheel_of_fortune.png"), ("justice", "11_justice.png"),
    ("hanged_man", "12_hanged_man.png"), ("death", "13_death.png"),
    ("temperance", "14_temperance.png"), ("devil", "15_devil.png"),
    ("tower", "16_tower.png"), ("star", "17_star.png"),
    ("moon", "18_moon.png"), ("sun", "19_sun.png"),
    ("judgement", "20_judgement.png"), ("world", "21_world.png"),
]

TAROT_NAME_JP = {
    "fool": "愚者", "magician": "魔術師", "high_priestess": "女教皇",
    "empress": "女帝", "emperor": "皇帝", "hierophant": "教皇",
    "lovers": "恋人", "chariot": "戦車", "strength": "力",
    "hermit": "隠者", "wheel_of_fortune": "運命の輪", "justice": "正義",
    "hanged_man": "吊るされた男", "death": "死神", "temperance": "節制",
    "devil": "悪魔", "tower": "塔", "star": "星",
    "moon": "月", "sun": "太陽", "judgement": "審判", "world": "世界",
}

# フォールバック用デフォルトメッセージ
_TAROT_BASE_DEFAULT = {
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
_TAROT_REVERSE_DEFAULT = {
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

def _get_base_msg(card_key):
    """正位置メッセージを取得（JSONのtarotセクション→フォールバック）"""
    card_name_jp = TAROT_NAME_JP.get(card_key, "")
    if card_name_jp:
        tarot_data = _get_tarot_msg(card_name_jp, "正位置")
        if tarot_data and isinstance(tarot_data, dict):
            return tarot_data.get("message", "")
    return _TAROT_BASE_DEFAULT.get(card_key, "")

def _get_reverse_msg(card_key):
    """逆位置メッセージを取得（JSONのtarotセクション→フォールバック）"""
    card_name_jp = TAROT_NAME_JP.get(card_key, "")
    if card_name_jp:
        tarot_data = _get_tarot_msg(card_name_jp, "逆位置")
        if tarot_data and isinstance(tarot_data, dict):
            return tarot_data.get("message", "")
    return _TAROT_REVERSE_DEFAULT.get(card_key, "")

def draw_card():
    card_key, filename = random.choice(cards)
    is_reversed = random.choice([True, False])
    card_name = TAROT_NAME_JP[card_key]
    if is_reversed:
        card_name += "（逆位置）"
        card_msg = _get_reverse_msg(card_key)
    else:
        card_msg = _get_base_msg(card_key)
    card_img = f"assets/tarot/{filename}"
    return card_name, card_msg, card_img, is_reversed

def draw_three_cards():
    selected = random.sample(cards, 3)
    result = []
    for card_key, filename in selected:
        is_reversed = random.choice([True, False])
        card_name = TAROT_NAME_JP[card_key]
        if is_reversed:
            card_name += "（逆位置）"
            card_msg = _get_reverse_msg(card_key)
        else:
            card_msg = _get_base_msg(card_key)
        card_img = f"assets/tarot/{filename}"
        result.append((card_name, card_msg, card_img, is_reversed))
    return result

def show(tab):
    with tab:
        st.markdown("### 🔮 1枚カードメッセージ", unsafe_allow_html=True)
        if st.button("カードを1枚引く", key="card"):
            card_name, card_msg, card_img, is_reversed = draw_card()
            img_path = Path(card_img) if card_img else None
            if img_path and img_path.exists():
                col1, col2, col3 = st.columns([2, 3, 2])
                with col2:
                    img = load_card_image(img_path, is_reversed)
                    if img:
                        st.image(img, width=350)
                    st.markdown(f"### {card_name}")
                    st.write(card_msg)
            else:
                st.caption("（画像がまだ未設定 or 見つかりません）")
            st.markdown(f"<div class='luna-card-box'><div class='luna-subtitle'>✨ 今日のヒント</div><div style='margin-top:6px;color:#2b1b4b;'>{card_msg}</div></div>", unsafe_allow_html=True)

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        theme = st.radio("🔮 テーマを選んでください", ["総合", "恋愛", "仕事"], horizontal=True)
        st.markdown("### 🔮 3枚引き（過去・現在・未来）")
        if st.button("3枚引きする", key="three"):
            cards_3 = draw_three_cards()
            labels = ["過去", "現在", "未来"]
            col1, col2, col3 = st.columns(3)
            for i, col in enumerate([col1, col2, col3]):
                name, msg, img_path, is_reversed = cards_3[i]
                with col:
                    try:
                        img = load_card_image(img_path, is_reversed)
                        if img:
                            st.image(img, width=200)
                        else:
                            st.caption("（画像なし）")
                    except Exception:
                        st.caption("（画像なし）")
                    st.markdown(f"### {labels[i]}")
                    st.markdown(f"**{name}**")
                    st.write(msg)
            future_name, future_msg, _, _ = cards_3[2]
            if theme == "恋愛":
                summary = f"恋愛面では「{future_name}」の流れです。{future_msg}"
            elif theme == "仕事":
                summary = f"仕事面では「{future_name}」の流れです。{future_msg}"
            else:
                summary = f"全体の流れとしては「{future_name}」に向かっています。{future_msg}"
            summary += " 無理せず整えていきましょう。"
            st.markdown(f"<div class='luna-card-box'><div class='luna-title'>🔮 総合メッセージ</div><div class='luna-text'>{summary}</div></div>", unsafe_allow_html=True)

def show_single(tab):
    with tab:
        st.markdown("### 🔮 1枚カードメッセージ")
        if st.button("カードを1枚引く", key="card_single"):
            card_name, card_msg, card_img, is_reversed = draw_card()
            img_path = Path(card_img) if card_img else None
            if img_path and img_path.exists():
                col1, col2, col3 = st.columns([2, 3, 2])
                with col2:
                    img = load_card_image(img_path, is_reversed)
                    if img:
                        st.image(img, width=350)
            else:
                st.caption("（画像がまだ未設定 or 見つかりません）")
            st.markdown(f"### {card_name}")
            st.markdown(f"<div class='luna-message'>{card_msg}</div>", unsafe_allow_html=True)

def show_three(tab):
    with tab:
        st.markdown("### 🔮 3枚引き（過去・現在・未来）")
        theme = st.radio("🔮 テーマを選んでください", ["総合", "恋愛", "仕事"], horizontal=True, key="tarot_theme")
        if st.button("3枚引きする", key="three_cards"):
            cards_3 = draw_three_cards()
            labels = ["過去", "現在", "未来"]
            col1, col2, col3 = st.columns(3)
            for i, col in enumerate([col1, col2, col3]):
                name, msg, img_path, is_reversed = cards_3[i]
                with col:
                    try:
                        img = load_card_image(img_path, is_reversed)
                        if img:
                            st.image(img, width=200)
                        else:
                            st.caption("（画像なし）")
                    except Exception:
                        st.caption("（画像なし）")
                    st.markdown(f"**{labels[i]}**")
                    st.markdown(f"**{name}**")
                    st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)
            future_name, future_msg, _, _ = cards_3[2]
            if theme == "恋愛":
                summary = f"恋愛面では「{future_name}」の流れです。{future_msg}"
            elif theme == "仕事":
                summary = f"仕事面では「{future_name}」の流れです。{future_msg}"
            else:
                summary = f"全体の流れとしては「{future_name}」に向かっています。{future_msg}"
            summary += " 無理せず整えていきましょう。"
            st.markdown(f"<div class='luna-message'>🔮 総合メッセージ：{summary}</div>", unsafe_allow_html=True)


# ============================================================
# ケルト十字（10枚展開）
# ============================================================

CELTIC_POSITIONS = [
    ("1", "現在の状況",   "今のあなたの状況を示します。"),
    ("2", "障害・課題",   "あなたの前に立ちはだかるものを示します。"),
    ("3", "遠い過去・根底", "問題の根底にあるものを示します。"),
    ("4", "近い過去",     "最近の出来事や影響を示します。"),
    ("5", "可能性・目標", "目指している方向性を示します。"),
    ("6", "近い未来",     "近いうちに起こりうることを示します。"),
    ("7", "あなた自身",   "今のあなたの内面・姿勢を示します。"),
    ("8", "周囲の環境",   "周りの人や状況の影響を示します。"),
    ("9", "希望と恐れ",   "あなたの深い望みと恐れを示します。"),
    ("10", "最終結果",    "この流れが向かう先を示します。"),
]

def draw_celtic_cross():
    """ケルト十字用に10枚引く"""
    selected = random.sample(cards, 10)
    result = []
    for card_key, filename in selected:
        is_reversed = random.choice([True, False])
        card_name = TAROT_NAME_JP[card_key]
        position_label = "逆位置" if is_reversed else "正位置"
        if is_reversed:
            card_msg = _get_reverse_msg(card_key)
        else:
            card_msg = _get_base_msg(card_key)
        card_img = f"assets/tarot/{filename}"
        result.append({
            "key": card_key,
            "name": card_name,
            "position": position_label,
            "msg": card_msg,
            "img": card_img,
            "is_reversed": is_reversed,
        })
    return result


def show_celtic(tab):
    with tab:
        st.markdown("### 🔮 ケルト十字（10枚展開）")
        st.caption("10枚のカードを1枚ずつ引いて、現在・過去・未来・環境・結果を読み解きます。")

        theme = st.radio(
            "テーマを選んでください",
            ["総合", "恋愛", "仕事", "お金"],
            horizontal=True,
            key="celtic_theme"
        )

        # ===== ケルト十字の配置図 =====
        st.markdown("""
        <div style='background:#f5f3ff;border-radius:12px;padding:12px;margin:8px 0;font-size:12px;color:#4c1d95;line-height:2;'>
        <b>📍 ケルト十字の配置</b><br>
        　　　　　⑤可能性<br>
        　④過去　①現在　⑥近い未来　｜　⑦自分<br>
        　　　　　②障害　　　　　　　｜　⑧環境<br>
        　　　　　③根底　　　　　　　｜　⑨希望と恐れ<br>
        　　　　　　　　　　　　　　　｜　⑩最終結果
        </div>
        """, unsafe_allow_html=True)

        # ===== session_state初期化 =====
        if "celtic_drawn" not in st.session_state:
            st.session_state["celtic_drawn"] = None
            st.session_state["celtic_step"] = 0

        # ===== リセット・スタートボタン =====
        col_start, col_reset = st.columns(2)
        with col_start:
            if st.button("🔮 カードを準備する", use_container_width=True, type="primary", key="btn_celtic_start"):
                st.session_state["celtic_drawn"] = draw_celtic_cross()
                st.session_state["celtic_step"] = 0
                st.rerun()
        with col_reset:
            if st.button("🔄 リセット", use_container_width=True, key="btn_celtic_reset"):
                st.session_state["celtic_drawn"] = None
                st.session_state["celtic_step"] = 0
                st.rerun()

        drawn = st.session_state.get("celtic_drawn")
        step  = st.session_state.get("celtic_step", 0)

        if drawn is None:
            st.info("「カードを準備する」を押してください。")
            return

        st.markdown("---")

        # ===== 引いたカードを順番に表示 =====
        for i in range(min(step, 10)):
            card = drawn[i]
            pos_num, pos_name, pos_desc = CELTIC_POSITIONS[i]

            # スタッフ（7〜10）は別セクション
            if i == 6:
                st.markdown("#### 📍 スタッフ（7〜10番）")

            col_img, col_txt = st.columns([1, 2])
            with col_img:
                img = load_card_image(card["img"], card["is_reversed"])
                if img:
                    st.image(img, width=120)
                else:
                    st.caption("（画像なし）")
            with col_txt:
                st.markdown(f"**{pos_num}. {pos_name}**")
                st.caption(pos_desc)
                st.markdown(f"🃏 **{card['name']}（{card['position']}）**")
                st.markdown(f"<div class='luna-message'>{card['msg']}</div>", unsafe_allow_html=True)
            st.markdown("---")

        # ===== 次のカードを引くボタン =====
        if step < 10:
            next_pos = CELTIC_POSITIONS[step]
            if st.button(
                f"🃏 {next_pos[0]}枚目を引く：{next_pos[1]}",
                use_container_width=True,
                type="primary",
                key=f"btn_celtic_{step}"
            ):
                st.session_state["celtic_step"] += 1
                st.rerun()

        # ===== 全部引いたら総合メッセージ =====
        if step >= 10:
            st.markdown("### 🌙 総合メッセージ")
            final_card  = drawn[9]
            near_future = drawn[5]["name"]
            outcome     = drawn[9]["name"]

            if theme == "恋愛":
                summary = f"恋愛面では「{near_future}」の流れを経て、最終的に「{outcome}」へと向かっています。"
            elif theme == "仕事":
                summary = f"仕事面では「{near_future}」の動きがあり、「{outcome}」という結果に向かっています。"
            elif theme == "お金":
                summary = f"金運は「{near_future}」の流れを経て、「{outcome}」へと展開していきます。"
            else:
                summary = f"近い未来に「{near_future}」の流れがあり、最終的には「{outcome}」へと向かっています。"

            summary += f" {final_card['msg']}"
            st.markdown(f"<div class='luna-message'>{summary}</div>", unsafe_allow_html=True)


# ============================================================
# ホロスコープスプレッド（12枚展開）
# ============================================================

HOROSCOPE_POSITIONS = [
    ("1", "第1ハウス", "自分自身・外見・第一印象", "あなた自身の今の状態を示します。"),
    ("2", "第2ハウス", "お金・価値観・所有", "財運や大切にしているものを示します。"),
    ("3", "第3ハウス", "コミュニケーション・学び", "言葉や情報のやりとりを示します。"),
    ("4", "第4ハウス", "家庭・ルーツ・安心", "家族や心の拠り所を示します。"),
    ("5", "第5ハウス", "恋愛・創造・楽しみ", "恋愛運や創造性を示します。"),
    ("6", "第6ハウス", "仕事・健康・日常", "日々の仕事や体調を示します。"),
    ("7", "第7ハウス", "パートナーシップ・対人", "重要な他者との関係を示します。"),
    ("8", "第8ハウス", "変容・深い絆・再生", "深い変化や共有を示します。"),
    ("9", "第9ハウス", "学び・哲学・精神", "精神的な成長や広い視野を示します。"),
    ("10", "第10ハウス", "社会・キャリア・使命", "社会での役割や目標を示します。"),
    ("11", "第11ハウス", "友人・希望・未来", "仲間や未来への展望を示します。"),
    ("12", "第12ハウス", "潜在意識・隠れたもの", "見えない部分や深層心理を示します。"),
]

def draw_horoscope_spread():
    """ホロスコープスプレッド用に12枚引く"""
    selected = random.sample(cards, 12)
    result = []
    for card_key, filename in selected:
        is_reversed = random.choice([True, False])
        card_name = TAROT_NAME_JP[card_key]
        position_label = "逆位置" if is_reversed else "正位置"
        if is_reversed:
            card_msg = _get_reverse_msg(card_key)
        else:
            card_msg = _get_base_msg(card_key)
        card_img = f"assets/tarot/{filename}"
        result.append({
            "key": card_key,
            "name": card_name,
            "position": position_label,
            "msg": card_msg,
            "img": card_img,
            "is_reversed": is_reversed,
        })
    return result


def show_horoscope_spread(tab):
    with tab:
        st.markdown("### 🌙 ホロスコープスプレッド（12枚展開）")
        st.caption("12枚のカードを1枚ずつ引いて、12ハウスの各テーマを読み解きます。")

        # ===== 配置図 =====
        st.markdown("""
        <div style='background:#f5f3ff;border-radius:12px;padding:12px;margin:8px 0;font-size:12px;color:#4c1d95;line-height:2;'>
        <b>🏠 12ハウスの対応</b><br>
        ①自分 ②お金 ③コミュニケーション ④家庭 ⑤恋愛・創造 ⑥仕事・健康<br>
        ⑦パートナー ⑧変容 ⑨学び・精神 ⑩キャリア ⑪友人・未来 ⑫潜在意識
        </div>
        """, unsafe_allow_html=True)

        # ===== session_state初期化 =====
        if "horoscope_drawn" not in st.session_state:
            st.session_state["horoscope_drawn"] = None
            st.session_state["horoscope_step"] = 0

        # ===== リセット・スタートボタン =====
        col_start, col_reset = st.columns(2)
        with col_start:
            if st.button("🌙 カードを準備する", use_container_width=True, type="primary", key="btn_horoscope_start"):
                st.session_state["horoscope_drawn"] = draw_horoscope_spread()
                st.session_state["horoscope_step"] = 0
                st.rerun()
        with col_reset:
            if st.button("🔄 リセット", use_container_width=True, key="btn_horoscope_reset"):
                st.session_state["horoscope_drawn"] = None
                st.session_state["horoscope_step"] = 0
                st.rerun()

        drawn = st.session_state.get("horoscope_drawn")
        step  = st.session_state.get("horoscope_step", 0)

        if drawn is None:
            st.info("「カードを準備する」を押してください。")
            return

        st.markdown("---")

        # ===== 引いたカードを順番に表示 =====
        for i in range(min(step, 12)):
            card = drawn[i]
            pos_num, pos_house, pos_theme, pos_desc = HOROSCOPE_POSITIONS[i]

            col_img, col_txt = st.columns([1, 2])
            with col_img:
                img = load_card_image(card["img"], card["is_reversed"])
                if img:
                    st.image(img, width=120)
                else:
                    st.caption("（画像なし）")
            with col_txt:
                st.markdown(f"**{pos_house}（{pos_theme}）**")
                st.caption(pos_desc)
                st.markdown(f"🃏 **{card['name']}（{card['position']}）**")
                st.markdown(f"<div class='luna-message'>{card['msg']}</div>", unsafe_allow_html=True)
            st.markdown("---")

        # ===== 次のカードを引くボタン =====
        if step < 12:
            next_pos = HOROSCOPE_POSITIONS[step]
            if st.button(
                f"🃏 {next_pos[0]}枚目を引く：{next_pos[1]}（{next_pos[2]}）",
                use_container_width=True,
                type="primary",
                key=f"btn_horoscope_{step}"
            ):
                st.session_state["horoscope_step"] += 1
                st.rerun()

        # ===== 全部引いたら総合メッセージ =====
        if step >= 12:
            st.markdown("### ✨ 注目のハウス")
            positive_cards = [(i, drawn[i]) for i in range(12) if not drawn[i]["is_reversed"]]
            if positive_cards:
                highlight_idx, highlight_card = positive_cards[0]
                pos_num, pos_house, pos_theme, pos_desc = HOROSCOPE_POSITIONS[highlight_idx]
                st.markdown(f"**{pos_house}（{pos_theme}）**が今特に輝いています。")
                st.markdown(f"🃏 **{highlight_card['name']}** が示すのは：")
                st.markdown(f"<div class='luna-message'>{highlight_card['msg']}</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🌙 総合メッセージ")
            card_1  = drawn[0]
            card_7  = drawn[6]
            card_10 = drawn[9]
            summary = (
                f"今のあなた（第1ハウス）は「{card_1['name']}」。{card_1['msg']} "
                f"対人・パートナーシップ（第7ハウス）では「{card_7['name']}」の流れがあります。"
                f"社会・キャリア（第10ハウス）は「{card_10['name']}」が示す方向へ向かっています。"
            )
            st.markdown(f"<div class='luna-message'>{summary}</div>", unsafe_allow_html=True)
