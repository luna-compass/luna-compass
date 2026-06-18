# menu.py
# Luna-compass トップメニュー画面

import streamlit as st


def show():
    """トップメニュー画面を表示する"""

    st.markdown("""
    <style>
    .menu-hero {
        text-align: center;
        padding: 6px 0 12px 0;
    }
    .menu-hero-title {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: 0.2em;
        color: #2b1b4b;
    }
    .menu-hero-sub {
        font-size: 12px;
        color: #7a6a9a;
        margin-top: 4px;
        font-style: italic;
    }
    .menu-grid {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-width: 480px;
        margin: 12px auto 0 auto;
    }
    .menu-card {
        background: rgba(255, 255, 255, 0.97);
        border-radius: 16px;
        border: 2px solid #d8b4fe;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.10);
        padding: 12px 16px 10px 16px;
        text-align: left;
    }
    .menu-card-top {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }
    .menu-card-icon {
        font-size: 32px;
        flex-shrink: 0;
    }
    .menu-card-title {
        font-size: 16px;
        font-weight: 700;
        color: #2b1b4b;
    }
    .menu-card-desc {
        font-size: 12px;
        color: #6b7280;
        line-height: 1.5;
        margin-bottom: 6px;
    }
    .menu-badge {
        display: inline-block;
        background: #f3e8ff;
        color: #7c3aed;
        font-size: 10px;
        border-radius: 999px;
        padding: 2px 10px;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .menu-badge-coming {
        display: inline-block;
        background: #f3f4f6;
        color: #9ca3af;
        font-size: 10px;
        border-radius: 999px;
        padding: 2px 10px;
        margin-top: 6px;
        font-weight: 600;
    }
    .menu-footer {
        text-align: center;
        margin-top: 36px;
        color: #9ca3af;
        font-size: 11px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ヒーローテキスト
    st.markdown("""
    <div class='menu-hero'>
        <div class='menu-hero-title'>🌙 Luna-compass</div>
        <div class='menu-hero-sub'>西洋占星術 × 数秘術　鑑定メニュー</div>
    </div>
    """, unsafe_allow_html=True)

    # ===== 総合鑑定カード =====
    st.markdown("""
    <div class='menu-grid'>
        <div class='menu-card'>
            <div class='menu-card-top'>
                <div class='menu-card-icon'>🌟</div>
                <div class='menu-card-title'>総合鑑定</div>
            </div>
            <div class='menu-card-desc'>ネイタルチャート（出生図）をもとに、あなたの本質・感情・思考・愛情・行動を多角的に鑑定します。数秘術も含めた総合鑑定書PDFをお届けします。</div>
            <div class='menu-badge'>✨ 鑑定書PDF付き</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 4, 1])
    with col_c:
        btn_general = st.button(
            "🌟 総合鑑定を始める",
            use_container_width=True,
            type="primary",
            key="menu_btn_general"
        )

    # ===== 相性占いカード =====
    st.markdown("""
    <div class='menu-grid'>
        <div class='menu-card'>
            <div class='menu-card-top'>
                <div class='menu-card-icon'>💑</div>
                <div class='menu-card-title'>相性占い</div>
            </div>
            <div class='menu-card-desc'>2人のホロスコープを重ねて、エレメント・太陽・月・金星×火星の相性を鑑定します。深い絆のヒントをお届けします。</div>
            <div class='menu-badge'>✨ 鑑定書PDF付き</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    col_l2, col_c2, col_r2 = st.columns([1, 4, 1])
    with col_c2:
        btn_compat = st.button(
            "💑 相性占いを始める",
            use_container_width=True,
            type="primary",
            key="menu_btn_compat"
        )

    # ===== タロットカード =====
    st.markdown("""
    <div class='menu-grid'>
        <div class='menu-card'>
            <div class='menu-card-top'>
                <div class='menu-card-icon'>🔮</div>
                <div class='menu-card-title'>タロット</div>
            </div>
            <div class='menu-card-desc'>1枚引き・3枚引き（過去・現在・未来）でメッセージをお届けします。今のあなたへのヒントが見つかります。</div>
            <div class='menu-badge'>✨ 今すぐ引ける</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    col_l3, col_c3, col_r3 = st.columns([1, 4, 1])
    with col_c3:
        btn_tarot = st.button(
            "🔮 タロットを引く",
            use_container_width=True,
            type="primary",
            key="menu_btn_tarot"
        )

    if btn_general:
        st.session_state["menu_selected"] = "general"
        st.rerun()

    if btn_compat:
        st.session_state["menu_selected"] = "compat"
        st.rerun()

    if btn_tarot:
        st.session_state["menu_selected"] = "tarot"
        st.rerun()

    # 将来追加予定メニュー（予告）
    st.markdown("""
    <div style='text-align:center; margin-top:28px;'>
        <span style='font-size:12px; color:#9ca3af;'>今後追加予定：</span>
        <span class='menu-badge-coming'>🔢 数秘術単独鑑定</span>
        <span style='margin:0 4px'></span>
        <span class='menu-badge-coming'>📅 今日の運勢</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='menu-footer'>
        Luna 占星術　Luna-compass　©2025 合同会社Lunacia
    </div>
    """, unsafe_allow_html=True)
