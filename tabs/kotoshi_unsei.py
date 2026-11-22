# -*- coding: utf-8 -*-
"""
tabs/kotoshi_unsei.py - 今年の運勢(四柱推命ベース)

四柱推命と同様に、出生時刻・出生地・夜子時・地方時差補正を使用して
年運・大運・月運を計算する。
"""
import datetime

import pandas as pd
import streamlit as st

from utils.shichusuimei import (
    build_meishiki, calc_daiun, calc_getsuun, calc_nenun, find_setsu,
)
from utils.messages_loader import get_message
from utils.pdf_report import create_kotoshi_pdf


@st.cache_data
def _load_cities_kotoshi():
    return pd.read_csv("cities.csv")


def _without_hour_relations(relations):
    """出生時刻が不明なとき、仮の時柱に由来する関係を表示しない。"""
    return [
        relation for relation in relations
        if not any(marker in relation for marker in ("時干", "時支", "時柱"))
    ]


def show_direct():
    st.markdown("### 📅 今年の運勢")
    st.caption("四柱推命であなたの今年と、月ごとの流れを読み解きます。年の切り替わりは立春基準です。")

    with st.expander("👤 基本情報を入力する", expanded=True):
        mode = st.radio(
            "占う対象",
            ("自分を占う", "別の人を占う"),
            key="mode_kotoshi",
            horizontal=True,
        )
        if mode == "自分を占う":
            default_name = "Luna"
            default_date = datetime.date(1968, 5, 27)
            default_hour = 0
            default_minute = 0
            default_city = "北九州"
        else:
            default_name = ""
            default_date = datetime.date(1990, 1, 1)
            default_hour = 12
            default_minute = 0
            default_city = "東京"

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                "お名前", value=default_name,
                key="name_kotoshi", help="ニックネームでもOKです",
            )
        with col2:
            birthday = st.date_input(
                "生年月日",
                value=default_date,
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today(),
                key="birthday_kotoshi",
            )

        time_unknown = st.checkbox(
            "出生時刻が不明（時柱に関する関係は表示しない）",
            value=False,
            key="time_unknown_kotoshi",
        )
        gender = st.radio(
            "性別（大運の判定に使用します）",
            ("女", "男"),
            key="gender_kotoshi",
            horizontal=True,
        )
        yako = st.checkbox(
            "夜子時：23時台生まれを翌日の日柱として扱う",
            value=True,
            key="yako_kotoshi",
            help="オンでは23時台の出生を翌日の日柱として判定します。"
                 "23時台以外は日柱に影響しません。",
        )
        local_time_adjust = st.checkbox(
            "地方時差補正：出生地の経度で出生時刻を補正する",
            value=True,
            key="local_adjust_kotoshi",
            disabled=time_unknown,
            help="日本標準時の基準経度（東経135度）との差を1度あたり4分で補正します。"
                 "日本以外で生まれた場合は、この補正をオフにしてください。",
        )

        adjust_min = 0
        if local_time_adjust and not time_unknown:
            cities = _load_cities_kotoshi()
            city_names = cities["city"].tolist()
            default_index = (
                city_names.index(default_city)
                if default_city in city_names else 0
            )
            birth_city = st.selectbox(
                "出生地", city_names,
                index=default_index,
                key="city_kotoshi",
            )
            longitude = float(
                cities.loc[cities["city"] == birth_city, "lon"].iloc[0]
            )
            adjust_min = round((longitude - 135.0) * 4)
            st.caption(
                f"{birth_city}の地方時差: {adjust_min:+d}分"
                "（標準時に加算して補正します）"
            )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            birth_hour = st.number_input(
                "出生時（時）", min_value=0, max_value=23,
                value=default_hour,
                key="hour_kotoshi", disabled=time_unknown,
            )
        with col_t2:
            birth_minute = st.number_input(
                "出生時（分）", min_value=0, max_value=59,
                value=default_minute,
                key="minute_kotoshi", disabled=time_unknown,
            )

    if st.button("今年の運勢を見る", key="calc_kotoshi", type="primary"):
        hour = 12 if time_unknown else int(birth_hour)
        minute = 0 if time_unknown else int(birth_minute)
        birth = datetime.datetime(
            birthday.year, birthday.month, birthday.day, hour, minute,
        )
        adjusted = local_time_adjust and not time_unknown and adjust_min != 0
        if adjusted:
            birth += datetime.timedelta(minutes=adjust_min)
            st.info(
                f"地方時差補正 {adjust_min:+d}分を適用："
                f"補正後の出生日時 {birth.strftime('%Y年%m月%d日 %H:%M')}。"
                f"日柱は{'23時' if yako else '0時'}切替方式で判定します。"
            )
        if time_unknown:
            st.info(
                "出生時刻が不明のため、時柱に関する関係は表示しません。"
                "節入り日付近では月柱などが変わる可能性があります。"
            )

        # 四柱推命メニューと同じ日時・同じ夜子時設定を全計算に渡す。
        m = build_meishiki(birth, yako_next_day=yako)

        # 立春基準の「今年」
        now = datetime.datetime.now()
        _, this_year, _, _ = find_setsu(now)

        # 年運(今年1年分)
        nen = calc_nenun(
            birth, gender, start_year=this_year, n_years=1,
            yako_next_day=yako,
        )[0]
        if time_unknown:
            nen = {
                **nen,
                "命式との関係": _without_hour_relations(nen["命式との関係"]),
            }
        year_star = get_message("shichu_tsuhensei", nen["通変星"], {})

        st.markdown(
            f"<div class='luna-section-title'>◆ {name}さんの{this_year}年（{nen['干支']}）</div>"
            if name else
            f"<div class='luna-section-title'>◆ {this_year}年（{nen['干支']}）の運勢</div>",
            unsafe_allow_html=True,
        )

        rel = "、".join(nen["命式との関係"]) or "大きな衝突のない穏やかな巡り"
        kubo_line = ""
        if nen["空亡"]:
            kubo_line = "<br>今年は<b>空亡（天中殺）</b>の年。新しく始めるより、学び直しと充電に向く一年です。"
        st.markdown(
            f"<div class='luna-message'>"
            f"あなたの日干<b>{m['日干']}</b>から見て、今年は<b>{nen['通変星']}</b>・"
            f"<b>{nen['十二運']}</b>の年です。<br>"
            f"命式との関係: {rel}{kubo_line}</div>",
            unsafe_allow_html=True,
        )

        if year_star:
            st.markdown(
                f"<div class='luna-message'><b>{year_star.get('title', '')}</b><br>"
                f"{year_star.get('message', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

        # 現在の大運
        d = calc_daiun(birth, gender, yako_next_day=yako)
        age = this_year - birthday.year
        current = None
        for x in d["大運"]:
            if x["開始年齢"] <= age < x["開始年齢"] + 10:
                current = x
                break
        if current:
            st.markdown(
                "<div class='luna-section-title'>◆ いま歩んでいる大運</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='luna-message'>"
                f"{current['開始年齢']}歳からの10年は<b>{current['干支']}</b>"
                f"（{current['通変星']}・{current['十二運']}）の大運です。"
                f"今年の運気は、この大きな流れの中で巡っています。</div>",
                unsafe_allow_html=True,
            )

        # 月ごとの流れ
        st.markdown(
            "<div class='luna-section-title'>◆ 月ごとの流れ</div>",
            unsafe_allow_html=True,
        )
        getsu = calc_getsuun(birth, this_year, yako_next_day=yako)
        if time_unknown:
            getsu = [
                {**x, "命式との関係": _without_hour_relations(x["命式との関係"])}
                for x in getsu
            ]
        rows = [
            {
                "月": f"{x['暦月目安']}({x['節月']})",
                "節入り": f"{x['節入り']}〜",
                "干支": x["干支"],
                "通変星": x["通変星"],
                "十二運": x["十二運"],
                "空亡": "○" if x["空亡"] else "",
                "命式との関係": "、".join(x["命式との関係"]) or "-",
            }
            for x in getsu
        ]
        st.table(rows)
        st.caption("※ 月の切り替わりは節入り基準です。空亡○の月は無理をせず、整える時間に。")

        # レポートPDFダウンロード
        st.markdown(
            "<div class='luna-section-title'>◆ レポートPDF</div>",
            unsafe_allow_html=True,
        )
        kotoshi_data = {
            "year": this_year,
            "nikkan": m["日干"],
            "nen": nen,
            "current_daiun": current,
            "getsuun": getsu,
            "messages": {
                "year_star": year_star,
                "kubo": get_message("shichu_kubo", "general", ""),
            },
        }
        pdf_user_data = {
            "name": name,
            "birthday": f"{birthday.year}年{birthday.month}月{birthday.day}日",
            "reading_date": datetime.date.today().strftime("%Y年%m月%d日"),
            "gender": gender,
        }
        pdf_buf = create_kotoshi_pdf(pdf_user_data, kotoshi_data)
        st.download_button(
            label="📄 今年の運勢レポートPDFをダウンロード",
            data=pdf_buf,
            file_name=f"luna_kotoshi_{this_year}_{name or 'guest'}.pdf",
            mime="application/pdf",
            key="dl_kotoshi_pdf",
        )
