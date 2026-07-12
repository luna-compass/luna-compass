# -*- coding: utf-8 -*-
"""
tabs/cosmic_timeline.py
=======================
総合鑑定に「🌌 タイムライン」タブを追加するモジュール。
出生データから「👤 あなた」レイヤーの events.json を生成し、
ダウンロードできるようにする。

luna_web.py への組み込み(2行変更):
    from tabs import natal, transit, numerology, cosmic_timeline
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌙 ネイタル", "🌍 トランジット", "🔢 数秘術", "🌌 タイムライン",
    ])
    ...
    cosmic_timeline.show(tab4, user_info)
"""
import json

import pandas as pd
import streamlit as st

from utils import timeline_export


def show(tab, user_info):
    with tab:
        st.markdown("### 🌌 宇宙タイムライン連携")
        st.markdown(
            "ビッグバンから現在までをスクロールで旅する「宇宙タイムライン」に、"
            "**あなたの誕生・木星回帰・サターンリターン**を正確な天体暦計算で"
            "重ねるためのデータを生成します。"
        )

        if st.button("👤 タイムライン用データを生成", key="gen_timeline", type="primary"):
            with st.spinner("天体暦で木星と土星の回帰を計算しています..."):
                try:
                    st.session_state["timeline_json"] = \
                        timeline_export.build_export_json(user_info)
                except Exception as e:
                    st.error(f"計算に失敗しました: {e}")

        if "timeline_json" in st.session_state:
            data = json.loads(st.session_state["timeline_json"])
            events = data.get("events", [])

            st.success(f"{len(events)}件のパーソナルイベントを生成しました。")

            # プレビュー表
            df = pd.DataFrame(
                [{"日付": e["when"], "イベント": f'{e["icon"]} {e["title"]}'}
                 for e in events]
            )
            st.table(df)

            st.download_button(
                "📥 events.json をダウンロード",
                data=st.session_state["timeline_json"],
                file_name="events.json",
                mime="application/json",
                key="dl_timeline",
            )
            st.caption(
                "ダウンロードした events.json を、宇宙タイムラインの "
                "index.html と同じフォルダに置いてページを開くと、"
                "「👤 あなた」レイヤーとして表示されます。"
                "(お客様への納品時は index.html + events.json の2ファイルを渡すだけでOK)"
            )
