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

# 通常フォント候補
_FONT_PATHS = [
    os.path.join(_BASE, 'fonts', 'NotoSansJP-Regular.ttf'),
    os.path.join(_BASE, 'fonts', 'gothic.ttc'),
    os.path.join(_BASE, 'fonts', 'NotoSansJP-VariableFont_wght.ttf'),
    '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
    '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
]
# 太字フォント候補（Bold専用ファイルがあれば優先）
_FONT_BOLD_PATHS = [
    os.path.join(_BASE, 'fonts', 'NotoSansJP-Bold.ttf'),
    os.path.join(_BASE, 'fonts', 'NotoSansJP_Bold.ttf'),
    os.path.join(_BASE, 'fonts', 'gothic-bold.ttc'),
    '/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf',
]

_registered_font_path = None
for _path in _FONT_PATHS:
    if os.path.exists(_path):
        pdfmetrics.registerFont(TTFont('JP', _path))
        _registered_font_path = _path
        break

# Bold用フォント：専用ファイルがあれば使い、なければ通常フォントで代用
_bold_registered = False
for _bpath in _FONT_BOLD_PATHS:
    if os.path.exists(_bpath):
        pdfmetrics.registerFont(TTFont('JPB', _bpath))
        _bold_registered = True
        break
if not _bold_registered and _registered_font_path:
    # 通常フォントを JPB としても登録（同名衝突を避けるため alias を使用）
    from reportlab.pdfbase.ttfonts import TTFont as _TTFont
    try:
        pdfmetrics.registerFont(_TTFont('JPB', _registered_font_path))
    except Exception:
        pass

# Noto Sans Symbols（占星術記号用）
_SYMBOL_FONT_PATHS = [
    os.path.join(_BASE, 'fonts', 'NotoSansSymbols-VariableFont_wght.ttf'),
    os.path.join(_BASE, 'fonts', 'NotoSansSymbols-Regular.ttf'),
]
_symbol_font_registered = False
for _path in _SYMBOL_FONT_PATHS:
    if os.path.exists(_path):
        pdfmetrics.registerFont(TTFont('Symbols', _path))
        _symbol_font_registered = True
        break

# Noto Sans Symbols 2（☉太陽など一部記号用）
_SYMBOL2_FONT_PATH = os.path.join(_BASE, 'fonts', 'NotoSansSymbols2-Regular.ttf')
_symbol2_font_registered = False
if os.path.exists(_SYMBOL2_FONT_PATH):
    pdfmetrics.registerFont(TTFont('Symbols2', _SYMBOL2_FONT_PATH))
    _symbol2_font_registered = True

# -----------------------------
# 色
# -----------------------------
PURPLE_DARK   = colors.HexColor("#7c3aed")
PURPLE_MID    = colors.HexColor("#7c3aed")
PURPLE_LIGHT  = colors.HexColor("#f3f0ff")
PURPLE_BORDER = colors.HexColor("#c4b5fd")
PURPLE_ACCENT = colors.HexColor("#d946ef")
GOLD          = colors.HexColor("#d97706")
TEXT_DARK     = colors.HexColor("#1f1437")
TEXT_GRAY     = colors.HexColor("#6b7280")

# -----------------------------
# スタイル
# -----------------------------
def S(name, size=10, color=TEXT_DARK, bold=False, align='LEFT', sb=6, sa=6):
    # パラメータからユニークなスタイル名を生成してスタイル衝突を防ぐ
    color_hex = color.hexval() if hasattr(color, 'hexval') else str(color)
    unique_name = f"{name}_{size}_{color_hex}_{bold}_{align}_{sb}_{sa}"
    return ParagraphStyle(
        unique_name,
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
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    # --------------------------------------------------------
    # ★ ここで section を定義（絶対に最初）
    # --------------------------------------------------------
    def section(title):
        story.append(Spacer(1, 8))
        # グラデーション風セクションヘッダー
        sec_rows = [[Paragraph(f"◆ {title}", S('sec', 13, colors.white, True, sb=0, sa=0))]]
        sec_table = Table(sec_rows, colWidths=[165*mm])
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_DARK),
            ('LEFTPADDING', (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 10))


    # --------------------------------------------------------
    # ★ 惑星カード（ここで定義）
    # --------------------------------------------------------
    time_unknown = user_data.get("time_unknown", False)

    def planet_row(symbol, label, sign, deg, house, msg, house_msg=""):
        if not sign:
            return

        content = []
        # ハウス表示：time_unknownのとき非表示
        # 惑星記号にSymbolsフォントを適用
        _sym_f = 'Symbols2' if _symbol2_font_registered and symbol == "☉" else ('Symbols' if _symbol_font_registered else 'JP')
        symbol_html = f'<font name="{_sym_f}">{symbol}</font>'
        header = f"{symbol_html} {label}　{sign} {deg}"
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
    # --------------------------------------------------------
    # ★ 1ページ目：タイトル＋基本情報＋ホロスコープ（視覚的インパクト重視）
    # --------------------------------------------------------

    # タイトル（コンパクト）
    story.append(Paragraph("Luna 占星術", S('t1', 16, PURPLE_DARK, True, 'CENTER', sb=4, sa=2)))
    story.append(Paragraph("ホロスコープ鑑定書", S('t2', 11, PURPLE_MID, True, 'CENTER', sb=2, sa=4)))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=6))

    # 基本情報（コンパクト）
    info = [
        [
            Paragraph("お名前", S('h', 9, PURPLE_DARK, True)),
            Paragraph(user_data.get("name", ""), S('v', 9)),
            Paragraph("鑑定日", S('h', 9, PURPLE_DARK, True)),
            Paragraph(user_data.get("reading_date", ""), S('v', 9)),
        ],
        [
            Paragraph("生年月日", S('h', 9, PURPLE_DARK, True)),
            Paragraph(user_data.get("birthday", ""), S('v', 9)),
            Paragraph("出生時刻", S('h', 9, PURPLE_DARK, True)),
            Paragraph(
                "不明（正午で計算）" if user_data.get("time_unknown") else user_data.get("birth_time", ""),
                S('v', 9, color=TEXT_GRAY) if user_data.get("time_unknown") else S('v', 9)
            ),
        ],
    ]
    t = Table(info, colWidths=[28 * mm, 62 * mm, 25 * mm, 45 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), PURPLE_LIGHT),
        ('BACKGROUND', (2, 0), (2, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # ホロスコープ画像（大きく・1ページ目メイン）
    if chart_image_bytes:
        img = Image(chart_image_bytes, width=155 * mm, height=155 * mm)
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

        # 星座・惑星記号の見方
        _sym = 'Symbols' if _symbol_font_registered else 'JP'
        _sym2 = 'Symbols2' if _symbol2_font_registered else _sym
        def _s(sym, jp):
            font = _sym2 if sym == "☉" else _sym
            return f'<font name="{font}">{sym}</font>{jp}'
        sign_row1 = "　".join([
            _s("♈","牡羊座"), _s("♉","牡牛座"), _s("♊","双子座"), _s("♋","蟹座"),
            _s("♌","獅子座"), _s("♍","乙女座"),
        ])
        sign_row2 = "　".join([
            _s("♎","天秤座"), _s("♏","蠍座"), _s("♐","射手座"),
            _s("♑","山羊座"), _s("♒","水瓶座"), _s("♓","魚座"),
        ])
        sign_legend_rows = [
            [Paragraph("ホロスコープの記号の見方", S('sl', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(sign_row1, S('sl2', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(sign_row2, S('sl2b', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(
                "　".join([
                    _s("☉","太陽"), _s("☽","月"), _s("☿","水星"), _s("♀","金星"), _s("♂","火星"),
                    _s("♃","木星"), _s("♄","土星"), _s("♅","天王星"), _s("♆","海王星"), _s("♇","冥王星"),
                ]),
                S('sl3', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=4)
            )],
        ]
        sign_legend = Table(sign_legend_rows, colWidths=[165*mm])
        sign_legend.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(sign_legend)
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 2ページ目：読み方ガイド＋キーワード＋総合メッセージ＋占い師メッセージ
    # --------------------------------------------------------

    # 鑑定書の読み方ガイド（新テキスト）
    guide_rows = [
        [Paragraph("この鑑定書について", S('gt', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
        [Paragraph(
            "本鑑定書は「占星術・数秘術・タロット」の3つの視点からお届けする総合鑑定書です。"
            "1ページ目のホロスコープはあなたの星の配置を示しています。"
            "次にキーワードと総合メッセージをご覧ください。"
            "また「占い師からのひとこと」には、鑑定師があなたのホロスコープを見て感じたメッセージを込めています。"
            "その後、各天体・アスペクト・数秘術と順にお読みいただくと、"
            "あなたの全体像がより深く理解できます。"
            "最後のタロットは「今このときのあなたへのメッセージ」としてお受け取りください。",
            S('gb', 9, TEXT_DARK, False, 'LEFT', sb=2, sa=4)
        )],
    ]
    guide_table = Table(guide_rows, colWidths=[165*mm])
    guide_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (0,0), 8),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
    ]))
    story.append(guide_table)
    story.append(Spacer(1, 8))

    # キーワードサマリー
    kw_asc     = user_data.get("kw_asc", "")
    kw_sun     = user_data.get("kw_sun", "")
    kw_moon    = user_data.get("kw_moon", "")
    kw_mercury = user_data.get("kw_mercury", "")
    kw_venus   = user_data.get("kw_venus", "")
    kw_mars    = user_data.get("kw_mars", "")
    name       = user_data.get("name", "あなた")

    if kw_sun or kw_moon:
        story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=4))
        story.append(Paragraph("◆ あなたのキーワード", STYLE_H1))
        story.append(Spacer(1, 6))

        kw_lines = []
        if kw_asc and not user_data.get("time_unknown"):
            kw_lines.append(f"第一印象　：{kw_asc}")
        if kw_sun:
            kw_lines.append(f"人生のテーマ：{kw_sun}")
        if kw_moon:
            kw_lines.append(f"心が求めるもの：{kw_moon}")
        if kw_mercury:
            kw_lines.append(f"思考スタイル：{kw_mercury}")
        if kw_venus:
            kw_lines.append(f"愛のスタイル：{kw_venus}")
        if kw_mars:
            kw_lines.append(f"行動スタイル：{kw_mars}")

        kw_rows = [[Paragraph(line, S('v', 10, PURPLE_DARK))] for line in kw_lines]
        kw_table = Table(kw_rows, colWidths=[165 * mm])
        kw_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PURPLE_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_MID),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(kw_table)
        story.append(Spacer(1, 12))

    # 総合メッセージ
    overall_first = user_data.get("overall_message", "")
    astrologer_top = user_data.get("astrologer_message", "")

    if overall_first or astrologer_top:
        story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=4))
        story.append(Paragraph("◆ あなたへの総合メッセージ", STYLE_H1))
        story.append(Spacer(1, 4))

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

    # 占い師からのメッセージ
    if astrologer_top and astrologer_top.strip():
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=0.5, color=PURPLE_BORDER, spaceBefore=4, spaceAfter=4))
        story.append(Paragraph("【占い師からのひとこと】", STYLE_H2))
        for line in astrologer_top.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
            else:
                story.append(Paragraph(line, STYLE_BODY))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # --------------------------------------------------------
    # ★ タロットメッセージ（「今知りたい答え」を早めに渡す）
    # --------------------------------------------------------
    tarot_data = user_data.get("tarot_message", {})
    if tarot_data and isinstance(tarot_data, dict):
        section("今日のあなたへのメッセージ")

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
                card_image = Image(img_buf, width=70 * mm, height=115 * mm)
                card_image.hAlign = 'CENTER'
                story.append(card_image)
                story.append(Spacer(1, 16))
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

        story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 3ページ目：ASC（第一印象）
    # --------------------------------------------------------
    if not user_data.get("time_unknown"):
        section("第一印象（ASC）")

        asc_title = f"ASC アセンダント　{user_data.get('asc_sign', '')} {user_data.get('asc_deg', '')}"
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
    # ★ 太陽・月（性格の核）
    # --------------------------------------------------------
    section("太陽・月")

    for sym, lbl, ks, kd, kh, km, khm in [
        ("☉", "太陽（本質）", "sun_sign", "sun_deg", "sun_house", "sun_message", "sun_house_message"),
        ("☽", "月（感情）", "moon_sign", "moon_deg", "moon_house", "moon_message", "moon_house_message"),
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
    # ★ 水星・金星・火星（考え方・恋愛・行動力）
    # --------------------------------------------------------
    section("水星・金星・火星")

    for sym, lbl, ks, kd, kh, km, khm in [
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

    story.append(PageBreak())

    # --------------------------------------------------------
    # ★ アスペクト（特別なパターンもここに含める）
    # --------------------------------------------------------
    aspects = user_data.get("aspects", [])
    grand_trines = user_data.get("grand_trines", [])
    grand_crosses = user_data.get("grand_crosses", [])

    if aspects or grand_trines or grand_crosses:
        section("アスペクト（天体の関係性）")

        # アスペクトの説明文＋凡例（一般の方向けの補足）
        aspect_intro_rows = [
            [Paragraph(
                "アスペクトとは、天体同士の関係性を表すものです。"
                "一つひとつの天体の意味だけでなく、天体同士がどのように影響し合うかを見ることで、"
                "あなたらしさや才能、課題をより深く読み解くことができます。",
                S('ai_b', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=8)
            )],
            [Paragraph("トライン：調和・才能", S('ai_l1', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=3))],
            [Paragraph("セクスタイル：協力・チャンス", S('ai_l2', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=3))],
            [Paragraph("スクエア：課題・成長", S('ai_l3', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=3))],
            [Paragraph("オポジション：バランスを学ぶ", S('ai_l4', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=3))],
            [Paragraph("コンジャンクション：強いエネルギー", S('ai_l5', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=0))],
        ]
        aspect_intro = Table(aspect_intro_rows, colWidths=[165 * mm])
        aspect_intro.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PURPLE_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ]))
        story.append(aspect_intro)
        story.append(Spacer(1, 10))

        for a in aspects:
            story.append(Paragraph(
                f"◇ {a.get('p1', '')} × {a.get('p2', '')}：{a.get('type', '')}",
                STYLE_H2,
            ))
            story.append(Paragraph(a.get("message", ""), STYLE_BODY))
            story.append(Spacer(1, 6))

        # --------------------------------------------------------
        # ★ グランドトライン・グランドクロス（アスペクトの一種として同セクション内に）
        # --------------------------------------------------------
        if grand_trines or grand_crosses:
            story.append(Spacer(1, 6))
            story.append(Paragraph("◆ 特別なパターン", STYLE_H1))
            story.append(Paragraph(
                "複数のアスペクトが組み合わさり、大きな図形を描く特別な配置です。",
                STYLE_NOTE
            ))
            story.append(Spacer(1, 6))

        for gt in grand_trines:
            elem = gt.get("element", "")
            planets_str = "・".join(gt.get("planets", []))
            signs_str = "・".join(gt.get("signs", []))
            elem_base = {
                "火": "情熱・行動力・創造性が大きく調和しています。自然なエネルギーの流れで、才能が開花しやすい配置です。",
                "地": "現実的な安定・忍耐・実行力が深く調和しています。着実に目標を実現する強い力を持っています。",
                "風": "知性・コミュニケーション・自由な発想が調和しています。アイデアが自然に広がる才能があります。",
                "水": "感情・共感・直感が深く調和しています。人の心を感じ取る繊細な感受性が大きな力になります。",
                "混合": "異なるエネルギーが大きく調和した、ユニークなグランドトラインです。",
            }.get(elem, "")
            elem_signs_note = {
                "火": "（牡羊座・獅子座・射手座のエレメント）",
                "地": "（牡牛座・乙女座・山羊座のエレメント）",
                "風": "（双子座・天秤座・水瓶座のエレメント）",
                "水": "（蟹座・蠍座・魚座のエレメント）",
            }.get(elem, "")
            elem_msg = f"{planets_str}が{elem}のエレメントで大きな三角形を形成しています。{elem_base}"
            rows = [
                [Paragraph(f"グランドトライン（{elem}のエレメント）{elem_signs_note}", S('gt', 11, PURPLE_MID, True, sb=4, sa=4))],
                [Paragraph(f"天体：{planets_str}", STYLE_BODY)],
                [Paragraph(f"星座：{signs_str}", STYLE_BODY)],
                [Spacer(1, 4)],
                [Paragraph(elem_msg, STYLE_BODY)],
            ]
            card = Table(rows, colWidths=[165*mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
                ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0,0), (-1,-1), 14),
                ('RIGHTPADDING', (0,0), (-1,-1), 14),
                ('TOPPADDING', (0,0), (0,0), 10),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ]))
            story.append(card)
            story.append(Spacer(1, 12))

        for gc in grand_crosses:
            mode = gc.get("mode", "")
            planets_str = "・".join(gc.get("planets", []))
            signs_str = "・".join(gc.get("signs", []))
            mode_msg = {
                "活動": "変化と行動のエネルギーが四方向から働いています。多くの課題に同時に向き合いながら、大きな成長を遂げる配置です。",
                "固定": "強い意志と粘り強さが四方向から働いています。困難を乗り越えて、揺るぎない力を築く配置です。",
                "柔軟": "適応力と変化への対応力が四方向から働いています。多様な状況に対処しながら、深い智慧を育てる配置です。",
                "不定": "強烈なエネルギーが四方向から交差するグランドクロスです。大きな試練と同時に、大きな成長の機会があります。",
            }.get(mode, "")
            rows = [
                [Paragraph(f"■ グランドクロス（{mode}モード）", S('gc', 11, PURPLE_MID, True, sb=4, sa=4))],
                [Paragraph(f"天体：{planets_str}", STYLE_BODY)],
                [Paragraph(f"星座：{signs_str}", STYLE_BODY)],
                [Spacer(1, 4)],
                [Paragraph(mode_msg, STYLE_BODY)],
            ]
            card = Table(rows, colWidths=[165*mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
                ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0,0), (-1,-1), 14),
                ('RIGHTPADDING', (0,0), (-1,-1), 14),
                ('TOPPADDING', (0,0), (0,0), 10),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ]))
            story.append(card)
            story.append(Spacer(1, 12))

    story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 数秘術
    # --------------------------------------------------------
    section("数秘術")

    lp_val = str(user_data.get("life_path", ""))
    bd_val = str(user_data.get("birthday_num", ""))
    rl_val = str(user_data.get("ruler_num", ""))

    nd = [
        [
            Paragraph("ライフパス", S('nl1', 9, PURPLE_DARK, True, 'CENTER', sb=2, sa=2)),
            Paragraph("バースデー", S('nl2', 9, PURPLE_DARK, True, 'CENTER', sb=2, sa=2)),
            Paragraph("ルーラー",   S('nl3', 9, PURPLE_DARK, True, 'CENTER', sb=2, sa=2)),
        ],
        [
            Paragraph(lp_val, S('nv1', 16, PURPLE_MID, True, 'CENTER', sb=2, sa=2)),
            Paragraph(bd_val, S('nv2', 16, PURPLE_MID, True, 'CENTER', sb=2, sa=2)),
            Paragraph(rl_val, S('nv3', 16, PURPLE_MID, True, 'CENTER', sb=2, sa=2)),
        ],
    ]

    nt = Table(nd, colWidths=[40*mm, 40*mm, 40*mm])
    nt.setStyle(TableStyle([
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

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"■ ライフパスナンバー {lp_num}　～人生のテーマ・使命～",
        S('lpt', 14, TEXT_DARK, True, sb=0, sa=2)
    ))
    story.append(Paragraph(
        "人生全体のテーマ・使命・歩むべき道",
        S('lps', 9, TEXT_GRAY, False, sb=0, sa=0)
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER, spaceBefore=6, spaceAfter=8))

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
        NUM_TITLES = {
    1: "リーダー・開拓者", 2: "調和・協力者", 3: "表現者・クリエイター",
    4: "誠実・建設者", 5: "自由・冒険者", 6: "愛・奉仕者",
    7: "探求・思想家", 8: "達成・実業家", 9: "博愛・完成者",
    11: "直感・インスピレーター（マスターナンバー）",
    22: "夢実現・マスタービルダー（マスターナンバー）",
    33: "愛と癒しの師（マスターナンバー）",
}
        bd_num_int = int(bd_num) if str(bd_num).isdigit() else 0
        bd_subtitle = NUM_TITLES.get(bd_num_int, "")
        bd_block = [
            Spacer(1, 10),
            Paragraph(
                f"■ バースデーナンバー {bd_num}　～生まれ持った才能～",
                S('bdt', 14, TEXT_DARK, True, sb=0, sa=2)
            ),
            Paragraph(
                "生まれ持った才能・自然に発揮できる力",
                S('bds', 9, TEXT_GRAY, False, sb=0, sa=0)
            ),
            HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER, spaceBefore=6, spaceAfter=8),
        ]
        if bd_subtitle:
            bd_block.append(Paragraph(f"{bd_num}：{bd_subtitle}", STYLE_H2))
        for line in bd_msg.split("\n"):
            line = line.strip()
            if not line:
                bd_block.append(Spacer(1, 4))
            elif line.startswith("【"):
                bd_block.append(Paragraph(line, STYLE_H3))
            else:
                bd_block.append(Paragraph(line, STYLE_BODY))
        bd_block.append(Spacer(1, 14))
        story.append(KeepTogether(bd_block))

    # ルーラーナンバー
    rl_num = user_data.get("ruler_num", "")
    rl_msg = user_data.get("ruler_message", "")
    if rl_msg:
        NUM_TITLES = {
    1: "リーダー・開拓者", 2: "調和・協力者", 3: "表現者・クリエイター",
    4: "誠実・建設者", 5: "自由・冒険者", 6: "愛・奉仕者",
    7: "探求・思想家", 8: "達成・実業家", 9: "博愛・完成者",
    11: "直感・インスピレーター（マスターナンバー）",
    22: "夢実現・マスタービルダー（マスターナンバー）",
    33: "愛と癒しの師（マスターナンバー）",
}
        rl_num_int = int(rl_num) if str(rl_num).isdigit() else 0
        rl_subtitle = NUM_TITLES.get(rl_num_int, "")
        rl_block = [
            Spacer(1, 10),
            Paragraph(
                f"■ ルーラーナンバー {rl_num}　～生まれた年の使命～",
                S('rlt', 14, TEXT_DARK, True, sb=0, sa=2)
            ),
            Paragraph(
                "生まれた年が示す使命・人生のテーマ",
                S('rls', 9, TEXT_GRAY, False, sb=0, sa=0)
            ),
            HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER, spaceBefore=6, spaceAfter=8),
        ]
        if rl_subtitle:
            rl_block.append(Paragraph(f"{rl_num}：{rl_subtitle}", STYLE_H2))
        for line in rl_msg.split("\n"):
            line = line.strip()
            if not line:
                rl_block.append(Spacer(1, 4))
            elif line.startswith("【"):
                rl_block.append(Paragraph(line, STYLE_H3))
            else:
                rl_block.append(Paragraph(line, STYLE_BODY))
        story.append(KeepTogether(rl_block))

    story.append(PageBreak())

    # --------------------------------------------------------
    # ★ 外惑星（資料編）の前置き
    # --------------------------------------------------------
    outer_intro_rows = [
        [Paragraph(
            "ここからは補足です",
            S('oi_t', 11, PURPLE_DARK, True, 'CENTER', sb=2, sa=4)
        )],
        [Paragraph(
            "木星から冥王星までは動きがゆっくりで、同世代の人と近い配置になりやすい天体です。"
            "ここまでの内容で十分にあなたらしさは掴めていますので、"
            "「もっと詳しく知りたい」という方は参考としてご覧ください。",
            S('oi_b', 9, TEXT_DARK, False, 'CENTER', sb=0, sa=2)
        )],
    ]
    outer_intro = Table(outer_intro_rows, colWidths=[165 * mm])
    outer_intro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (0, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
    ]))
    story.append(outer_intro)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # ★ 外惑星（興味がある人向けの資料編）
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

    # 最後のカード直後の余白（Spacer 20mm）を詰めて、フッターが同一ページに収まりやすくする
    if story and isinstance(story[-1], Spacer):
        story.pop()
        story.append(Spacer(1, 4))

    # --------------------------------------------------------
    # ★ フッター
    # --------------------------------------------------------
    story.append(KeepTogether([
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER),
        Paragraph(
            "Luna 占星術　Luna-compass",
            S('ft', 8, TEXT_GRAY, align='CENTER', sb=4, sa=0),
        ),
    ]))

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
        topMargin=12 * mm,
        bottomMargin=12 * mm,
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
    # ★ 鑑定書の読み方ガイド
    # --------------------------------------------------------
    guide_rows = [
        [Paragraph(
            "【この鑑定書について】ネイタルチャートに今日の天体（トランジット）がどう影響しているかをお伝えします。"
            "アスペクトで今の流れを、外惑星の動きで大きなテーマをご確認ください。",
            S('gb', 8, PURPLE_DARK, False, 'LEFT', sb=2, sa=2)
        )],
    ]
    guide_table = Table(guide_rows, colWidths=[165*mm])
    guide_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (0,0), 6),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 6),
    ]))
    story.append(guide_table)
    story.append(Spacer(1, 6))

    # --------------------------------------------------------
    # ★ チャート（2重円）
    # --------------------------------------------------------
    if chart_image_bytes:
        img = Image(chart_image_bytes, width=130 * mm, height=130 * mm)
        img.hAlign = 'CENTER'
        _sym_t = 'Symbols' if _symbol_font_registered else 'JP'
        _sym2_t = 'Symbols2' if _symbol2_font_registered else _sym_t
        def _st(sym, jp):
            font = _sym2_t if sym == "☉" else _sym_t
            return f'<font name="{font}">{sym}</font>{jp}'
        _sign_row1_t = "　".join([_st("♈","牡羊座"),_st("♉","牡牛座"),_st("♊","双子座"),_st("♋","蟹座"),_st("♌","獅子座"),_st("♍","乙女座")])
        _sign_row2_t = "　".join([_st("♎","天秤座"),_st("♏","蠍座"),_st("♐","射手座"),_st("♑","山羊座"),_st("♒","水瓶座"),_st("♓","魚座")])
        _planet_row_t = "　".join([_st("☉","太陽"),_st("☽","月"),_st("☿","水星"),_st("♀","金星"),_st("♂","火星"),_st("♃","木星"),_st("♄","土星"),_st("♅","天王星"),_st("♆","海王星"),_st("♇","冥王星")])
        sign_legend_rows = [
            [Paragraph("ホロスコープの記号の見方", S('sl', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(_sign_row1_t, S('sl2', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_sign_row2_t, S('sl2b', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_planet_row_t, S('sl3', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=2))],
            [Paragraph("▲マーク=トランジット（今日）の天体　●マーク=ネイタル（生まれた時）の天体", S('sl4', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=4))],
        ]
        sign_legend = Table(sign_legend_rows, colWidths=[165*mm])
        sign_legend.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        chart_block = KeepTogether([
            Paragraph("◆ ホロスコープ（ネイタル＋トランジット）", STYLE_H1),
            Spacer(1, 4),
            img,
            Spacer(1, 6),
        ])
        story.append(chart_block)
        story.append(sign_legend)
        story.append(Spacer(1, 6))
        story.append(PageBreak())

    # --------------------------------------------------------
    # ★ section関数をローカル定義
    # --------------------------------------------------------
    def section(title):
        story.append(Spacer(1, 8))
        sec_rows = [[Paragraph(f"◆ {title}", S('sec', 13, colors.white, True, sb=0, sa=0))]]
        sec_table = Table(sec_rows, colWidths=[165*mm])
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_DARK),
            ('LEFTPADDING', (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 10))

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

    _sym2_t2 = 'Symbols2' if _symbol2_font_registered else ('Symbols' if _symbol_font_registered else 'JP')
    _sym_t2 = 'Symbols' if _symbol_font_registered else 'JP'
    story.append(Paragraph(f'<font name="{_sym2_t2}">☉</font> トランジット太陽：{t_sun} {t_sun_deg}', S('p', 10, PURPLE_MID, True, sb=2, sa=4)))
    story.append(Paragraph(f'<font name="{_sym_t2}">☽</font> トランジット月：{t_moon} {t_moon_deg}', S('p', 10, PURPLE_MID, True, sb=2, sa=8)))

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

    # --------------------------------------------------------
    # ★ グランドトライン・グランドクロス（トランジット）
    # --------------------------------------------------------
    grand_trines = natal_data.get("grand_trines", [])
    grand_crosses = natal_data.get("grand_crosses", [])

    if grand_trines or grand_crosses:
        section("特別なパターン")

        for gt in grand_trines:
            elem = gt.get("element", "")
            planets_str = "・".join([p.replace("T_","トランジット") for p in gt.get("planets", [])])
            elem_msg = {
                "火": "情熱・行動・創造のエネルギーが大きく調和しています。積極的に動く絶好のタイミングです。",
                "地": "安定・実行・現実化のエネルギーが調和しています。着実な行動が大きな実りを生みます。",
                "風": "知性・表現・つながりのエネルギーが調和しています。発信や学びに最高のタイミングです。",
                "水": "感情・直感・癒しのエネルギーが調和しています。感性を信じて動くと良い流れが生まれます。",
                "混合": "今の天体の流れがあなたのチャートと大きなトラインを形成しています。",
            }.get(elem, "")
            rows = [
                [Paragraph(f"▲ グランドトライン（{elem}のエレメント）", S('gt', 11, PURPLE_MID, True, sb=4, sa=4))],
                [Paragraph(f"天体：{planets_str}", STYLE_BODY)],
                [Spacer(1, 4)],
                [Paragraph(elem_msg, STYLE_BODY)],
            ]
            card = Table(rows, colWidths=[165*mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
                ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0,0), (-1,-1), 14),
                ('RIGHTPADDING', (0,0), (-1,-1), 14),
                ('TOPPADDING', (0,0), (0,0), 10),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ]))
            story.append(card)
            story.append(Spacer(1, 12))

        for gc in grand_crosses:
            mode = gc.get("mode", "")
            planets_str = "・".join([p.replace("T_","トランジット") for p in gc.get("planets", [])])
            mode_base = {
                "活動": "今の天体の流れがあなたのチャートと大きな十字を形成しています。多くのテーマと同時に向き合う時期ですが、乗り越えた先に大きな成長があります。",
                "固定": "強固なエネルギーが今の流れで交差しています。粘り強さと忍耐が大きな力になります。",
                "柔軟": "今の天体の流れが適応力を試す十字を形成しています。柔軟に対応することで突破口が開けます。",
                "不定": "今の流れがあなたのチャートと強いグランドクロスを形成しています。",
            }.get(mode, "")
            mode_msg = f"{planets_str}が{mode}モードで大きな十字を形成しています。{mode_base}"
            rows = [
                [Paragraph(f"グランドクロス（{mode}モード）", S('gc', 11, PURPLE_MID, True, sb=4, sa=4))],
                [Paragraph(f"天体：{planets_str}", STYLE_BODY)],
                [Spacer(1, 4)],
                [Paragraph(mode_msg, STYLE_BODY)],
            ]
            card = Table(rows, colWidths=[165*mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
                ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0,0), (-1,-1), 14),
                ('RIGHTPADDING', (0,0), (-1,-1), 14),
                ('TOPPADDING', (0,0), (0,0), 10),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ]))
            story.append(card)
            story.append(Spacer(1, 12))

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

        _sym_op = 'Symbols' if _symbol_font_registered else 'JP'
        rows = [[Paragraph(f'<font name="{_sym_op}">♃</font> {p_name}：{p_sign} {p_deg}', S('p', 10, PURPLE_MID, True, sb=4, sa=4))]]
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
    overall, compat_note, chart_image_bytes=None, overall_data=None
):
    import io as _io

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    story = []

    def section(title):
        story.append(Spacer(1, 8))
        sec_rows = [[Paragraph(f"◆ {title}", S('sec', 13, colors.white, True, sb=0, sa=0))]]
        sec_table = Table(sec_rows, colWidths=[165*mm])
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_DARK),
            ('LEFTPADDING', (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 10))

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
    # ★ 鑑定書の読み方ガイド
    # --------------------------------------------------------
    guide_rows = [
        [Paragraph(
            "【この鑑定書について】2人の星の配置から相性を読み解く総合相性鑑定書です。"
            "太陽・月・金星×火星の相性でお二人の本質的なつながりを、"
            "グランドトライン等の特別なパターンにもぜひご注目ください。",
            S('gb', 8, PURPLE_DARK, False, 'LEFT', sb=2, sa=2)
        )],
    ]
    guide_table = Table(guide_rows, colWidths=[165*mm])
    guide_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (0,0), 6),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 6),
    ]))
    story.append(guide_table)
    story.append(Spacer(1, 6))

    # --------------------------------------------------------
    # ★ チャート
    # --------------------------------------------------------
    if chart_image_bytes:
        img = Image(chart_image_bytes, width=130 * mm, height=130 * mm)
        img.hAlign = 'CENTER'
        _sym_c = 'Symbols' if _symbol_font_registered else 'JP'
        _sym2_c = 'Symbols2' if _symbol2_font_registered else _sym_c
        def _sc(sym, jp):
            font = _sym2_c if sym == "☉" else _sym_c
            return f'<font name="{font}">{sym}</font>{jp}'
        _sign_row1_c = "　".join([_sc("♈","牡羊座"),_sc("♉","牡牛座"),_sc("♊","双子座"),_sc("♋","蟹座"),_sc("♌","獅子座"),_sc("♍","乙女座")])
        _sign_row2_c = "　".join([_sc("♎","天秤座"),_sc("♏","蠍座"),_sc("♐","射手座"),_sc("♑","山羊座"),_sc("♒","水瓶座"),_sc("♓","魚座")])
        _planet_row_c = "　".join([_sc("☉","太陽"),_sc("☽","月"),_sc("☿","水星"),_sc("♀","金星"),_sc("♂","火星"),_sc("♃","木星"),_sc("♄","土星"),_sc("♅","天王星"),_sc("♆","海王星"),_sc("♇","冥王星")])
        sign_legend_rows = [
            [Paragraph("ホロスコープの記号の見方", S('sl', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(_sign_row1_c, S('sl2', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_sign_row2_c, S('sl2b', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_planet_row_c, S('sl3', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=4))],
        ]
        sign_legend = Table(sign_legend_rows, colWidths=[165*mm])
        sign_legend.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        chart_block = KeepTogether([
            Paragraph("◆ ホロスコープ（2人の重ね表示）", STYLE_H1),
            Spacer(1, 4),
            img,
            Spacer(1, 6),
            sign_legend,
            Spacer(1, 6),
        ])
        story.append(chart_block)
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
        [Paragraph("☉ 太陽", STYLE_BODY), Paragraph(sun_sign1, STYLE_BODY), Paragraph(sun_sign2, STYLE_BODY)],
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
    # ★ 2人の特別なパターン
    # --------------------------------------------------------
    grand_trines = overall_data.get("grand_trines", []) if isinstance(overall_data, dict) else []
    grand_crosses = overall_data.get("grand_crosses", []) if isinstance(overall_data, dict) else []

    if grand_trines or grand_crosses:
        section("2人の特別なパターン")

        for gt in grand_trines:
            elem = gt.get("element", "")
            planets_str = "・".join([p.replace("T_","相手の") for p in gt.get("planets", [])])
            elem_msg = {
                "火": "2人のエネルギーが火のエレメントで大きく調和しています。情熱・行動力・創造性が共鳴する素晴らしい組み合わせです。",
                "地": "2人のエネルギーが地のエレメントで大きく調和しています。安定・信頼・現実的な力が深く共鳴します。",
                "風": "2人のエネルギーが風のエレメントで大きく調和しています。知性・コミュニケーション・自由が共鳴する関係です。",
                "水": "2人のエネルギーが水のエレメントで大きく調和しています。感情・共感・直感が深く共鳴する魂の絆です。",
                "混合": "2人の天体が大きなグランドトラインを形成しています。",
            }.get(elem, "")
            rows = [
                [Paragraph(f"2人のグランドトライン（{elem}のエレメント）", S('gt', 11, PURPLE_MID, True, sb=4, sa=4))],
                [Paragraph(f"天体：{planets_str}", STYLE_BODY)],
                [Spacer(1, 4)],
                [Paragraph(elem_msg, STYLE_BODY)],
            ]
            card = Table(rows, colWidths=[165*mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
                ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0,0), (-1,-1), 14),
                ('RIGHTPADDING', (0,0), (-1,-1), 14),
                ('TOPPADDING', (0,0), (0,0), 10),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ]))
            story.append(card)
            story.append(Spacer(1, 12))

        for gc in grand_crosses:
            mode = gc.get("mode", "")
            planets_str = "・".join([p.replace("T_","相手の") for p in gc.get("planets", [])])
            mode_msg = {
                "活動": "2人の天体が活動サインで大きな十字を形成しています。お互いの課題が刺激し合い、大きな成長をもたらす関係です。",
                "固定": "2人の天体が固定サインで大きな十字を形成しています。強い意志を持つ者同士が向き合う、深い絆の関係です。",
                "柔軟": "2人の天体が柔軟サインで大きな十字を形成しています。お互いの適応力が試される、成長し合える関係です。",
                "不定": "2人の天体が大きなグランドクロスを形成しています。",
            }.get(mode, "")
            rows = [
                [Paragraph(f"2人のグランドクロス（{mode}モード）", S('gc', 11, PURPLE_MID, True, sb=4, sa=4))],
                [Paragraph(f"天体：{planets_str}", STYLE_BODY)],
                [Spacer(1, 4)],
                [Paragraph(mode_msg, STYLE_BODY)],
            ]
            card = Table(rows, colWidths=[165*mm])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
                ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
                ('LEFTPADDING', (0,0), (-1,-1), 14),
                ('RIGHTPADDING', (0,0), (-1,-1), 14),
                ('TOPPADDING', (0,0), (0,0), 10),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ]))
            story.append(card)
            story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ★ 数秘術の相性
    # --------------------------------------------------------
    num_lp1 = overall_data.get("num_lp1") if isinstance(overall_data, dict) else None
    if num_lp1 is not None:
        section("数秘術の相性")
        num_lp2 = overall_data.get("num_lp2")
        num_bd1 = overall_data.get("num_bd1")
        num_bd2 = overall_data.get("num_bd2")
        num_rl1 = overall_data.get("num_rl1")
        num_rl2 = overall_data.get("num_rl2")
        num_lp_msg = overall_data.get("num_lp_msg", "")
        num_bd_msg = overall_data.get("num_bd_msg", "")
        num_rl_msg = overall_data.get("num_rl_msg", "")
        num_overall = overall_data.get("num_overall", "")
        n1 = overall_data.get("name1", "お相手1")
        n2 = overall_data.get("name2", "お相手2")

        # 数字一覧テーブル
        num_info = [
            [Paragraph("", STYLE_BODY),
             Paragraph(str(n1), S('h', 10, PURPLE_DARK, True)),
             Paragraph(str(n2), S('h', 10, PURPLE_DARK, True))],
            [Paragraph("ライフパス", S('h', 9, PURPLE_DARK, True)),
             Paragraph(str(num_lp1), S('v', 11, PURPLE_MID, True, 'CENTER')),
             Paragraph(str(num_lp2), S('v', 11, PURPLE_MID, True, 'CENTER'))],
            [Paragraph("バースデー", S('h', 9, PURPLE_DARK, True)),
             Paragraph(str(num_bd1), S('v', 11, PURPLE_MID, True, 'CENTER')),
             Paragraph(str(num_bd2), S('v', 11, PURPLE_MID, True, 'CENTER'))],
            [Paragraph("ルーラー", S('h', 9, PURPLE_DARK, True)),
             Paragraph(str(num_rl1), S('v', 11, PURPLE_MID, True, 'CENTER')),
             Paragraph(str(num_rl2), S('v', 11, PURPLE_MID, True, 'CENTER'))],
        ]
        num_table = Table(num_info, colWidths=[40*mm, 60*mm, 60*mm])
        num_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), PURPLE_LIGHT),
            ('BACKGROUND', (0,0), (-1,0), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
            ('INNERGRID', (0,0), (-1,-1), 0.3, PURPLE_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ]))
        story.append(num_table)
        story.append(Spacer(1, 10))

        for label, msg in [
            ("ライフパスの相性（人生テーマ）", num_lp_msg),
            ("バースデーの相性（才能・個性）", num_bd_msg),
            ("ルーラーの相性（使命・エネルギー）", num_rl_msg),
        ]:
            story.append(Paragraph(f"◇ {label}", STYLE_H3))
            story.append(Paragraph(msg, STYLE_BODY))
            story.append(Spacer(1, 6))

        story.append(Paragraph("◇ 総合数秘術相性", STYLE_H3))
        story.append(Paragraph(num_overall, STYLE_BODY))
        story.append(Spacer(1, 10))

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
