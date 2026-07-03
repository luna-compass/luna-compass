# -*- coding: utf-8 -*-
"""
tabs/shichusuimei.py - 四柱推命(開発中)

luna_web.py のメニュー分岐から show_direct() で呼ばれる。
iching / compatibility と同じ規約。
"""
import datetime

import streamlit as st

from utils.shichusuimei import (build_meishiki, calc_daiun, calc_kakukyoku, calc_nenun,
                                detect_kankei, detect_shinsatsu,
                                getsurei, natchin, KAN_GOGYO, SHI_GOGYO, ZOKAN)
from utils.messages_loader import get_message


def show_direct():
    st.markdown("### 🀄 四柱推命(開発中)")
    st.caption("節入りは太陽黄経による精密計算。境界±1時間は警告を表示します。")

    with st.expander("👤 基本情報を入力する", expanded=True):
        mode = st.radio(
            "占う対象",
            ("自分を占う", "別の人を占う"),
            key="mode_shichu",
            horizontal=True,
        )

        if mode == "自分を占う":
            default_name = "Luna"
            default_date = datetime.date(1968, 5, 27)
            default_hour = 0
            default_min = 0
        else:
            default_name = ""
            default_date = datetime.date(1990, 1, 1)
            default_hour = 12
            default_min = 0

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("お名前", value=default_name,
                                 key="name_shichu", help="ニックネームでもOKです")
        with col2:
            birthday = st.date_input(
                "生年月日",
                value=default_date,
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today(),
                key="birthday_shichu",
            )

        time_unknown = st.checkbox(
            "出生時刻が不明（時柱を省いた三柱で表示）",
            value=False,
            key="time_unknown_shichu",
        )

        gender = st.radio(
            "性別（大運の順行・逆行の判定に使用します）",
            ("女", "男"),
            key="gender_shichu",
            horizontal=True,
        )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            birth_hour = st.number_input(
                "出生時（時）", min_value=0, max_value=23, value=default_hour,
                key="hour_shichu", disabled=time_unknown,
            )
        with col_t2:
            birth_minute = st.number_input(
                "出生時（分）", min_value=0, max_value=59, value=default_min,
                key="minute_shichu", disabled=time_unknown,
            )

    if st.button("命式を計算する", key="calc_shichu", type="primary"):
        hour = 12 if time_unknown else int(birth_hour)
        minute = 0 if time_unknown else int(birth_minute)
        birth = datetime.datetime(birthday.year, birthday.month, birthday.day, hour, minute)

        m = build_meishiki(birth)

        # 節入り境界警告(時刻不明時は時刻由来の判定自体が曖昧なので常に注意書き)
        if m["節入り境界警告"] and not time_unknown:
            gap_min = int(m["直近節入りとの差"].total_seconds() // 60)
            st.warning(
                f"⚠ 節入りの境界まで約{gap_min}分です。"
                "出生時刻のわずかな誤差で月柱(場合により年柱も)が変わる可能性があります。"
            )
        if time_unknown:
            st.info("出生時刻が不明のため、時柱を省いた三柱で表示しています。"
                    "生年月日が節入り日の場合、月柱が前後する可能性があります。")

        st.markdown(
            f"<div class='luna-section-title'>◆ {name}さんの命式</div>"
            if name else "<div class='luna-section-title'>◆ 命式</div>",
            unsafe_allow_html=True,
        )

        # 表示対象の柱(時刻不明なら時柱を除外)
        pillar_names = ["年柱", "月柱", "日柱"] if time_unknown else ["年柱", "月柱", "日柱", "時柱"]

        rows = []
        for pname in pillar_names:
            kan, shi = m["四柱"][pname]
            star = m["通変星"][pname]
            rows.append({
                "柱": pname,
                "干支": f"{kan}{shi}",
                "蔵干(初→本気)": "→".join(m["蔵干"][pname]),
                "通変星(天干)": star["天干"],
                "通変星(蔵干本気)": star["蔵干本気"],
                "十二運": m["十二運"][pname],
            })
        st.table(rows)

        # 空亡
        kubo_s = "・".join(m["空亡"])
        if m["空亡該当柱"]:
            hit = "・".join(m["空亡該当柱"])
            st.markdown(
                f"<div class='luna-message'>空亡(天中殺)は <b>{kubo_s}</b> です。"
                f"命式中では <b>{hit}</b> が空亡に当たっています。</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='luna-message'>空亡(天中殺)は <b>{kubo_s}</b> です。"
                "命式中に空亡に当たる柱はありません。</div>",
                unsafe_allow_html=True,
            )

        kubo_general = get_message("shichu_kubo", "general", "")
        if kubo_general:
            st.markdown(
                f"<div class='luna-message'>{kubo_general.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

        # 干支の関係(干合・支合・三合・刑・冲・害・破)
        kankei = detect_kankei(m["四柱"])
        if time_unknown:
            kankei = [f for f in kankei if "時柱" not in f["柱"]]
        if kankei:
            st.markdown("<div class='luna-section-title'>◆ 干支の関係</div>", unsafe_allow_html=True)
            st.table([{"種類": f["種類"], "内容": f["内容"], "柱": f["柱"]} for f in kankei])

        # 神殺
        shinsatsu = detect_shinsatsu(m)
        if time_unknown:
            shinsatsu = [f for f in shinsatsu if "時柱" not in f["該当"]]
        if shinsatsu:
            st.markdown("<div class='luna-section-title'>◆ 神殺・特殊星</div>", unsafe_allow_html=True)
            st.table([{"神殺": f["神殺"], "該当": f["該当"], "説明": f["説明"]} for f in shinsatsu])

        # 日干
        e, yang = m["日干五行"]
        g_state, g_toku = getsurei(m["日干"], m["四柱"]["月柱"][1])
        d_kan_p, d_shi_p = m["四柱"]["日柱"]
        st.markdown(
            f"<div class='luna-message'>日干は <b>{m['日干']}({e}の{'陽' if yang else '陰'})</b> です。<br>"
            f"月令は <b>{g_state}({'得令' if g_toku else '失令'})</b>、"
            f"日柱の納音は <b>{natchin(d_kan_p, d_shi_p)}</b> です。</div>",
            unsafe_allow_html=True,
        )

        # 日干メッセージ(messages_data.json: shichu_nikkan)
        nk = get_message("shichu_nikkan", m["日干"], {})
        if nk:
            st.markdown(f"<div class='luna-section-title'>◆ {nk.get('title', '日干メッセージ')}</div>",
                        unsafe_allow_html=True)
            body = nk.get("message", "").replace("\n", "<br>")
            talent = nk.get("talent", "")
            challenge = nk.get("challenge", "").replace("\n", "<br>")
            keywords = nk.get("keywords", "")
            st.markdown(
                f"<div class='luna-message'>{body}<br><br>"
                f"<b>【才能】</b>{talent}<br>"
                f"<b>【課題】</b>{challenge}<br>"
                f"<b>【キーワード】</b>{keywords}</div>",
                unsafe_allow_html=True,
            )

        # 中心星(元命: 月柱蔵干本気の通変星)
        ganmei = m["通変星"]["月柱"]["蔵干本気"]
        ts = get_message("shichu_tsuhensei", ganmei, {})
        if ts:
            st.markdown(f"<div class='luna-section-title'>◆ あなたの中心星（元命）: {ts.get('title', ganmei)}</div>",
                        unsafe_allow_html=True)
            st.markdown(
                f"<div class='luna-message'>{ts.get('message', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

        # 格局
        kaku = calc_kakukyoku(m)
        st.markdown(f"<div class='luna-section-title'>◆ 格局: {kaku['格局']}</div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div class='luna-message'>判定根拠: {kaku['根拠']}<br>"
            "<span style='font-size:12px; color:#6b7280;'>※普通格局(建禄格・月刃格・八格)による判定です。"
            "従格などの特別格局は対象外です。</span></div>",
            unsafe_allow_html=True,
        )

        # 日柱の十二運
        d_juniun = m["十二運"]["日柱"]
        ju = get_message("shichu_juniun", d_juniun, {})
        if ju:
            st.markdown(f"<div class='luna-section-title'>◆ 日柱の十二運: {ju.get('title', d_juniun)}</div>",
                        unsafe_allow_html=True)
            st.markdown(
                f"<div class='luna-message'>{ju.get('message', '')}</div>",
                unsafe_allow_html=True,
            )

        # 五行バランス(時刻不明時は三柱分で再集計)
        st.markdown("<div class='luna-section-title'>◆ 五行バランス</div>", unsafe_allow_html=True)
        if time_unknown:
            bal = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
            for pname in pillar_names:
                kan, shi = m["四柱"][pname]
                bal[KAN_GOGYO[kan][0]] += 1
                bal[SHI_GOGYO[shi]] += 1
                bal[KAN_GOGYO[ZOKAN[shi][-1]][0]] += 1
        else:
            bal = m["五行バランス"]

        cols = st.columns(5)
        for c, (gogyo, cnt) in zip(cols, bal.items()):
            c.metric(gogyo, cnt)

        # 大運
        st.markdown("<div class='luna-section-title'>◆ 大運（10年ごとの運気の流れ）</div>", unsafe_allow_html=True)
        d = calc_daiun(birth, gender)
        ry, rm = d["立運"]
        st.markdown(
            f"<div class='luna-message'>大運は <b>{d['順逆']}</b>、"
            f"立運は <b>{ry}歳{rm}ヶ月</b> です。"
            f"{'出生時刻が不明のため、立運は目安としてご覧ください。' if time_unknown else ''}</div>",
            unsafe_allow_html=True,
        )
        daiun_rows = [
            {
                "開始年齢": f"{x['開始年齢']}歳〜",
                "干支": x["干支"],
                "通変星": x["通変星"],
                "十二運": x["十二運"],
            }
            for x in d["大運"]
        ]
        st.table(daiun_rows)

        # 年運(今年から10年)
        st.markdown("<div class='luna-section-title'>◆ 年運（今年からの10年）</div>", unsafe_allow_html=True)
        nenun = calc_nenun(birth, gender, start_year=datetime.date.today().year, n_years=10)
        nenun_rows = [
            {
                "西暦": f"{x['西暦']}年",
                "年齢": f"{x['年齢']}歳",
                "干支": x["干支"],
                "通変星": x["通変星"],
                "十二運": x["十二運"],
                "納音": x["納音"],
                "空亡": "○" if x["空亡"] else "",
                "大運": x["大運"],
            }
            for x in nenun
        ]
        st.table(nenun_rows)
        st.caption("※年齢は各年に迎える満年齢の目安です。年の切り替わりは立春基準で計算しています。")

        with st.expander("計算メモ(開発用)"):
            st.write(f"換算年(立春基準): {m['換算年(立春基準)']}年")
            st.write(f"直近節入りとの差: {m['直近節入りとの差']}")
