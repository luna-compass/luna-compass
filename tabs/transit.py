# tabs/transit.py
# タブ2：トランジット

import streamlit as st
import datetime
import io
import swisseph as swe

from utils.astro import (
    make_ts_from_local, get_sun_info, get_moon_info,
    get_body_longitudes_ts, get_planet_signs_ts,
    split_sign_degree, get_sign, simple_compare_message,
    detect_special_patterns
)
from utils.messages import (
    get_transit_aspect_message
)
from utils.chart import plot_horoscope


def get_aspects_transit(natal_planets, transit_planets):
    """トランジット天体×ネイタル天体のアスペクトを計算"""
    aspects = []
    aspect_defs = {
        "コンジャンクション": 0,
        "セクスタイル": 60,
        "スクエア": 90,
        "トライン": 120,
        "オポジション": 180
    }
    orbs = {
        "コンジャンクション": 8,
        "セクスタイル": 4,
        "スクエア": 6,
        "トライン": 6,
        "オポジション": 8
    }

    for t_name, t_deg in transit_planets.items():
        for n_name, n_deg in natal_planets.items():
            diff = abs(t_deg - n_deg) % 360
            if diff > 180:
                diff = 360 - diff
            for asp_name, asp_angle in aspect_defs.items():
                if abs(diff - asp_angle) <= orbs[asp_name]:
                    aspects.append({
                        "transit": t_name,
                        "natal": n_name,
                        "type": asp_name,
                        "orb": abs(diff - asp_angle)
                    })
    # 優先度順に並び替え（個人天体優先→アスペクト強度順→オーブ順）
    PERSONAL = {"太陽", "月", "水星", "金星", "火星"}
    ASPECT_PRIO = {"コンジャンクション":0,"オポジション":1,"スクエア":2,"トライン":3,"セクスタイル":4}
    aspects.sort(key=lambda x: (
        (0 if x["natal"] in PERSONAL else 1) + (0 if x["transit"] in PERSONAL else 1),
        ASPECT_PRIO.get(x["type"], 5),
        x["orb"]
    ))
    return aspects


def show(tab, user_info):
    with tab:

        birthday     = user_info["birthday"]
        birth_hour   = user_info["birth_hour"]
        birth_minute = user_info["birth_minute"]
        tz_offset    = user_info["tz_offset"]
        lat          = user_info["lat"]
        lon          = user_info["lon"]

        st.markdown("### 🌍 トランジット（今日・気になる日の流れ）")

        transit_date = st.date_input(
            "トランジットを見る日",
            value=datetime.date.today(),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            key="transit_date"
        )

        btn_transit = st.button("🌍 トランジットを見る", use_container_width=True, type="primary", key="btn_transit")

        if btn_transit:
            # ===== ネイタル計算 =====
            t_natal = make_ts_from_local(birthday, int(birth_hour), int(birth_minute), tz_offset)
            natal_longs = get_body_longitudes_ts(t_natal)
            sun_sign, sun_deg, _ = get_sun_info(t_natal)
            moon_sign, moon_deg, _ = get_moon_info(t_natal)
            sun_text  = f"{sun_sign} {sun_deg:.2f}°"
            moon_text = f"{moon_sign} {moon_deg:.2f}°"

            # ===== ハウス計算 =====
            dt_utc = datetime.datetime(
                birthday.year, birthday.month, birthday.day,
                int(birth_hour), int(birth_minute)
            ) - datetime.timedelta(hours=tz_offset)
            jd = swe.julday(
                dt_utc.year, dt_utc.month, dt_utc.day,
                dt_utc.hour + dt_utc.minute / 60.0
            )
            house_cusps, ascmc = swe.houses(jd, lat, lon, b'P')
            houses = house_cusps

            # ===== トランジット計算 =====
            t_transit = make_ts_from_local(transit_date, 12, 0, tz_offset)
            t_sun_sign, t_sun_deg, _ = get_sun_info(t_transit)
            t_moon_sign, t_moon_deg, _ = get_moon_info(t_transit)
            trans_planets = get_planet_signs_ts(t_transit)
            transit_longs = get_body_longitudes_ts(t_transit)

            trans_sun_text  = f"{t_sun_sign} {t_sun_deg:.2f}°"
            trans_moon_text = f"{t_moon_sign} {t_moon_deg:.2f}°"

            st.write("トランジット日：", transit_date)

            # ===== ①ホロスコープ（ネイタル＋トランジット重ね表示） =====
            st.markdown("### 🌙 ホロスコープ（ネイタル＋トランジット）")
            st.caption("● ネイタル天体　▲ トランジット天体（青）")
            fig = plot_horoscope(natal_longs, houses, transit_longs)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")  # 表示用はdpi=150で十分
            buf.seek(0)
            st.image(buf, use_container_width=True)

            buf2 = io.BytesIO()
            fig.savefig(buf2, format="png", bbox_inches="tight")
            buf2.seek(0)
            st.download_button(
                label="☁ ホロスコープ画像をダウンロード",
                data=buf2,
                file_name="luna_transit.png",
                mime="image/png",
            )


            # ===== 星座・惑星記号の見方 =====
            with st.expander("🔍 ホロスコープの記号の見方"):
                st.markdown("""
**【星座記号の見方】**

| 記号 | 星座 | 記号 | 星座 |
|:---:|:---:|:---:|:---:|
| ♈ | 牡羊座 | ♎ | 天秤座 |
| ♉ | 牡牛座 | ♏ | 蠍座 |
| ♊ | 双子座 | ♐ | 射手座 |
| ♋ | 蟹座   | ♑ | 山羊座 |
| ♌ | 獅子座 | ♒ | 水瓶座 |
| ♍ | 乙女座 | ♓ | 魚座   |

**【惑星記号の見方】**

| 記号 | 惑星 | 記号 | 惑星 |
|:---:|:---:|:---:|:---:|
| ☉ | 太陽 | ♃ | 木星 |
| ☽ | 月 | ♄ | 土星 |
| ☿ | 水星 | ♅ | 天王星 |
| ♀ | 金星 | ♆ | 海王星 |
| ♂ | 火星 | ♇ | 冥王星 |

**【トランジット天体について】**
▲マークがトランジット（今日）の天体、●マークがネイタル（生まれた時）の天体です。

**【度数の見方】**
例：`☉ 双子座5°` → 太陽が双子座5度にあります
""")

            # ===== ②今日の太陽・月 =====
            st.markdown("---")
            st.markdown("### ☀ 今日の太陽・月")
            st.write(f"☀ 太陽：{trans_sun_text}")
            st.write(f"☽ 月：{trans_moon_text}")

            # ===== ③今日の流れメッセージ =====
            st.markdown("### ✨ 今日の流れ")
            flow_messages = {
                "牡羊座": {
                    "title": "🔥 行動と情熱の日",
                    "body": "新しいことをスタートするのに最適な日です。迷いを捨てて動くほど流れが開けます。直感を信じて、思い切った一歩を踏み出しましょう。エネルギーが高まっているので、体を動かすことも運気アップにつながります。",
                },
                "牡牛座": {
                    "title": "🌿 安定と現実の日",
                    "body": "お金・所有・価値観を整える日です。衝動買いや無駄遣いに注意しつつ、本当に大切なものを見極めましょう。五感を喜ばせることが運気アップのカギ。おいしいものを食べたり、心地よい空間で過ごすと充実した一日になります。",
                },
                "双子座": {
                    "title": "💨 情報と対話の日",
                    "body": "コミュニケーション・情報収集・発信が鍵になる日です。人と話すほどチャンスが広がり、新しいアイデアが生まれやすいです。複数のことを同時進行で進めても上手くいきやすい日。好奇心のままに動いてみましょう。",
                },
                "蟹座": {
                    "title": "💧 心と家の日",
                    "body": "感情・家族・安心がテーマの日です。身近な人を大切にすることで運が上がります。無理に外向きに動くより、自分の心地よい場所でゆっくり過ごすことが大切。感情に素直になることで、大切なものが見えてきます。",
                },
                "獅子座": {
                    "title": "☀ 輝きと表現の日",
                    "body": "自分を表現することで運が動く日です。主役意識で堂々と動くほど評価が上がります。創造的な活動・趣味・人前に出る機会があれば積極的に。褒められたり、認められる出来事が起きやすい日です。",
                },
                "乙女座": {
                    "title": "🌾 整理と改善の日",
                    "body": "細かい見直し・整理・改善が運気アップにつながる日です。デスクや部屋の片付け、データ整理など地道な作業が大きな成果につながります。健康面の見直しにも良いタイミング。丁寧に一つひとつこなすことが大切です。",
                },
                "天秤座": {
                    "title": "⚖️ 調和と関係の日",
                    "body": "人間関係・パートナーシップ・バランスが鍵になる日です。対話を大切にし、相手の気持ちに寄り添うことで流れが良くなります。美しいものに触れることも運気アップに。一人で抱え込まず、誰かと協力することで良い結果が生まれます。",
                },
                "蠍座": {
                    "title": "🔮 深さと集中の日",
                    "body": "一つのことに深く集中するほど大きな成果が出る日です。表面的なことより、物事の本質を掘り下げることで新しい発見があります。感情が深まりやすい日でもあるので、信頼できる人との深い対話が心を豊かにしてくれます。",
                },
                "射手座": {
                    "title": "🏹 拡大と挑戦の日",
                    "body": "学び・冒険・新しい挑戦に向いた日です。いつもより視野を広げて、遠くに目を向けることで運が動きます。海外・異文化・哲学的なことへの関心が高まりやすい日。楽観的に動くことで、予想以上の結果がついてきます。",
                },
                "山羊座": {
                    "title": "🏔️ 努力と結果の日",
                    "body": "仕事・目標・現実的な行動が評価につながる日です。地道な努力が確実に実を結びやすいタイミング。長期的な計画を立てたり、重要な決断をするのに向いています。責任感を持って取り組むほど、信頼と成果が積み上がります。",
                },
                "水瓶座": {
                    "title": "⚡ 革新と発見の日",
                    "body": "発想の転換・独自のアイデア・新しいやり方が突破口になる日です。常識にとらわれず、いつもと違うアプローチを試してみましょう。人との出会いや情報交換からインスピレーションを得やすい日。未来に向けた行動が吉です。",
                },
                "魚座": {
                    "title": "🌊 感性と直感の日",
                    "body": "感受性・直感・流れに乗ることが大切な日です。無理に頑張るより、自然な流れに委ねると良い方向へ進みます。芸術・音楽・癒しに触れることで心が整います。夢や直感からのメッセージを大切にして、感性を信じて動きましょう。",
                },
            }
            flow = flow_messages.get(t_sun_sign)
            if flow:
                st.markdown(f"**{flow['title']}**")
                st.markdown(f"<div class='luna-message'>{flow['body']}</div>", unsafe_allow_html=True)

            # ===== ④ネイタルとの比較 =====
            st.markdown("---")
            st.markdown("### 🔄 ネイタルとの比較")

            compare_planets = [
                ("☀ 太陽", sun_text, trans_sun_text, "太陽"),
                ("☽ 月", moon_text, trans_moon_text, "月"),
            ]
            # 水星・金星・火星のネイタル・トランジットを追加
            for p_jp, p_key in [("☿ 水星", "水星"), ("♀ 金星", "金星"), ("♂ 火星", "火星")]:
                n_sign, n_deg = split_sign_degree(natal_longs.get(p_key, 0))
                t_sign, t_deg = split_sign_degree(transit_longs.get(p_key, 0))
                compare_planets.append((
                    p_jp,
                    f"{n_sign} {n_deg:.2f}°",
                    f"{t_sign} {t_deg:.2f}°",
                    p_jp.split(" ")[1]
                ))

            for title, n_text, t_text, label in compare_planets:
                st.markdown(f"**{title}**")
                st.write(f"ネイタル：{n_text}　→　トランジット：{t_text}")
                st.markdown(f"<div class='luna-message'>{simple_compare_message(n_text, t_text, label)}</div>", unsafe_allow_html=True)

            # ===== ⑤トランジット×ネイタル アスペクト =====
            st.markdown("---")
            st.markdown("### 🔮 トランジット×ネイタル アスペクト")
            st.caption("今この人の星に何が起きているかを示します")

            # 重要な天体に絞る
            natal_key_planets = {
                "太陽": natal_longs.get("太陽", 0),
                "月": natal_longs.get("月", 0),
                "水星": natal_longs.get("水星", 0),
                "金星": natal_longs.get("金星", 0),
                "火星": natal_longs.get("火星", 0),
            }
            transit_key_planets = {
                "木星": transit_longs.get("木星", 0),
                "土星": transit_longs.get("土星", 0),
                "天王星": transit_longs.get("天王星", 0),
                "海王星": transit_longs.get("海王星", 0),
                "冥王星": transit_longs.get("冥王星", 0),
            }

            aspects = get_aspects_transit(natal_key_planets, transit_key_planets)

            if aspects:
                for a in aspects:
                    asp_icon = {
                        "コンジャンクション": "🔴",
                        "トライン": "🟢",
                        "スクエア": "🟠",
                        "セクスタイル": "🔵",
                        "オポジション": "🟣"
                    }.get(a["type"], "⚪")

                    st.markdown(f"**{asp_icon} トランジット{a['transit']} × ネイタル{a['natal']}：{a['type']}**")
                    msg = get_transit_aspect_message(a["transit"], a["natal"], a["type"])
                    st.markdown(f"<div class='luna-message'>{msg}</div>", unsafe_allow_html=True)
            else:
                st.write("現在、主要なアスペクトはありません。")

            # ===== グランドトライン・グランドクロス判定（トランジット込み） =====
            patterns = detect_special_patterns(natal_longs, transit_longs)
            gt_natal = patterns["natal_grand_trine"]
            gc_natal = patterns["natal_grand_cross"]
            gt_transit = patterns["transit_grand_trine"]
            gc_transit = patterns["transit_grand_cross"]

            if gt_natal or gc_natal or gt_transit or gc_transit:
                st.markdown("---")
                st.markdown("### ✨ 特別なパターン")

            for gt in gt_natal:
                elem = gt["element"]
                planets_str = "・".join(gt["planets"])
                elem_signs_note = {
                    "火": "（牡羊座・獅子座・射手座のエレメント）",
                    "地": "（牡牛座・乙女座・山羊座のエレメント）",
                    "風": "（双子座・天秤座・水瓶座のエレメント）",
                    "水": "（蟹座・蠍座・魚座のエレメント）",
                }.get(elem, "")
                elem_base = {
                    "火": "情熱・行動力・創造性が大きく調和しています。",
                    "地": "現実的な安定・忍耐・実行力が深く調和しています。",
                    "風": "知性・コミュニケーション・自由な発想が調和しています。",
                    "水": "感情・共感・直感が深く調和しています。",
                    "混合": "異なるエネルギーが大きく調和したグランドトラインです。",
                }.get(elem, "")
                elem_msg = f"{planets_str}が{elem}のエレメントで大きな三角形を形成しています。{elem_base}"
                st.markdown(f"""
<div class='luna-message'>
🔺 <b>【ネイタル】グランドトライン（{elem}のエレメント）{elem_signs_note}</b><br>
天体：{planets_str}<br><br>
{elem_msg}
</div>
""", unsafe_allow_html=True)

            for gc in gc_natal:
                mode = gc["mode"]
                planets_str = "・".join(gc["planets"])
                mode_base = {
                    "活動": "変化と行動のエネルギーが四方向から働いています。",
                    "固定": "強い意志と粘り強さが四方向から働いています。",
                    "柔軟": "適応力と変化への対応力が四方向から働いています。",
                    "不定": "強烈なエネルギーが四方向から交差しています。",
                }.get(mode, "")
                mode_msg = f"{planets_str}が{mode}モードで大きな十字を形成しています。{mode_base}"
                st.markdown(f"""
<div class='luna-message'>
✚ <b>【ネイタル】グランドクロス（{mode}モード）</b><br>
天体：{planets_str}<br><br>
{mode_msg}
</div>
""", unsafe_allow_html=True)

            for gt in gt_transit:
                if gt in gt_natal:
                    continue
                elem = gt["element"]
                planets_str = "・".join([p.replace("T_","トランジット") for p in gt["planets"]])
                elem_signs_note = {
                    "火": "（牡羊座・獅子座・射手座のエレメント）",
                    "地": "（牡牛座・乙女座・山羊座のエレメント）",
                    "風": "（双子座・天秤座・水瓶座のエレメント）",
                    "水": "（蟹座・蠍座・魚座のエレメント）",
                }.get(elem, "")
                elem_base = {
                    "火": "情熱・行動・創造のエネルギーが今の流れで大きく調和しています。積極的に動く絶好のタイミングです。",
                    "地": "安定・実行・現実化のエネルギーが今の流れで調和しています。着実な行動が大きな実りを生みます。",
                    "風": "知性・表現・つながりのエネルギーが今の流れで調和しています。発信や学びに最高のタイミングです。",
                    "水": "感情・直感・癒しのエネルギーが今の流れで調和しています。感性を信じて動くと良い流れが生まれます。",
                    "混合": "今の天体の流れがあなたのチャートと大きなトラインを形成しています。",
                }.get(elem, "")
                elem_msg = f"{planets_str}が{elem}のエレメントで大きな三角形を形成しています。{elem_base}"
                st.markdown(f"""
<div class='luna-message'>
🔺 <b>【トランジット】グランドトライン（{elem}のエレメント）{elem_signs_note}</b><br>
天体：{planets_str}<br><br>
{elem_msg}
</div>
""", unsafe_allow_html=True)

            for gc in gc_transit:
                if gc in gc_natal:
                    continue
                mode = gc["mode"]
                planets_str = "・".join([p.replace("T_","トランジット") for p in gc["planets"]])
                mode_base = {
                    "活動": "今の天体の流れがあなたのチャートと大きな十字を形成しています。多くのテーマと同時に向き合う時期ですが、乗り越えた先に大きな成長があります。",
                    "固定": "強固なエネルギーが今の流れで交差しています。粘り強さと忍耐が大きな力になります。",
                    "柔軟": "今の天体の流れが適応力を試す十字を形成しています。柔軟に対応することで突破口が開けます。",
                    "不定": "今の流れがあなたのチャートと強いグランドクロスを形成しています。",
                }.get(mode, "")
                mode_msg = f"{planets_str}が{mode}モードで大きな十字を形成しています。{mode_base}"
                st.markdown(f"""
<div class='luna-message'>
✚ <b>【トランジット】グランドクロス（{mode}モード）</b><br>
天体：{planets_str}<br><br>
{mode_msg}
</div>
""", unsafe_allow_html=True)

            # ===== ⑥注目の外惑星 =====
            st.markdown("---")
            st.markdown("### ★ 外惑星の動き")
            st.caption("ゆっくり動く惑星は長期的な流れを示します")

            outer_messages = {
                "木星": {
                    "牡羊座": "行動と挑戦の分野で運が拡大する時代。自分から動く人に大きなチャンスが訪れます。",
                    "牡牛座": "豊かさ・安定・価値観の分野で拡大の流れ。物質的な豊かさと本質的な価値が広がります。",
                    "双子座": "情報・コミュニケーション・学びの分野で運が広がる時代。言葉と知識でチャンスをつかめます。",
                    "蟹座": "家庭・感情・安心の分野で発展の流れ。心のつながりと居場所づくりに幸運があります。",
                    "獅子座": "創造性・自己表現・恋愛の分野で運が拡大。自信を持って輝くほど成功が近づきます。",
                    "乙女座": "仕事・健康・実務の分野で発展の時代。地道な努力が大きな実りにつながります。",
                    "天秤座": "人間関係・パートナーシップの分野で幸運が広がります。縁と協力で運が開けます。",
                    "蠍座": "変容・深い絆・共有の分野で拡大の流れ。本気で取り組むほど大きく伸びます。",
                    "射手座": "自由・学び・海外の分野で運が最大化する時代。広い世界へ飛び出すほど運が開けます。",
                    "山羊座": "社会的成功・キャリアの分野で発展の流れ。努力と実力が評価される時代です。",
                    "水瓶座": "革新・コミュニティ・未来志向の分野で運が広がります。個性と独自性が力になります。",
                    "魚座": "感性・癒し・精神性の分野で拡大の流れ。見えない世界との縁が深まる時代です。",
                },
                "土星": {
                    "牡羊座": "行動と自立に試練と成長のテーマがある時代。粘り強く動くことで本物の実力が育ちます。",
                    "牡牛座": "お金・価値観・安定に慎重さが求められる時代。堅実な積み重ねが長期的な豊かさにつながります。",
                    "双子座": "言葉・学び・コミュニケーションに深さと責任が求められます。真剣な学びが大きな力になります。",
                    "蟹座": "家庭・感情・安心のテーマで試練がある時代。内面の強さと自立心を育てる時期です。",
                    "獅子座": "自己表現・創造性に制限を感じやすい時代ですが、乗り越えると本物の自信が育ちます。",
                    "乙女座": "仕事・健康・日常に規律と努力が求められます。丁寧な積み上げが信頼と実力を生みます。",
                    "天秤座": "対人関係・パートナーシップに課題がある時代。真剣に向き合うことで深い絆が育ちます。",
                    "蠍座": "変容・深い感情に試練がある時代。手放しと再生を通じて圧倒的な強さを手にします。",
                    "射手座": "自由と責任のバランスが問われる時代。哲学的な深さと誠実さが育まれます。",
                    "山羊座": "社会的責任・キャリアに重要な試練がある時代。努力と誠実さで大きな成功をつかみます。",
                    "水瓶座": "革新と責任が問われる時代。個性を活かしながら社会に貢献する形を模索します。",
                    "魚座": "精神性・感受性に課題がある時代。現実と感性のバランスを取りながら深く成長します。",
                },
                "天王星": {
                    "牡羊座": "個人の自由と革命が加速する時代。自分らしさを取り戻す動きが世界に広がっています。",
                    "牡牛座": "お金・価値観・地球環境に革命が起きる時代。本物の豊かさとは何かが問われています。",
                    "双子座": "情報・AI・コミュニケーションに革命が起きる時代。知識と発信の在り方が大きく変わります。",
                    "蟹座": "家族・居場所・感情の在り方に変化が起きる時代。新しい家族の形が生まれます。",
                    "獅子座": "表現・創造・エンターテインメントに革命が起きる時代。個性の輝きが社会を動かします。",
                    "乙女座": "仕事・健康・テクノロジーに革命が起きる時代。日常の仕組みが大きく変わっていきます。",
                    "天秤座": "人間関係・法律・美意識に革命が起きる時代。関係性の在り方が根本から変わります。",
                    "蠍座": "金融・変容・潜在意識に革命が起きる時代。深い部分からの変化が社会を動かします。",
                    "射手座": "思想・宗教・海外との関係に革命が起きる時代。価値観の多様化が加速します。",
                    "山羊座": "社会構造・政治・権力に革命が起きる時代。古い仕組みが更新されていきます。",
                    "水瓶座": "テクノロジー・人権・コミュニティに革命が起きる時代。未来志向の変化が加速します。",
                    "魚座": "精神性・芸術・見えない世界に革命が起きる時代。感性と直感が社会を変えていきます。",
                },
                "海王星": {
                    "牡羊座": "個人の夢と理想が新しい形で広がる時代。情熱と感性が融合した創造性が開花します。",
                    "牡牛座": "豊かさと美の概念が変容する時代。本物の価値と感覚的な豊かさへの関心が高まります。",
                    "双子座": "言葉・情報・ネットワークに幻想と直感が溶け込む時代。創造的な発信が力を持ちます。",
                    "蟹座": "家族・感情・故郷への深い共感が広がる時代。癒しと優しさが社会に溶け込みます。",
                    "獅子座": "創造性・芸術・エンターテインメントに夢と幻想が広がる時代です。",
                    "乙女座": "奉仕・癒し・日常に繊細な感性が広がる時代。丁寧さと優しさが力を持ちます。",
                    "天秤座": "愛・調和・美に理想が高まる時代。人との美しいつながりへの憧れが広がります。",
                    "蠍座": "深い精神世界・変容・直感に夢と霊感が溶け込む時代。見えない世界との縁が深まります。",
                    "射手座": "自由・哲学・精神的探究に理想が広がる時代。魂の旅と真実の探求が活発になります。",
                    "山羊座": "社会・権威・現実への理想と幻想が混ざる時代。夢を現実に落とし込む力が問われます。",
                    "水瓶座": "テクノロジーと精神性が融合する時代。未来への夢とビジョンが社会を動かします。",
                    "魚座": "感性・癒し・スピリチュアルが最大に高まる時代。境界を超えた共感と愛が広がります。",
                },
                "冥王星": {
                    "牡羊座": "個人の力と自由が根底から変革される時代。新しい人間のあり方が問われています。",
                    "牡牛座": "お金・経済・地球環境が根底から変革される時代。価値観の大転換が起きています。",
                    "双子座": "情報・言語・AIが根底から変革される時代。コミュニケーションの本質が変わります。",
                    "蟹座": "家族・国家・感情の在り方が根底から変革される時代です。",
                    "獅子座": "権力・エンターテインメント・自己表現が根底から変革される時代です。",
                    "乙女座": "仕事・医療・テクノロジーが根底から変革される時代。細部の力が社会を変えます。",
                    "天秤座": "人間関係・法律・パートナーシップが根底から変革される時代です。",
                    "蠍座": "金融・変容・潜在意識が根底から変革される最も強力な時代。深い再生が起きます。",
                    "射手座": "宗教・思想・高等教育が根底から変革される時代。真実の探求が加速します。",
                    "山羊座": "社会構造・権力・政治が根底から変革される時代。古い仕組みが崩れ新しい秩序が生まれます。",
                    "水瓶座": "テクノロジー・民主主義・コミュニティが根底から変革される時代です。",
                    "魚座": "精神性・芸術・見えない世界が根底から変革される時代。魂の進化が加速します。",
                },
            }

            for p in ["木星", "土星", "天王星", "海王星", "冥王星"]:
                if p in transit_longs:
                    sign, d = split_sign_degree(transit_longs[p])
                    st.markdown(f"**{p}**：{sign} {d:.1f}°")
                    p_msgs = outer_messages.get(p, {})
                    p_msg = p_msgs.get(sign, "")
                    if p_msg:
                        st.markdown(f"<div class='luna-message'>{p_msg}</div>", unsafe_allow_html=True)

            # ===== ⑦PDF出力 =====
            st.markdown("---")
            st.markdown("### 📄 鑑定書PDF")

            from utils.pdf_report import create_transit_pdf

            # チャート画像（2重円）
            chart_buf = io.BytesIO()
            fig2 = plot_horoscope(natal_longs, houses, transit_longs)
            fig2.savefig(chart_buf, format="png", dpi=150, bbox_inches="tight")
            chart_buf.seek(0)

            # アスペクトにメッセージを付与
            aspects_with_msg = []
            for a in aspects:
                msg = get_transit_aspect_message(a["transit"], a["natal"], a["type"])
                aspects_with_msg.append({**a, "message": msg})

            # 外惑星データ
            outer_list = []
            for p in ["木星", "土星", "天王星", "海王星", "冥王星"]:
                if p in transit_longs:
                    sign, d = split_sign_degree(transit_longs[p])
                    p_msg = outer_messages.get(p, {}).get(sign, "")
                    outer_list.append({"name": p, "sign": sign, "deg": f"{d:.1f}°", "message": p_msg})

            # natal_data（グランドトライン・グランドクロスも含める）
            natal_data_pdf = {
                "name": user_info.get("name", ""),
                "birthday": f"{birthday.year}年{birthday.month}月{birthday.day}日",
                "birth_time": f"{int(birth_hour):02d}:{int(birth_minute):02d}",
                "time_unknown": user_info.get("time_unknown", False),
                "grand_trines": gt_transit,
                "grand_crosses": gc_transit,
            }

            # transit_data
            flow = flow_messages.get(t_sun_sign, {})
            transit_data_pdf = {
                "transit_date": str(transit_date),
                "sun_sign": t_sun_sign,
                "sun_deg": f"{t_sun_deg:.1f}°",
                "moon_sign": t_moon_sign,
                "moon_deg": f"{t_moon_deg:.1f}°",
                "flow_title": flow.get("title", ""),
                "flow_body": flow.get("body", ""),
            }

            try:
                pdf_buf = create_transit_pdf(
                    natal_data_pdf, transit_data_pdf,
                    aspects_with_msg, outer_list, chart_buf
                )
                st.download_button(
                    label="📄 トランジット鑑定書をダウンロード",
                    data=pdf_buf,
                    file_name=f"luna_transit_{user_info.get('name', '')}_{transit_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_transit_pdf"
                )
            except Exception as e:
                st.error(f"PDF生成エラー: {e}")
                import traceback
                st.code(traceback.format_exc())
