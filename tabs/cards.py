# tabs/cards.py
# タブ4：タロットカードメッセージ

import streamlit as st
import random
from pathlib import Path
from PIL import Image
from utils.messages_loader import get_message

# ---------- カードデータ ----------
ASSET_DIR = Path("assets/tarot")

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
    return get_message("tarot_base", card_key) or _TAROT_BASE_DEFAULT.get(card_key, "")

def _get_reverse_msg(card_key):
    return get_message("tarot_reverse", card_key) or _TAROT_REVERSE_DEFAULT.get(card_key, "")

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
                    img = Image.open(img_path)
                    if is_reversed:
                        img = img.rotate(180)
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
                        img = Image.open(img_path)
                        if is_reversed:
                            img = img.rotate(180)
                        st.image(img, width=200)
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
                    img = Image.open(img_path)
                    if is_reversed:
                        img = img.rotate(180)
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
                        img = Image.open(img_path)
                        if is_reversed:
                            img = img.rotate(180)
                        st.image(img, width=200)
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
