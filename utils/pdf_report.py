from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether, PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os

# -----------------------------
# フォント登録
# -----------------------------
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_PATHS = [
    os.path.join(_BASE, 'fonts', 'gothic.ttc'),
    '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
    '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
]
for _path in _FONT_PATHS:
    if os.path.exists(_path):
        pdfmetrics.registerFont(TTFont('JP', _path))
        pdfmetrics.registerFont(TTFont('JPB', _path))
        break

# -----------------------------
# 色
# -----------------------------
PURPLE_DARK   = colors.HexColor("#4c1d95")
PURPLE_MID    = colors.HexColor("#7c3aed")
PURPLE_LIGHT  = colors.HexColor("#f5f3ff")
PURPLE_BORDER = colors.HexColor("#a78bfa")
TEXT_DARK     = colors.HexColor("#1f1437")
TEXT_GRAY     = colors.HexColor("#6b7280")

# -----------------------------
# スタイル
# -----------------------------
def S(name, size=10, color=TEXT_DARK, bold=False, align='LEFT', sb=6, sa=6):
    return ParagraphStyle(
        name,
        fontName='JPB' if bold else 'JP',
        fontSize=size,
        textColor=color,
        alignment={'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}.get(align, 0),
        spaceBefore=sb,
        spaceAfter=sa,
        leading=size * 1.8,
    )

STYLE_H1   = S('h1', 13, PURPLE_DARK, True, 'LEFT', sb=10, sa=6)
STYLE_H2   = S('h2', 11, PURPLE_MID,  True, 'LEFT', sb=8,  sa=4)
STYLE_H3   = S('h3', 10, PURPLE_MID,  True, 'LEFT', sb=6,  sa=2)
STYLE_BODY = S('body', 9, TEXT_DARK,  False, 'LEFT', sb=0,  sa=3)
STYLE_NOTE = S('note', 8, TEXT_GRAY,  False, 'LEFT', sb=2,  sa=4)

# ============================================================
# ★ create_reading_pdf（完全版）
# ============================================================
def create_reading_pdf(user_data, chart_image_bytes=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    # --------------------------------------------------------
    # ★ ここで section を定義（絶対に最初）
    # --------------------------------------------------------
    def section(title):
        # 前のカードとの間にしっかり距離を取る
        #story.append(Spacer(1, 40))  # ← ここが最重要（上の余白）

        story.append(HRFlowable(
            width="100%",
            thickness=1,
            color=PURPLE_BORDER,
            spaceBefore=6,
            spaceAfter=6
        ))

        story.append(Paragraph(f"◆ {title}", STYLE_H1))

        story.append(Spacer(1, 12))  # 見出しの下の余白


    # --------------------------------------------------------
    # ★ 惑星カード（ここで定義）
    # --------------------------------------------------------
    time_unknown = user_data.get("time_unknown", False)

    def planet_row(symbol, label, sign, deg, house, msg, house_msg=""):
        if not sign:
            return

        content = []
        # ハウス表示：time_unknownのとき非表示
        header = f"{symbol} {label}　{sign} {deg}"
        if house and not time_unknown:
            header += f"　{house}ハウス"
        content.append(Paragraph(
            header,
            S('p', 11, PURPLE_MID, True, sb=6, sa=10)
        ))

        if msg:
            for line in msg.split("\n"):
                line = line.strip()
                if not line:
                    content.append(Spacer(1, 5))
                elif line.startswith("【"):
                    content.append(Paragraph(line, STYLE_H3))
                else:
                    content.append(Paragraph(line, STYLE_BODY))

        # ハウスメッセージ：time_unknownのとき非表示
        if house_msg and not time_unknown:
            content.append(Paragraph(f"【ハウス】{house_msg}", STYLE_NOTE))

        # 各行を別セルにしてページまたぎ対応
        rows = [[item] for item in content]
        card = Table(rows, colWidths=[165*mm])
        card_style = [
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('LINEBEFORE', (0,0), (0,-1), 0.5, PURPLE_MID),
            ('LINEAFTER', (0,0), (0,-1), 0.5, PURPLE_MID),
            ('LINEABOVE', (0,0), (-1,0), 0.5, PURPLE_MID),
            ('LINEBELOW', (0,-1), (-1,-1), 0.5, PURPLE_MID),
            ('LEFTPADDING', (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
            ('TOPPADDING', (0,0), (0,0), 12),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 12),
            ('TOPPADDING', (0,1), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-2), 2),
        ]
        card.setStyle(TableStyle(card_style))
        card.repeatRows = 0

        story.append(card)
        story.append(Spacer(1, 20))

    # --------------------------------------------------------
    # ★ タイトル
    # --------------------------------------------------------
    story.append(Paragraph("Luna 占星術", S('t1', 20, PURPLE_DARK, True, 'CENTER')))
    story.append(Paragraph("ホロスコープ鑑定書", S('t2', 14, PURPLE_MID, True, 'CENTER')))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=8))

    # --------------------------------------------------------
    # ★ 基本情報
    # --------------------------------------------------------
    info = [
        [
            Paragraph("お名前", S('h', 10, PURPLE_DARK, True)),
            Paragraph(user_data.get("name", ""), S('v')),
            Paragraph("鑑定日", S('h', 10, PURPLE_DARK, True)),
            Paragraph(user_data.get("reading_date", ""), S('v')),
        ],
        [
            Paragraph("生年月日", S('h', 10, PURPLE_DARK, True)),
            Paragraph(user_data.get("birthday", ""), S('v')),
            Paragraph("出生時刻", S('h', 10, PURPLE_DARK, True)),
            Paragraph(
                "不明（正午で計算）" if user_data.get("time_unknown") else user_data.get("birth_time", ""),
                S('v', color=TEXT_GRAY) if user_data.get("time_unknown") else S('v')
            ),
        ],
    ]
    t = Table(info, colWidths=[28 * mm, 62 * mm, 25 * mm, 45 * mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'JP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, -1), PURPLE_LIGHT),
        ('BACKGROUND', (2, 0), (2, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------
    # ★ 総合メッセージ
    # --------------------------------------------------------
    overall_first = user_data.get("overall_message", "")
    astrologer_top = user_data.get("astrologer_message", "")

    if overall_first or astrologer_top:
        story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=4))
        story.append(Paragraph("◆ あなたへの総合メッセージ", STYLE_H1))
        story.append(Spacer(1, 4))

    # ① 自動生成メッセージ
    if overall_first:
        story.append(Paragraph("【星が示すあなたのストーリー】", STYLE_H2))
        for line in overall_first.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 3))
            elif line.startswith("【"):
                story.append(Paragraph(line, STYLE_H3))
            else:
                story.append(Paragraph(line, STYLE_BODY))
        story.append(Spacer(1, 8))

    # ② 占い師からのメッセージ
    if astrologer_top and astrologer_top.strip():
        story.append(HRFlowable(width="100%", thickness=0.5, color=PURPLE_BORDER, spaceBefore=4, spaceAfter=4))
        story.append(Paragraph("【占い師からのひとこと】", STYLE_H2))
        for line in astrologer_top.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
            else:
                story.append(Paragraph(line, STYLE_BODY))
        story.append(Spacer(1, 8))

    # --------------------------------------------------------
    # ★ ホロスコープ画像
    # --------------------------------------------------------
    if chart_image_bytes:
        img = Image(chart_image_bytes, width=120 * mm, height=120 * mm)
        img.hAlign = 'CENTER'
        chart_title = "◆ 円形ホロスコープ（ソーラーチャート）" if user_data.get("time_unknown") else "◆ 円形ホロスコープ"
        chart_block = [
            Paragraph(chart_title, STYLE_H1),
            Spacer(1, 4),
            img,
            Spacer(1, 6),
        ]
        if user_data.get("time_unknown"):
            chart_block.insert(1, Paragraph(
                "※ 出生時刻不明のため、太陽星座を第1ハウスとするソーラーチャートで表示しています。",
                STYLE_NOTE,
            ))
        story.append(KeepTogether(chart_block))

        story.append(PageBreak())

    # --------------------------------------------------------
    # ★ ASC（第一印象）：出生時刻不明の場合は非表示
    # --------------------------------------------------------
    if not user_data.get("time_unknown"):
        section("第一印象（ASC）")

        asc_title = f"☺ アセンダント　{user_data.get('asc_sign', '')} {user_data.get('asc_deg', '')}"
        asc_msg = user_data.get("asc_message", "")

        asc_content = []
        asc_content.append(Paragraph(
            asc_title,
            S('asc_header', 11, PURPLE_MID, True, sb=6, sa=6)
        ))

        if asc_msg:
            for line in asc_msg.split("\n"):
                line = line.strip()
                if not line:
                    asc_content.append(Spacer(1, 4))
                elif line.startswith("【"):
                    asc_content.append(Paragraph(line, STYLE_H3))
                else:
                    asc_content.append(Paragraph(line, STYLE_BODY))

        asc_card = Table([[asc_content]], colWidths=[165*mm])
        asc_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))

        story.append(asc_card)
        story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 主要天体
    # --------------------------------------------------------
    section("主要天体")

    for sym, lbl, ks, kd, kh, km, khm in [
        ("☀", "太陽（本質）", "sun_sign", "sun_deg", "sun_house", "sun_message", "sun_house_message"),
        ("☽", "月（感情）", "moon_sign", "moon_deg", "moon_house", "moon_message", "moon_house_message"),
        ("☿", "水星（思考）", "mercury_sign", "mercury_deg", "mercury_house", "mercury_message", "mercury_house_message"),
        ("♀", "金星（愛・好み）", "venus_sign", "venus_deg", "venus_house", "venus_message", "venus_house_message"),
        ("♂", "火星（行動）", "mars_sign", "mars_deg", "mars_house", "mars_message", "mars_house_message"),
    ]:
        planet_row(
            sym, lbl,
            user_data.get(ks, ""),
            user_data.get(kd, ""),
            user_data.get(kh, ""),
            user_data.get(km, ""),
            user_data.get(khm, ""),
        )

    # --------------------------------------------------------
    # ★ 外惑星
    # --------------------------------------------------------
    section("外惑星")

    for sym, lbl, ks, kd, kh, km, khm in [
        ("♃", "木星（発展）", "jupiter_sign", "jupiter_deg", "jupiter_house", "jupiter_message", "jupiter_house_message"),
        ("♄", "土星（課題）", "saturn_sign", "saturn_deg", "saturn_house", "saturn_message", "saturn_house_message"),
        ("♅", "天王星（改革）", "uranus_sign", "uranus_deg", "uranus_house", "uranus_message", "uranus_house_message"),
        ("♆", "海王星（直感）", "neptune_sign", "neptune_deg", "neptune_house", "neptune_message", "neptune_house_message"),
        ("♇", "冥王星（変容）", "pluto_sign", "pluto_deg", "pluto_house", "pluto_message", "pluto_house_message"),
    ]:
        planet_row(
            sym, lbl,
            user_data.get(ks, ""),
            user_data.get(kd, ""),
            user_data.get(kh, ""),
            user_data.get(km, ""),
            user_data.get(khm, ""),
        )

    story.append(PageBreak())    

    # --------------------------------------------------------
    # ★ アスペクト
    # --------------------------------------------------------
    aspects = user_data.get("aspects", [])
    if aspects:
        section("アスペクト（天体の関係性）")

        for a in aspects:
            story.append(Paragraph(
                f"◇ {a.get('p1', '')} × {a.get('p2', '')}：{a.get('type', '')}",
                STYLE_H2,
            ))
            story.append(Paragraph(a.get("message", ""), STYLE_BODY))
            story.append(Spacer(1, 6))

    story.append(PageBreak())  

    # --------------------------------------------------------
    # ★ 数秘術
    # --------------------------------------------------------
    section("数秘術")

    def _num_cell(label, value):
        return [
            Paragraph(label, S('nl', 9, PURPLE_DARK, True, 'CENTER', sb=2, sa=2)),
            Paragraph(str(value), S('nv', 16, PURPLE_MID, True, 'CENTER', sb=2, sa=2)),
        ]

    nd = [[
        _num_cell("ライフパス", user_data.get("life_path", "")),
        _num_cell("バースデー", user_data.get("birthday_num", "")),
        _num_cell("ルーラー",   user_data.get("ruler_num", "")),
    ]]

    nt = Table(nd, colWidths=[40*mm, 40*mm, 40*mm])
    nt.setStyle(TableStyle([
        ('FONTNAME',      (0,0), (-1,-1), 'JP'),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND',    (0,0), (-1,-1), PURPLE_LIGHT),
        ('BOX',           (0,0), (-1,-1), 1.5, PURPLE_MID),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, PURPLE_BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    nt.hAlign = 'CENTER'
    story.append(nt)
    story.append(Spacer(1, 20))

    # ライフパス
    lp_num = user_data.get("life_path", "")
    lp_msg = user_data.get("life_path_message", "")

    story.append(Paragraph(
        f"◇ ライフパスナンバー {lp_num}　～人生のテーマ・使命～",
        STYLE_H2,
    ))

    if lp_msg:
        for line in lp_msg.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
            elif line.startswith("【"):
                story.append(Paragraph(line, STYLE_H3))
            else:
                story.append(Paragraph(line, STYLE_BODY))

    story.append(Spacer(1, 14))

    # バースデーナンバー
    bd_num = user_data.get("birthday_num", "")
    bd_msg = user_data.get("birthday_message", "")
    if bd_msg:
        story.append(Paragraph(
            f"◇ バースデーナンバー {bd_num}　～生まれ持った才能～",
            STYLE_H2,
        ))
        for line in bd_msg.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
            elif line.startswith("【"):
                story.append(Paragraph(line, STYLE_H3))
            else:
                story.append(Paragraph(line, STYLE_BODY))
        story.append(Spacer(1, 14))

    # ルーラーナンバー
    rl_num = user_data.get("ruler_num", "")
    rl_msg = user_data.get("ruler_message", "")
    if rl_msg:
        story.append(Paragraph(
            f"◇ ルーラーナンバー {rl_num}　～生まれた年の使命～",
            STYLE_H2,
        ))
        for line in rl_msg.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
            elif line.startswith("【"):
                story.append(Paragraph(line, STYLE_H3))
            else:
                story.append(Paragraph(line, STYLE_BODY))

    story.append(PageBreak())


    # --------------------------------------------------------
    # ★ タロットメッセージ
    # --------------------------------------------------------
    tarot_data = user_data.get("tarot_message", {})
    if tarot_data and isinstance(tarot_data, dict):
        section("今日のあなたへのメッセージ 🔮")

        from PIL import Image as PILImage
        import io as _io

        card_img_path = tarot_data.get("image", "")
        card_name = tarot_data.get("name", "")
        card_position = tarot_data.get("position", "")
        card_msg = tarot_data.get("message", "")
        is_reversed = tarot_data.get("is_reversed", False)

        # カード画像（PDF用にリサイズして軽量化）
        if card_img_path and os.path.exists(card_img_path):
            try:
                pil_img = PILImage.open(card_img_path).convert("RGB")
                if is_reversed:
                    pil_img = pil_img.rotate(180)
                # PDF埋め込み用に最大300×500pxにリサイズ
                pil_img.thumbnail((300, 500), PILImage.LANCZOS)
                img_buf = _io.BytesIO()
                pil_img.save(img_buf, format="JPEG", quality=75, optimize=True)
                img_buf.seek(0)
                card_image = Image(img_buf, width=40 * mm, height=65 * mm)
                card_image.hAlign = 'CENTER'
                story.append(card_image)
                story.append(Spacer(1, 6))
            except Exception:
                pass

        story.append(Paragraph(
            f"{card_name}（{card_position}）",
            S('tm', 12, PURPLE_MID, True, align='CENTER', sb=4, sa=4),
        ))

        if card_msg:
            for line in card_msg.split("\n"):
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 4))
                elif line.startswith("【"):
                    story.append(Paragraph(line, S('tmh', 10, PURPLE_MID, True, align='LEFT', sb=4, sa=2)))
                else:
                    story.append(Paragraph(line, S('tmm', 10, TEXT_DARK, align='LEFT', sb=0, sa=3)))

    # --------------------------------------------------------
    # ★ フッター
    # --------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER))
    story.append(Paragraph(
        "Luna 占星術　Luna-compass",
        S('ft', 8, TEXT_GRAY, align='CENTER', sb=4, sa=0),
    ))

    # --------------------------------------------------------
    # ★ PDF 出力
    # --------------------------------------------------------
    doc.build(story)
    buf.seek(0)
    return buf


# ============================================================
# トランジット鑑定書PDF生成
# ============================================================
def create_transit_pdf(natal_data, transit_data, aspects, outer_planets, chart_image_bytes=None):
    """
    natal_data: dict（name, birthday, birth_time, asc_sign など）
    transit_data: dict（transit_date, sun_sign, moon_sign, flow_title, flow_body）
    aspects: list of dict（transit, natal, type, orb）
    outer_planets: list of dict（name, sign, deg, message）
    chart_image_bytes: BytesIO（2重円チャート）
    """
    import io as _io

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    story = []

    name = natal_data.get("name", "")
    reading_date = transit_data.get("transit_date", "")

    # --------------------------------------------------------
    # ★ タイトル
    # --------------------------------------------------------
    story.append(Paragraph("Luna 占星術", S('t1', 20, PURPLE_DARK, True, 'CENTER')))
    story.append(Paragraph("トランジット鑑定書", S('t2', 13, PURPLE_MID, False, 'CENTER', sb=4, sa=10)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PURPLE_BORDER, spaceAfter=8))

    # --------------------------------------------------------
    # ★ 基本情報テーブル
    # --------------------------------------------------------
    info = [
        [
            Paragraph("お名前", S('h', 10, PURPLE_DARK, True)),
            Paragraph(name, S('v')),
            Paragraph("鑑定日", S('h', 10, PURPLE_DARK, True)),
            Paragraph(reading_date, S('v')),
        ],
        [
            Paragraph("生年月日", S('h', 10, PURPLE_DARK, True)),
            Paragraph(natal_data.get("birthday", ""), S('v')),
            Paragraph("出生時刻", S('h', 10, PURPLE_DARK, True)),
            Paragraph(
                "不明（正午で計算）" if natal_data.get("time_unknown") else natal_data.get("birth_time", ""),
                S('v', color=TEXT_GRAY) if natal_data.get("time_unknown") else S('v')
            ),
        ],
    ]
    t = Table(info, colWidths=[28 * mm, 62 * mm, 25 * mm, 45 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), PURPLE_LIGHT),
        ('BACKGROUND', (2, 0), (2, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, PURPLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ★ チャート（2重円）
    # --------------------------------------------------------
    if chart_image_bytes:
        img = Image(chart_image_bytes, width=120 * mm, height=120 * mm)
        img.hAlign = 'CENTER'
        story.append(Paragraph("◆ ホロスコープ（ネイタル＋トランジット）", STYLE_H1))
        story.append(Spacer(1, 4))
        story.append(img)
        story.append(Spacer(1, 8))
        story.append(PageBreak())

    # --------------------------------------------------------
    # ★ section関数をローカル定義
    # --------------------------------------------------------
    def section(title):
        story.append(HRFlowable(
            width="100%", thickness=1, color=PURPLE_BORDER,
            spaceBefore=6, spaceAfter=6
        ))
        story.append(Paragraph(f"◆ {title}", STYLE_H1))
        story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ★ 今日の流れ
    # --------------------------------------------------------
    section("今日の流れ")
    flow_title = transit_data.get("flow_title", "")
    flow_body  = transit_data.get("flow_body", "")
    t_sun  = transit_data.get("sun_sign", "")
    t_moon = transit_data.get("moon_sign", "")
    t_sun_deg  = transit_data.get("sun_deg", "")
    t_moon_deg = transit_data.get("moon_deg", "")

    story.append(Paragraph(f"☀ トランジット太陽：{t_sun} {t_sun_deg}", S('p', 10, PURPLE_MID, True, sb=2, sa=4)))
    story.append(Paragraph(f"☽ トランジット月：{t_moon} {t_moon_deg}", S('p', 10, PURPLE_MID, True, sb=2, sa=8)))

    if flow_title:
        story.append(Paragraph(flow_title, STYLE_H3))
    if flow_body:
        for line in flow_body.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, STYLE_BODY))
    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # ★ トランジットアスペクト
    # --------------------------------------------------------
    section("トランジット × ネイタル アスペクト")
    story.append(Paragraph("今この星があなたに与えている影響を示します。", STYLE_NOTE))
    story.append(Spacer(1, 6))

    asp_icons = {
        "コンジャンクション": "●",
        "トライン": "△",
        "スクエア": "□",
        "セクスタイル": "✦",
        "オポジション": "○",
    }

    if aspects:
        for a in aspects:
            icon = asp_icons.get(a["type"], "◇")
            header = f"{icon} トランジット{a['transit']} × ネイタル{a['natal']}：{a['type']}"
            msg = a.get("message", "")
            rows = [[Paragraph(header, S('p', 10, PURPLE_MID, True, sb=4, sa=4))]]
            if msg:
                for line in msg.split("\n"):
                    line = line.strip()
                    if not line:
                        rows.append([Spacer(1, 3)])
                    else:
                        rows.append([Paragraph(line, STYLE_BODY)])
            card = Table(rows, colWidths=[165 * mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), PURPLE_LIGHT),
                ('LINEBEFORE', (0, 0), (0, -1), 0.5, PURPLE_MID),
                ('LINEAFTER', (0, 0), (0, -1), 0.5, PURPLE_MID),
                ('LINEABOVE', (0, 0), (-1, 0), 0.5, PURPLE_MID),
                ('LINEBELOW', (0, -1), (-1, -1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0, 0), (-1, -1), 14),
                ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                ('TOPPADDING', (0, 0), (0, 0), 10),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -2), 2),
            ]))
            story.append(card)
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("現在、主要なアスペクトはありません。", STYLE_BODY))

    story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 外惑星の動き
    # --------------------------------------------------------
    section("外惑星の動き")
    story.append(Paragraph("ゆっくり動く惑星は長期的な流れを示します。", STYLE_NOTE))
    story.append(Spacer(1, 6))

    for op in outer_planets:
        p_name = op.get("name", "")
        p_sign = op.get("sign", "")
        p_deg  = op.get("deg", "")
        p_msg  = op.get("message", "")

        rows = [[Paragraph(f"♃ {p_name}：{p_sign} {p_deg}", S('p', 10, PURPLE_MID, True, sb=4, sa=4))]]
        if p_msg:
            for line in p_msg.split("\n"):
                line = line.strip()
                if not line:
                    rows.append([Spacer(1, 3)])
                else:
                    rows.append([Paragraph(line, STYLE_BODY)])
        card = Table(rows, colWidths=[165 * mm])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PURPLE_LIGHT),
            ('LINEBEFORE', (0, 0), (0, -1), 0.5, PURPLE_MID),
            ('LINEAFTER', (0, 0), (0, -1), 0.5, PURPLE_MID),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, PURPLE_MID),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, PURPLE_MID),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -2), 2),
        ]))
        story.append(card)
        story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # ★ フッター
    # --------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER))
    story.append(Paragraph(
        "Luna 占星術　Luna-compass",
        S('ft', 8, TEXT_GRAY, align='CENTER', sb=4, sa=0),
    ))

    doc.build(story)
    buf.seek(0)
    return buf


# ============================================================
# 相性鑑定書PDF生成
# ============================================================
def create_compatibility_pdf(
    name1, birthday1, sun_sign1, moon_sign1, venus_sign1, mars_sign1,
    name2, birthday2, sun_sign2, moon_sign2, venus_sign2, mars_sign2,
    overall, compat_note, chart_image_bytes=None
):
    import io as _io

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    story = []

    def section(title):
        story.append(HRFlowable(
            width="100%", thickness=1, color=PURPLE_BORDER,
            spaceBefore=6, spaceAfter=6
        ))
        story.append(Paragraph(f"◆ {title}", STYLE_H1))
        story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ★ タイトル
    # --------------------------------------------------------
    story.append(Paragraph("Luna 占星術", S('t1', 20, PURPLE_DARK, True, 'CENTER')))
    story.append(Paragraph("相性鑑定書", S('t2', 13, PURPLE_MID, False, 'CENTER', sb=4, sa=10)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PURPLE_BORDER, spaceAfter=8))

    # --------------------------------------------------------
    # ★ 基本情報テーブル
    # --------------------------------------------------------
    info = [
        [
            Paragraph("お相手1", S('h', 10, PURPLE_DARK, True)),
            Paragraph(name1, S('v')),
            Paragraph("お相手2", S('h', 10, PURPLE_DARK, True)),
            Paragraph(name2, S('v')),
        ],
        [
            Paragraph("生年月日", S('h', 10, PURPLE_DARK, True)),
            Paragraph(f"{birthday1.year}年{birthday1.month}月{birthday1.day}日", S('v')),
            Paragraph("生年月日", S('h', 10, PURPLE_DARK, True)),
            Paragraph(f"{birthday2.year}年{birthday2.month}月{birthday2.day}日", S('v')),
        ],
    ]
    t = Table(info, colWidths=[25 * mm, 65 * mm, 25 * mm, 45 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), PURPLE_LIGHT),
        ('BACKGROUND', (2, 0), (2, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, PURPLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ★ チャート
    # --------------------------------------------------------
    if chart_image_bytes:
        img = Image(chart_image_bytes, width=120 * mm, height=120 * mm)
        img.hAlign = 'CENTER'
        story.append(Paragraph("◆ ホロスコープ（2人の重ね表示）", STYLE_H1))
        story.append(Spacer(1, 4))
        story.append(img)
        story.append(Spacer(1, 8))
        story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 天体情報
    # --------------------------------------------------------
    section("2人の天体")
    planet_rows = [
        [
            Paragraph("天体", S('h', 10, PURPLE_DARK, True)),
            Paragraph(name1, S('h', 10, PURPLE_DARK, True)),
            Paragraph(name2, S('h', 10, PURPLE_DARK, True)),
        ],
        [Paragraph("☀ 太陽", STYLE_BODY), Paragraph(sun_sign1, STYLE_BODY), Paragraph(sun_sign2, STYLE_BODY)],
        [Paragraph("☽ 月", STYLE_BODY), Paragraph(moon_sign1, STYLE_BODY), Paragraph(moon_sign2, STYLE_BODY)],
        [Paragraph("♀ 金星", STYLE_BODY), Paragraph(venus_sign1, STYLE_BODY), Paragraph(venus_sign2, STYLE_BODY)],
        [Paragraph("♂ 火星", STYLE_BODY), Paragraph(mars_sign1, STYLE_BODY), Paragraph(mars_sign2, STYLE_BODY)],
    ]
    pt = Table(planet_rows, colWidths=[40 * mm, 62 * mm, 62 * mm])
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, PURPLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(pt)
    story.append(Spacer(1, 16))

    # --------------------------------------------------------
    # ★ 相性メッセージ
    # --------------------------------------------------------
    section("相性鑑定")
    for line in compat_note.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
        elif line.startswith("【"):
            story.append(Paragraph(line, STYLE_H3))
        else:
            story.append(Paragraph(line, STYLE_BODY))
    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ★ 総合メッセージ
    # --------------------------------------------------------
    section("総合相性メッセージ")
    story.append(Paragraph(overall, STYLE_BODY))

    # --------------------------------------------------------
    # ★ フッター
    # --------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER))
    story.append(Paragraph(
        "Luna 占星術　Luna-compass",
        S('ft', 8, TEXT_GRAY, align='CENTER', sb=4, sa=0),
    ))

    doc.build(story)
    buf.seek(0)
    return buf
