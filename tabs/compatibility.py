# tabs/compatibility.py
# タブ3：相性占い

import streamlit as st
import datetime
from utils.astro import make_ts_from_local, get_sun_info, get_moon_info, ELEMENTS


def get_element(sign):
    return ELEMENTS.get(sign, None)


def compatibility_message(sun1, sun2, moon1, moon2, name1="Aさん", name2="Bさん"):
    e1 = get_element(sun1)
    e2 = get_element(sun2)

    base = f"{name1}（太陽{sun1}）と{name2}（太陽{sun2}）の関係性は、<br>"

    if e1 == e2 and e1 is not None:
        msg = "同じエレメント同士。基本的な感覚やテンポが似ていて、自然体でいられる相性です。"
    elif {e1, e2} == {"火", "風"}:
        msg = "火と風の組み合わせ。勢いとアイデアが噛み合う、刺激的で前向きな相性です。"
    elif {e1, e2} == {"地", "水"}:
        msg = "地と水の組み合わせ。安心感や現実性、情の深さを育てやすい、落ち着いた相性です。"
    elif {e1, e2} == {"火", "水"}:
        msg = "火と水の組み合わせ。情熱と感情が揺れやすく、ドラマチックになりやすい相性です。"
    elif {e1, e2} == {"風", "地"}:
        msg = "風と地の組み合わせ。考え方と現実感覚がすれ違いやすい分、お互いを補い合える相性です。"
    else:
        msg = "違うタイプ同士。最初は「違い」を感じますが、理解し合えれば学び合う関係になれます。"

    moon_part = f"<br><br>月の組み合わせとしては、{name1}の月は{moon1}、{name2}の月は{moon2}。<br>"
    moon_part += "感情面・安心感のポイントを大切にすると、関係性がより穏やかになります。"

    return base + msg + moon_part


def show(tab):
    with tab:
        st.markdown("<div class='luna-section-title'>お二人の相性</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            name1 = st.text_input("お相手1のお名前", value="Luna", key="compat_name1")
            bday1 = st.date_input(
                "お相手1の生年月日",
                key="bday1",
                value=datetime.date(1968, 5, 27),
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today()
            )
        with col2:
            name2 = st.text_input("お相手2のお名前", value="", placeholder="お相手のお名前", key="compat_name2")
            bday2 = st.date_input(
                "お相手2の生年月日",
                key="bday2",
                value=datetime.date(1990, 1, 1),
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today()
            )

        if st.button("💞 相性を見る", key="compat"):
            def get_signs_for_date(d):
                t = make_ts_from_local(d, 12, 0, 9)
                sun_s, _, _ = get_sun_info(t)
                moon_s, _, _ = get_moon_info(t)
                return sun_s, moon_s

            sun1, moon1 = get_signs_for_date(bday1)
            sun2, moon2 = get_signs_for_date(bday2)

            disp1 = name1 or "Aさん"
            disp2 = name2 or "Bさん"

            st.write(f"{disp1}：太陽 {sun1}／月 {moon1}")
            st.write(f"{disp2}：太陽 {sun2}／月 {moon2}")

            comp = compatibility_message(sun1, sun2, moon1, moon2, disp1, disp2)
            st.markdown(f"<div class='luna-message'>{comp}</div>", unsafe_allow_html=True)
