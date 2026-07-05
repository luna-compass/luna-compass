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
        wordWrap='CJK',  # 日本語禁則処理（。、」等が行頭に来ないようにする）
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
    def section(title, defer=False):
        flowables = [Spacer(1, 8)]
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
        flowables.append(sec_table)
        flowables.append(Spacer(1, 10))
        if defer:
            return flowables
        story.extend(flowables)


    # --------------------------------------------------------
    # ★ 惑星カード（ここで定義）
    # --------------------------------------------------------
    time_unknown = user_data.get("time_unknown", False)

    def planet_row(symbol, label, sign, deg, house, msg, house_msg="", extra_note="", defer=False):
        if not sign:
            return [] if defer else None

        content = []
        # ハウス表示：time_unknownのとき非表示
        # 惑星記号にSymbolsフォントを適用
        _sym_f = 'Symbols2' if _symbol2_font_registered and symbol == "☉" else ('Symbols' if _symbol_font_registered else 'JP')
        symbol_html = f'<font name="{_sym_f}">{symbol}</font>'
        header = f"{symbol_html} {label}　{sign} {deg}"
        if house and not time_unknown:
            header += f"　　　　　　{house}ハウス"
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

        # 追加注記（月星座の境界注意など）
        if extra_note:
            content.append(Paragraph(extra_note, STYLE_NOTE))

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

        if defer:
            return [card, Spacer(1, 20)]

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
        sign_row1 = "\u00A0\u00A0\u00A0\u00A0".join([
            _s("♈","牡羊座"), _s("♉","牡牛座"), _s("♊","双子座"), _s("♋","蟹座"),
            _s("♌","獅子座"), _s("♍","乙女座"),
        ])
        sign_row2 = "\u00A0\u00A0\u00A0\u00A0".join([
            _s("♎","天秤座"), _s("♏","蠍座"), _s("♐","射手座"),
            _s("♑","山羊座"), _s("♒","水瓶座"), _s("♓","魚座"),
        ])
        sign_legend_rows = [
            [Paragraph("ホロスコープの記号の見方", S('sl', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(sign_row1, S('sl2', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(sign_row2, S('sl2b', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(
                "\u00A0\u00A0\u00A0\u00A0".join([
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
    # 時刻不明時はASCセクションが無いため、読み順の文言を切り替える
    _guide_order = "続いて太陽・月・水星・金星・火星、" if time_unknown else "続いてASC・太陽・月・水星・金星・火星、"
    guide_rows = [
        [Paragraph("この鑑定書について", S('gt', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
        [Paragraph(
            "本鑑定書は「占星術・数秘術・タロット」の3つの視点からお届けする総合鑑定書です。"
            "1ページ目のホロスコープはあなたの星の配置を示しています。"
            "次にキーワードと総合メッセージをご覧ください。"
            "また「占い師からのひとこと」には、鑑定師があなたのホロスコープを見て感じたメッセージを込めています。"
            "その後の「今日のあなたへのメッセージ」は、タロットからの「今このときのあなたへ」のメッセージです。"
            + _guide_order +
            "そしてアスペクト（天体同士の関係性）、数秘術と"
            "順にお読みいただくと、あなたの全体像がより深く理解できます。"
            "最後の外惑星は、興味のある方向けの補足資料としてご覧ください。",
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
        story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_MID, spaceAfter=4))
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
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(kw_table)
        story.append(Spacer(1, 8))

    # 総合メッセージ
    overall_first = user_data.get("overall_message", "")
    astrologer_top = user_data.get("astrologer_message", "")

    if overall_first or astrologer_top:
        story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_MID, spaceAfter=4))
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
        # 占星術の基本用語解説（惑星・ハウス・アセンダント）
        term_guide_rows = [
            [Paragraph("占星術の基本用語", S('tg', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(
                "占星術には「惑星」「ハウス」「アセンダント」という基本要素があります。"
                "この3つを組み合わせて読み解くことで、あなたらしさが立体的に見えてきます。",
                S('tg_i', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=8)
            )],
            [Paragraph(
                "◇ 惑星（天体）とは：太陽・月・水星・金星・火星などの天体は、それぞれ性格や才能の"
                "異なるテーマ・エネルギーを象徴します。太陽は「本質」、月は「感情」、水星は「思考・"
                "コミュニケーション」、金星は「愛や好み」、火星は「行動力」を表します。さらに木星から"
                "冥王星までの外惑星は、幸運や人生の課題など、より大きなスケールでの成長テーマを示します。",
                S('tg_p', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=6)
            )],
            [Paragraph(
                "◇ ハウスとは：天体が人生のどの分野（仕事・家庭・人間関係など）で力を発揮しやすいかを示す"
                "「舞台」です。星座が天体の「性質」を表すのに対し、ハウスは「舞台」というイメージです。",
                S('tg_h', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=6)
            )],
            [Paragraph(
                "◇ アセンダントとは：生まれた瞬間に東の地平線から昇っていた星座で、「第一印象」や"
                "「外から見たあなた」を表します。太陽が「本質」なら、アセンダントは「見た目の入り口」です。",
                S('tg_a', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=0)
            )],
        ]
        term_guide_table = Table(term_guide_rows, colWidths=[165*mm])
        term_guide_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (0,0), 8),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
        ]))
        story.append(term_guide_table)
        story.append(Spacer(1, 8))

        asc_header_flowables = section("第一印象（ASC）", defer=True)

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

        story.append(KeepTogether(asc_header_flowables + [asc_card]))
        story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # ★ 太陽・月（性格の核）
    # --------------------------------------------------------
    if time_unknown:
        # 出生時刻不明の場合はASC・ハウスの説明がないため、惑星のみの簡易版をここに表示
        term_guide_rows_tu = [
            [Paragraph("占星術の基本用語", S('tgu', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(
                "◇ 惑星（天体）とは：太陽・月・水星・金星・火星などの天体は、それぞれ性格や才能の"
                "異なるテーマ・エネルギーを象徴します。太陽は「本質」、月は「感情」、水星は「思考・"
                "コミュニケーション」、金星は「愛や好み」、火星は「行動力」を表します。さらに木星から"
                "冥王星までの外惑星は、幸運や人生の課題など、より大きなスケールでの成長テーマを示します。"
                "これから登場する天体それぞれの意味を読み解いていきましょう。",
                S('tgu_p', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=0)
            )],
        ]
        term_guide_table_tu = Table(term_guide_rows_tu, colWidths=[165*mm])
        term_guide_table_tu.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, PURPLE_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (0,0), 8),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
        ]))
        story.append(term_guide_table_tu)
        story.append(Spacer(1, 8))

    sun_moon_header_flowables = section("太陽・月", defer=True)

    # 時刻不明時、月が星座の境界付近（0〜7度・23〜30度）なら注記を出す
    # （月は1日に約13度動くため、正午±12時間で約±6.5度の幅がある）
    moon_boundary_note = ""
    if time_unknown:
        try:
            _moon_d = int(str(user_data.get("moon_deg", "")).split("°")[0].strip())
            if _moon_d < 7 or _moon_d >= 23:
                moon_boundary_note = (
                    "※ 月は1日に約13度動くため、出生時刻が不明の場合、"
                    "実際の出生時刻によっては月星座が隣の星座になる可能性があります。"
                )
        except (ValueError, TypeError):
            pass

    for _sm_idx, (sym, lbl, ks, kd, kh, km, khm) in enumerate([
        ("☉", "太陽（本質）", "sun_sign", "sun_deg", "sun_house", "sun_message", "sun_house_message"),
        ("☽", "月（感情）", "moon_sign", "moon_deg", "moon_house", "moon_message", "moon_house_message"),
    ]):
        if _sm_idx == 0:
            first_flowables = planet_row(
                sym, lbl,
                user_data.get(ks, ""),
                user_data.get(kd, ""),
                user_data.get(kh, ""),
                user_data.get(km, ""),
                user_data.get(khm, ""),
                extra_note=moon_boundary_note if ks == "moon_sign" else "",
                defer=True,
            )
            story.append(KeepTogether(sun_moon_header_flowables + first_flowables))
            continue
        planet_row(
            sym, lbl,
            user_data.get(ks, ""),
            user_data.get(kd, ""),
            user_data.get(kh, ""),
            user_data.get(km, ""),
            user_data.get(khm, ""),
            extra_note=moon_boundary_note if ks == "moon_sign" else "",
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
                S('asp_h', 11, PURPLE_MID, True, 'LEFT', sb=5, sa=2),
            ))
            story.append(Paragraph(a.get("message", ""), STYLE_BODY))
            story.append(Spacer(1, 2))

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

    # 数秘術の説明文（一般の方向けの補足）
    numerology_intro_rows = [
        [Paragraph(
            "数秘術とは、生年月日から導き出される数字であなたを読み解く占術です。"
            "星占いとは違う角度から、あなたの人生のテーマや才能を紐解くことができます。",
            S('ni_b', 9, TEXT_DARK, False, 'LEFT', sb=0, sa=8)
        )],
        [Paragraph("ライフパス：人生全体のテーマ・使命", S('ni_l1', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=3))],
        [Paragraph("バースデー：生まれ持った才能", S('ni_l2', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=3))],
        [Paragraph("ルーラー：生まれた年が示す使命", S('ni_l3', 8, TEXT_GRAY, False, 'LEFT', sb=0, sa=0))],
    ]
    numerology_intro = Table(numerology_intro_rows, colWidths=[165 * mm])
    numerology_intro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (0, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
    ]))
    story.append(numerology_intro)
    story.append(Spacer(1, 12))

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
        _sign_row1_t = "\u00A0\u00A0\u00A0\u00A0".join([_st("♈","牡羊座"),_st("♉","牡牛座"),_st("♊","双子座"),_st("♋","蟹座"),_st("♌","獅子座"),_st("♍","乙女座")])
        _sign_row2_t = "\u00A0\u00A0\u00A0\u00A0".join([_st("♎","天秤座"),_st("♏","蠍座"),_st("♐","射手座"),_st("♑","山羊座"),_st("♒","水瓶座"),_st("♓","魚座")])
        _planet_row_t = "\u00A0\u00A0\u00A0\u00A0".join([_st("☉","太陽"),_st("☽","月"),_st("☿","水星"),_st("♀","金星"),_st("♂","火星"),_st("♃","木星"),_st("♄","土星"),_st("♅","天王星"),_st("♆","海王星"),_st("♇","冥王星")])
        sign_legend_rows = [
            [Paragraph("ホロスコープの記号の見方", S('sl', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(_sign_row1_t, S('sl2', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_sign_row2_t, S('sl2b', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_planet_row_t, S('sl3', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=2))],
            [Paragraph("▲マーク=トランジット（今日）の天体\u00A0\u00A0\u00A0\u00A0●マーク=ネイタル（生まれた時）の天体", S('sl4', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=4))],
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
        "セクスタイル": "☆",
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
        _op_syms = {"木星": "♃", "土星": "♄", "天王星": "♅", "海王星": "♆", "冥王星": "♇"}
        _op_sym = _op_syms.get(p_name, "♃")
        rows = [[Paragraph(f'<font name="{_sym_op}">{_op_sym}</font> {p_name}：{p_sign} {p_deg}', S('p', 10, PURPLE_MID, True, sb=4, sa=4))]]
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
        _sign_row1_c = "\u00A0\u00A0\u00A0\u00A0".join([_sc("♈","牡羊座"),_sc("♉","牡牛座"),_sc("♊","双子座"),_sc("♋","蟹座"),_sc("♌","獅子座"),_sc("♍","乙女座")])
        _sign_row2_c = "\u00A0\u00A0\u00A0\u00A0".join([_sc("♎","天秤座"),_sc("♏","蠍座"),_sc("♐","射手座"),_sc("♑","山羊座"),_sc("♒","水瓶座"),_sc("♓","魚座")])
        _planet_row_c = "\u00A0\u00A0\u00A0\u00A0".join([_sc("☉","太陽"),_sc("☽","月"),_sc("☿","水星"),_sc("♀","金星"),_sc("♂","火星"),_sc("♃","木星"),_sc("♄","土星"),_sc("♅","天王星"),_sc("♆","海王星"),_sc("♇","冥王星")])
        sign_legend_rows = [
            [Paragraph("ホロスコープの記号の見方", S('sl', 10, PURPLE_DARK, True, 'CENTER', sb=4, sa=4))],
            [Paragraph(_sign_row1_c, S('sl2', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_sign_row2_c, S('sl2b', 8, PURPLE_DARK, False, 'CENTER', sb=2, sa=2))],
            [Paragraph(_planet_row_c, S('sl3', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=4))],
            [Paragraph(f"●マーク={name1}の天体    ▲マーク={name2}の天体", S('sl4', 8, TEXT_GRAY, False, 'CENTER', sb=2, sa=4))],
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
        [Paragraph('<font name="' + ('Symbols' if _symbol_font_registered else 'JP') + '">☽</font> 月', STYLE_BODY), Paragraph(moon_sign1, STYLE_BODY), Paragraph(moon_sign2, STYLE_BODY)],
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
        if line.startswith("【総合】"):
            continue  # 末尾の「総合相性メッセージ」と重複するためスキップ
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

        # 同一メッセージが複数カテゴリに出る場合は、2件目以降をカテゴリ別の言い回しに差し替える
        _num_alt = {
            "ライフパスの相性（人生テーマ）": "人生のテーマが異なる2人。互いの歩む道を尊重し合うことで、1人では見えない景色が見えてくる相性です。",
            "バースデーの相性（才能・個性）": "持って生まれた才能が異なる2人。違う個性の掛け合わせが、新しい可能性を生み出します。",
            "ルーラーの相性（使命・エネルギー）": "使命のエネルギーが異なる2人。得意な役割を分担することで、お互いの世界が大きく広がります。",
        }
        _seen_num_msgs = set()
        for label, msg in [
            ("ライフパスの相性（人生テーマ）", num_lp_msg),
            ("バースデーの相性（才能・個性）", num_bd_msg),
            ("ルーラーの相性（使命・エネルギー）", num_rl_msg),
        ]:
            if msg and msg in _seen_num_msgs and label in _num_alt:
                msg = _num_alt[label]
            _seen_num_msgs.add(msg)
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


# ============================================================
# 四柱推命 鑑定書PDF生成
# ============================================================
def create_shichusuimei_pdf(user_data, shichu):
    """四柱推命の鑑定書PDFを生成する。

    user_data: {"name", "birthday", "birth_time", "reading_date", "time_unknown", "gender"}
    shichu: {
        "meishiki": build_meishiki() の戻り値,
        "kakukyoku": calc_kakukyoku() の戻り値,
        "tokubetsu": calc_tokubetsu_kakukyoku() の戻り値(None可),
        "shinjaku": calc_shinjaku() の戻り値,
        "getsurei": (状態, 得令bool),
        "natchin": 日柱の納音(str),
        "kankei": detect_kankei() の戻り値,
        "shinsatsu": detect_shinsatsu() の戻り値,
        "daiun": calc_daiun() の戻り値,
        "nenun": calc_nenun() の戻り値(5年分推奨),
        "messages": {"nikkan": dict, "ganmei": dict, "juniun": dict, "kubo": str},
    }
    構成順: 命式 → 本質 → 中心星と格局 → 命式の関係 → 大運 → 年運 → 補足(身強身弱) → 神殺 → 結び
    """
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
    time_unknown = user_data.get("time_unknown", False)

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

    def message_card(title, msg, extra_note=""):
        content = [Paragraph(title, S('p', 11, PURPLE_MID, True, sb=6, sa=10))]
        if msg:
            for line in msg.split("\n"):
                line = line.strip()
                if not line:
                    content.append(Spacer(1, 5))
                elif line.startswith("【"):
                    content.append(Paragraph(line, STYLE_H3))
                else:
                    content.append(Paragraph(line, STYLE_BODY))
        if extra_note:
            content.append(Paragraph(extra_note, STYLE_NOTE))
        rows = [[item] for item in content]
        card = Table(rows, colWidths=[165*mm])
        card.setStyle(TableStyle([
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
        ]))
        story.append(card)
        story.append(Spacer(1, 14))

    def data_table(header, rows_data, col_widths):
        rows = [[Paragraph(h, S('th', 9, colors.white, True, 'CENTER', sb=0, sa=0)) for h in header]]
        rows.extend(rows_data)
        tbl = Table(rows, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PURPLE_DARK),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PURPLE_LIGHT]),
            ('BOX', (0, 0), (-1, -1), 1, PURPLE_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))

    def C(text, size=9, color=TEXT_DARK, bold=False, align='CENTER'):
        return Paragraph(text, S('cell', size, color, bold, align, sb=0, sa=0))

    m = shichu["meishiki"]
    msgs = shichu.get("messages", {})

    # --------------------------------------------------------
    # 1ページ目: タイトル + 基本情報 + 命式表
    # --------------------------------------------------------
    story.append(Paragraph("Luna 四柱推命", S('t1', 16, PURPLE_DARK, True, 'CENTER', sb=4, sa=2)))
    story.append(Paragraph("命式鑑定書", S('t2', 11, PURPLE_MID, True, 'CENTER', sb=2, sa=4)))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=6))

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
                "不明（時柱を省いています）" if time_unknown else user_data.get("birth_time", ""),
                S('v', 9, color=TEXT_GRAY) if time_unknown else S('v', 9)
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

    story.append(Paragraph("この鑑定書について", STYLE_H2))
    story.append(Paragraph(
        "本鑑定書は四柱推命による命式鑑定書です。まず下の命式表があなたの生まれ持った星の配置です。"
        "続く「あなたの本質」で日干（あなたの中心）を、「中心星と格局」で人生のテーマを読み解きます。"
        "その後、命式の中の関係、大運（10年ごとの運気）、年運と続き、"
        "巻末には補足資料と神殺・特殊星の一覧を収めています。",
        STYLE_BODY))
    story.append(Spacer(1, 10))

    story.append(Paragraph("◆ あなたの命式", STYLE_H1))
    pillar_names = ["年柱", "月柱", "日柱"] if time_unknown else ["年柱", "月柱", "日柱", "時柱"]
    mrows = [[Paragraph(h, S('mh', 10, colors.white, True, 'CENTER', sb=0, sa=0))
              for h in ["柱", "干支", "蔵干(初→本気)", "通変星(天干)", "通変星(蔵干)", "十二運"]]]
    for pname in pillar_names:
        kan, shi = m["四柱"][pname]
        star = m["通変星"][pname]
        mrows.append([
            C(pname, 11, PURPLE_DARK, True),
            C(f"{kan}{shi}", 18, TEXT_DARK, True),
            C("→".join(m["蔵干"][pname]), 11),
            C(star["天干"], 11),
            C(star["蔵干本気"], 11),
            C(m["十二運"][pname], 11),
        ])
    mt = Table(mrows, colWidths=[18*mm, 30*mm, 40*mm, 28*mm, 28*mm, 21*mm])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE_DARK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PURPLE_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 9),
    ]))
    story.append(mt)
    story.append(Spacer(1, 10))

    e, yang = m["日干五行"]
    g_state, g_toku = shichu["getsurei"]
    bal = m["五行バランス"]
    bal_s = "　".join(f"{k}:{v}" for k, v in bal.items())
    kubo_s = "・".join(m["空亡"])
    summary_rows = [
        [Paragraph(
            f"日干: <b>{m['日干']}</b>（{e}の{'陽' if yang else '陰'}）　月令: {g_state}（{'得令' if g_toku else '失令'}）　日柱の納音: {shichu['natchin']}",
            S('sm', 10, TEXT_DARK, False, sb=0, sa=0))],
        [Paragraph(f"空亡（天中殺）: {kubo_s}　　五行バランス: {bal_s}",
                   S('sm', 10, TEXT_DARK, False, sb=0, sa=0))],
    ]
    sm_card = Table(summary_rows, colWidths=[165*mm])
    sm_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PURPLE_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, PURPLE_MID),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
        ('TOPPADDING', (0,1), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-2), 2),
    ]))
    story.append(sm_card)
    if time_unknown:
        story.append(Paragraph(
            "※ 出生時刻が不明のため、時柱を省いた三柱で作成しています。五行バランスは三柱分の集計です。",
            STYLE_NOTE))

    story.append(PageBreak())

    # --------------------------------------------------------
    # あなたの本質(日干)
    # --------------------------------------------------------
    section("あなたの本質（日干）")
    nk = msgs.get("nikkan", {})
    if nk:
        body = nk.get("message", "")
        extra = []
        if nk.get("talent"):
            extra.append(f"【才能】{nk['talent']}")
        if nk.get("challenge"):
            extra.append("【課題】" + nk["challenge"].replace("\n", " "))
        if nk.get("keywords"):
            extra.append(f"【キーワード】{nk['keywords']}")
        full = body + ("\n\n" + "\n".join(extra) if extra else "")
        message_card(nk.get("title", f"日干 {m['日干']}"), full)

    # --------------------------------------------------------
    # 中心星(元命)と格局
    # --------------------------------------------------------
    section("あなたの中心星と格局")
    gm_ = msgs.get("ganmei", {})
    if gm_:
        message_card(f"中心星（元命）: {gm_.get('title', '')}", gm_.get("message", ""))
    kaku = shichu["kakukyoku"]
    tokubetsu = shichu.get("tokubetsu")
    kaku_msg = f"判定根拠: {kaku['根拠']}"
    if tokubetsu:
        kaku_msg += f"\n\n【特別格局】{tokubetsu['名称']}\n{tokubetsu['根拠']}"
    message_card(f"格局: {kaku['格局']}", kaku_msg,
                 extra_note="※ 普通格局（建禄格・月刃格・八格）による判定です。")
    ju = msgs.get("juniun", {})
    if ju:
        message_card(f"日柱の十二運: {ju.get('title', '')}", ju.get("message", ""))

    # --------------------------------------------------------
    # 命式の中の関係
    # --------------------------------------------------------
    kankei = shichu.get("kankei", [])
    if time_unknown:
        kankei = [f for f in kankei if "時柱" not in f["柱"]]
    section("命式の中の関係（合・冲・刑・害・破）")
    if kankei:
        krows = [[C(f["種類"], 9, PURPLE_DARK, True), C(f["内容"]), C(f["柱"])] for f in kankei]
        data_table(["種類", "内容", "柱"], krows, [35*mm, 70*mm, 60*mm])
    else:
        story.append(Paragraph("命式の中に目立った合・冲・刑・害・破はありません。穏やかな配置です。", STYLE_BODY))
        story.append(Spacer(1, 4))

    kubo_msg = msgs.get("kubo", "")
    if kubo_msg:
        message_card(f"空亡（天中殺）: {kubo_s}", kubo_msg)

    # --------------------------------------------------------
    # 大運
    # --------------------------------------------------------
    section("大運（10年ごとの運気の流れ）")
    d = shichu["daiun"]
    ry, rm = d["立運"]
    story.append(Paragraph(
        f"大運は<b>{d['順逆']}</b>、立運は<b>{ry}歳{rm}ヶ月</b>です。"
        + ("※出生時刻不明のため立運は目安です。" if time_unknown else ""),
        STYLE_BODY))
    story.append(Spacer(1, 4))
    drows = []
    for x in d["大運"]:
        drows.append([
            C(f"{x['開始年齢']}歳〜", 9, PURPLE_DARK, True),
            C(x["干支"], 10, TEXT_DARK, True),
            C(x["通変星"]),
            C(x["十二運"]),
            C("○" if x["空亡"] else "", 9, GOLD, True),
            C("、".join(x["命式との関係"]) or "-", 8, TEXT_DARK, False, 'LEFT'),
        ])
    data_table(["開始年齢", "干支", "通変星", "十二運", "空亡", "命式との関係"],
               drows, [20*mm, 20*mm, 20*mm, 18*mm, 12*mm, 75*mm])

    # --------------------------------------------------------
    # 年運
    # --------------------------------------------------------
    section("年運（これからの流れ）")
    nrows = []
    for x in shichu["nenun"]:
        nrows.append([
            C(f"{x['西暦']}年", 9, PURPLE_DARK, True),
            C(x["干支"], 10, TEXT_DARK, True),
            C(x["通変星"]),
            C(x["十二運"]),
            C("○" if x["空亡"] else "", 9, GOLD, True),
            C("、".join(x["命式との関係"]) or "-", 8, TEXT_DARK, False, 'LEFT'),
        ])
    data_table(["西暦", "干支", "通変星", "十二運", "空亡", "命式との関係"],
               nrows, [18*mm, 20*mm, 20*mm, 18*mm, 12*mm, 77*mm])
    story.append(Paragraph("※ 年の切り替わりは立春基準です。空亡○の年は「手放しと充電」を意識してお過ごしください。", STYLE_NOTE))

    # --------------------------------------------------------
    # 補足: 身強身弱
    # --------------------------------------------------------
    sj = shichu["shinjaku"]
    section("補足資料: 身強身弱について")
    ne = "・".join(sj["通根"]) if sj["通根"] else "なし"
    cats = "　".join(f"{k}:{v}" for k, v in sj["勢力内訳"].items())
    story.append(Paragraph(
        f"簡易判定: <b>{sj['判定']}</b>（得令: {'○' if sj['得令'] else '×'}　"
        f"得地: {'○' if sj['得地'] else '×'}　得勢: {'○' if sj['得勢'] else '×'}）",
        STYLE_BODY))
    story.append(Paragraph(f"通根: {ne}", STYLE_BODY))
    story.append(Paragraph(f"勢力内訳: {cats}", STYLE_BODY))
    story.append(Paragraph(
        "※ 得令・得地・得勢の3条件による簡易判定です。命式全体の総合判断とは異なる場合があります。",
        STYLE_NOTE))

    # --------------------------------------------------------
    # 神殺・特殊星(巻末一覧)
    # --------------------------------------------------------
    shinsatsu = shichu.get("shinsatsu", [])
    if time_unknown:
        shinsatsu = [f for f in shinsatsu if "時柱" not in f["該当"]]
    if shinsatsu:
        section("神殺・特殊星一覧")
        srows = [[C(f["神殺"], 9, PURPLE_DARK, True), C(f["該当"]),
                  C(f.get("説明", ""), 8, TEXT_DARK, False, 'LEFT')] for f in shinsatsu]
        data_table(["星", "該当", "意味"], srows, [30*mm, 50*mm, 85*mm])

    # --------------------------------------------------------
    # 結び + フッター(セットで改ページされないよう KeepTogether)
    # --------------------------------------------------------
    story.append(KeepTogether([
        Spacer(1, 10),
        Paragraph(
            "あなたの命式は、この世でただ一つの星の配置です。"
            "その光が、これからの歩みをやさしく照らしますように。",
            S('close', 9, PURPLE_MID, False, 'CENTER', sb=4, sa=6)),
        HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER),
        Paragraph(
            "Luna 四柱推命　Luna-compass",
            S('ft', 8, TEXT_GRAY, align='CENTER', sb=4, sa=0),
        ),
    ]))

    doc.build(story)
    buf.seek(0)
    return buf


# ============================================================
# 今年の運勢 レポートPDF生成
# ============================================================
def create_kotoshi_pdf(user_data, kotoshi):
    """今年の運勢レポートPDF(軽量版)を生成する。

    user_data: {"name", "birthday", "reading_date", "gender"}
    kotoshi: {
        "year": 対象年(int, 立春基準),
        "nikkan": 日干(str),
        "nen": calc_nenun() の1年分dict,
        "current_daiun": 現在の大運dict または None,
        "getsuun": calc_getsuun() の戻り値(12ヶ月),
        "messages": {"year_star": 通変星メッセージdict, "kubo": 空亡総論str},
    }
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
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

    def message_card(title, msg):
        content = [Paragraph(title, S('p', 11, PURPLE_MID, True, sb=6, sa=10))]
        if msg:
            for line in msg.split("\n"):
                line = line.strip()
                if not line:
                    content.append(Spacer(1, 5))
                elif line.startswith("【"):
                    content.append(Paragraph(line, STYLE_H3))
                else:
                    content.append(Paragraph(line, STYLE_BODY))
        rows = [[item] for item in content]
        card = Table(rows, colWidths=[165*mm])
        card.setStyle(TableStyle([
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
        ]))
        story.append(card)
        story.append(Spacer(1, 14))

    def C(text, size=9, color=TEXT_DARK, bold=False, align='CENTER'):
        return Paragraph(text, S('cell', size, color, bold, align, sb=0, sa=0))

    year = kotoshi["year"]
    nen = kotoshi["nen"]
    nikkan = kotoshi["nikkan"]
    msgs = kotoshi.get("messages", {})

    # --------------------------------------------------------
    # タイトル + 基本情報
    # --------------------------------------------------------
    story.append(Paragraph("Luna 今年の運勢", S('t1', 16, PURPLE_DARK, True, 'CENTER', sb=4, sa=2)))
    story.append(Paragraph(f"{year}年（{nen['干支']}）運勢レポート",
                           S('t2', 11, PURPLE_MID, True, 'CENTER', sb=2, sa=4)))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=6))

    info = [[
        Paragraph("お名前", S('h', 9, PURPLE_DARK, True)),
        Paragraph(user_data.get("name", ""), S('v', 9)),
        Paragraph("生年月日", S('h', 9, PURPLE_DARK, True)),
        Paragraph(user_data.get("birthday", ""), S('v', 9)),
        Paragraph("鑑定日", S('h', 9, PURPLE_DARK, True)),
        Paragraph(user_data.get("reading_date", ""), S('v', 9)),
    ]]
    t = Table(info, colWidths=[20*mm, 35*mm, 22*mm, 38*mm, 18*mm, 32*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), PURPLE_LIGHT),
        ('BACKGROUND', (2, 0), (2, -1), PURPLE_LIGHT),
        ('BACKGROUND', (4, 0), (4, -1), PURPLE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "本レポートは四柱推命による年運・月運レポートです。年と月の切り替わりは節入り（立春など）基準です。"
        "今年一年のテーマ、いま歩んでいる大運、そして月ごとの流れを収めています。",
        STYLE_BODY))

    # --------------------------------------------------------
    # 今年のテーマ
    # --------------------------------------------------------
    section(f"{year}年　あなたの一年のテーマ")
    rel = "、".join(nen["命式との関係"]) or "大きな衝突のない穏やかな巡り"
    theme = (f"あなたの日干は<b>{nikkan}</b>。今年{year}年（{nen['干支']}）は、"
             f"<b>{nen['通変星']}</b>・<b>{nen['十二運']}</b>の一年です。")
    story.append(Paragraph(theme, STYLE_BODY))
    story.append(Paragraph(f"命式との関係: {rel}", STYLE_BODY))
    story.append(Spacer(1, 6))

    ys = msgs.get("year_star", {})
    if ys:
        message_card(f"今年の星: {ys.get('title', nen['通変星'])}", ys.get("message", ""))

    if nen["空亡"]:
        kubo_msg = msgs.get("kubo", "")
        message_card("今年は空亡（天中殺）の年です",
                     "新しく始めるより、学び直しと内面の充実に向く一年です。\n" + kubo_msg)

    # 現在の大運
    cur = kotoshi.get("current_daiun")
    if cur:
        message_card(
            f"いま歩んでいる大運: {cur['干支']}（{cur['通変星']}・{cur['十二運']}）",
            f"{cur['開始年齢']}歳からの10年は{cur['干支']}の大運です。\n"
            "今年の運気は、この大きな流れの中で巡っています。")

    # --------------------------------------------------------
    # 月ごとの流れ
    # --------------------------------------------------------
    section("月ごとの流れ")
    grows = [[Paragraph(h, S('gh', 9, colors.white, True, 'CENTER', sb=0, sa=0))
              for h in ["月", "節入り", "干支", "通変星", "十二運", "空亡", "命式との関係"]]]
    for x in kotoshi["getsuun"]:
        grows.append([
            C(f"{x['暦月目安']}({x['節月']})", 9, PURPLE_DARK, True),
            C(f"{x['節入り']}〜", 8),
            C(x["干支"], 10, TEXT_DARK, True),
            C(x["通変星"]),
            C(x["十二運"]),
            C("○" if x["空亡"] else "", 9, GOLD, True),
            C("、".join(x["命式との関係"]) or "-", 8, TEXT_DARK, False, 'LEFT'),
        ])
    gt = Table(grows, colWidths=[22*mm, 16*mm, 18*mm, 18*mm, 16*mm, 10*mm, 65*mm])
    gt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE_DARK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PURPLE_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1, PURPLE_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, PURPLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(gt)
    story.append(Paragraph(
        "※ 空亡○の月は無理をせず、整える時間に。冲・刑のある月は変化が起きやすいので、余裕を持った計画を。",
        STYLE_NOTE))

    # --------------------------------------------------------
    # 結び + フッター
    # --------------------------------------------------------
    story.append(KeepTogether([
        Spacer(1, 10),
        Paragraph(
            f"{year}年が、あなたにとって実り多き一年になりますように。",
            S('close', 9, PURPLE_MID, False, 'CENTER', sb=4, sa=6)),
        HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER),
        Paragraph("Luna 四柱推命　Luna-compass",
                  S('ft', 8, TEXT_GRAY, align='CENTER', sb=4, sa=0)),
    ]))

    doc.build(story)
    buf.seek(0)
    return buf
