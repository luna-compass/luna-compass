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
                    st.session_state["timeline_html"] = \
                        timeline_export.build_delivery_html(user_info)
                    st.session_state["timeline_name"] = \
                        (user_info.get("name") or "guest").strip() or "guest"
                except FileNotFoundError:
                    st.session_state.pop("timeline_html", None)
                    st.warning(
                        "納品用HTMLの雛形(cosmic_timeline_template.html)が"
                        "見つかりません。タイムラインの index.html をコピーして、"
                        "luna_web.py と同じフォルダにこの名前で置いてください。"
                        "(events.json の生成だけは利用できます)"
                    )
                    try:
                        st.session_state["timeline_json"] = \
                            timeline_export.build_export_json(user_info)
                    except Exception as e:
                        st.error(f"計算に失敗しました: {e}")
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

            # --- 納品用(お客様にはこちらを渡す) ---
            if "timeline_html" in st.session_state:
                st.download_button(
                    "📦 納品用HTML(1ファイル)をダウンロード",
                    data=st.session_state["timeline_html"],
                    file_name=f"cosmic_timeline_{st.session_state['timeline_name']}.html",
                    mime="text/html",
                    key="dl_timeline_html",
                    type="primary",
                )
                st.caption(
                    "★お客様への納品はこの1ファイルだけでOK。"
                    "ダブルクリックで開くだけで動きます(通信・設定不要)。"
                )

            # --- 開発用(自分のタイムラインフォルダに置く用) ---
            st.download_button(
                "📥 events.json をダウンロード(開発用)",
                data=st.session_state["timeline_json"],
                file_name="events.json",
                mime="application/json",
                key="dl_timeline",
            )
            st.caption(
                "events.json は自分のタイムライン(index.html)と同じフォルダに"
                "置いて使う開発・確認用です。"
            )
