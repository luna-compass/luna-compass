from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

import os
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

PURPLE_DARK  = colors.HexColor("#4c1d95")
PURPLE_MID   = colors.HexColor("#7c3aed")
PURPLE_LIGHT = colors.HexColor("#f5f3ff")
PURPLE_BORDER= colors.HexColor("#a78bfa")
TEXT_DARK    = colors.HexColor("#1f1437")
TEXT_GRAY    = colors.HexColor("#6b7280")

def S(name, size=10, color=TEXT_DARK, bold=False, align='LEFT', sb=6, sa=6):
    return ParagraphStyle(name, fontName='JPB' if bold else 'JP',
        fontSize=size, textColor=color,
        alignment={'LEFT':0,'CENTER':1,'RIGHT':2}.get(align,0),
        spaceBefore=sb, spaceAfter=sa, leading=size*2.0)

def create_reading_pdf(user_data, chart_image_bytes=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=15*mm, bottomMargin=15*mm)

    story = []

    # タイトル
    story.append(Paragraph("Luna 占星術", S('t1', 20, PURPLE_DARK, True, 'CENTER', 0, 2)))
    story.append(Paragraph("ホロスコープ鑑定書", S('t2', 14, PURPLE_MID, True, 'CENTER', 0, 8)))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=8))

    # 基本情報
    info = [
        [Paragraph("お名前", S('h',10,PURPLE_DARK,True)), Paragraph(user_data.get("name",""), S('v')),
         Paragraph("鑑定日", S('h',10,PURPLE_DARK,True)), Paragraph(user_data.get("reading_date",""), S('v'))],
        [Paragraph("生年月日", S('h',10,PURPLE_DARK,True)), Paragraph(user_data.get("birthday",""), S('v')),
         Paragraph("出生時刻", S('h',10,PURPLE_DARK,True)), Paragraph(user_data.get("birth_time",""), S('v'))],
    ]
    t = Table(info, colWidths=[28*mm, 62*mm, 25*mm, 45*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'JP'),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('BACKGROUND',(0,0),(0,-1),PURPLE_LIGHT),
        ('BACKGROUND',(2,0),(2,-1),PURPLE_LIGHT),
        ('BOX',(0,0),(-1,-1),1,PURPLE_BORDER),
        ('INNERGRID',(0,0),(-1,-1),0.5,PURPLE_BORDER),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(t)
    story.append(Spacer(1,8))

    # ===== 総合メッセージ（最初に表示）=====
    overall_first = user_data.get("overall_message","")
    if overall_first:
        story.append(HRFlowable(width="100%", thickness=2, color=PURPLE_MID, spaceAfter=4))
        story.append(Paragraph("◆ あなたへの総合メッセージ", S('ov_title',13,PURPLE_DARK,True,align='CENTER',sb=4,sa=6)))
        for line in overall_first.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 3))
            elif line.startswith("【"):
                story.append(Paragraph(line, S('ovh2',10,PURPLE_MID,True,sb=4,sa=1)))
            else:
                story.append(Paragraph(line, S('ov2',10,TEXT_DARK,sb=0,sa=3)))
        story.append(Spacer(1,8))

    # ホロスコープ画像
    if chart_image_bytes:
        story.append(Paragraph("◆ 円形ホロスコープ", S('s1',12,PURPLE_DARK,True,sb=8,sa=4)))
        img = Image(chart_image_bytes, width=120*mm, height=120*mm)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1,6))

    def section(title):
        story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER, spaceBefore=6, spaceAfter=4))
        story.append(Paragraph(f"◆ {title}", S('sec',12,PURPLE_DARK,True,sb=2,sa=4)))

    def planet_row(symbol, label, sign, deg, house, msg, house_msg=""):
        if not sign: return
        story.append(Paragraph(f"{symbol} {label}　{sign} {deg}　{house}ハウス",
            S('p',10,PURPLE_MID,True,sb=4,sa=2)))
        # 改行を段落に分けて表示
        if msg:
            lines = msg.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 3))
                elif line.startswith("【"):
                    story.append(Paragraph(line, S('mh',9,PURPLE_MID,True,sb=4,sa=1)))
                else:
                    story.append(Paragraph(line, S('m',9,TEXT_DARK,sb=0,sa=2)))
        if house_msg:
            story.append(Paragraph(f"【ハウス】{house_msg}", S('hm',9,TEXT_GRAY,sb=4,sa=4)))

    # ASC
    section("第一印象（ASC）")
    story.append(Paragraph(f"☺ アセンダント　{user_data.get('asc_sign','')} {user_data.get('asc_deg','')}",
        S('p',10,PURPLE_MID,True,sb=4,sa=2)))
    asc_msg = user_data.get("asc_message","")
    if asc_msg:
        for line in asc_msg.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 3))
            elif line.startswith("【"):
                story.append(Paragraph(line, S('asch',9,PURPLE_MID,True,sb=4,sa=1)))
            else:
                story.append(Paragraph(line, S('ascm',9,TEXT_DARK,sb=0,sa=2)))

    # 内惑星
    section("主要天体")
    for sym, lbl, ks, kd, kh, km, khm in [
        ("☀","太陽（本質）","sun_sign","sun_deg","sun_house","sun_message","sun_house_message"),
        ("☽","月（感情）","moon_sign","moon_deg","moon_house","moon_message","moon_house_message"),
        ("☿","水星（思考）","mercury_sign","mercury_deg","mercury_house","mercury_message","mercury_house_message"),
        ("♀","金星（愛・好み）","venus_sign","venus_deg","venus_house","venus_message","venus_house_message"),
        ("♂","火星（行動）","mars_sign","mars_deg","mars_house","mars_message","mars_house_message"),
    ]:
        planet_row(sym, lbl, user_data.get(ks,""), user_data.get(kd,""),
                   user_data.get(kh,""), user_data.get(km,""), user_data.get(khm,""))

    # 外惑星
    section("外惑星")
    for sym, lbl, ks, kd, kh, km, khm in [
        ("♃","木星（発展）","jupiter_sign","jupiter_deg","jupiter_house","jupiter_message","jupiter_house_message"),
        ("♄","土星（課題）","saturn_sign","saturn_deg","saturn_house","saturn_message","saturn_house_message"),
        ("♅","天王星（覚醒）","uranus_sign","uranus_deg","uranus_house","uranus_message","uranus_house_message"),
        ("♆","海王星（夢）","neptune_sign","neptune_deg","neptune_house","neptune_message","neptune_house_message"),
        ("♇","冥王星（変容）","pluto_sign","pluto_deg","pluto_house","pluto_message","pluto_house_message"),
    ]:
        planet_row(sym, lbl, user_data.get(ks,""), user_data.get(kd,""),
                   user_data.get(kh,""), user_data.get(km,""), user_data.get(khm,""))

    # アスペクト
    aspects = user_data.get("aspects", [])
    if aspects:
        section("アスペクト（天体の関係性）")
        for a in aspects:
            story.append(Paragraph(
                f"◇ {a.get('p1','')} x {a.get('p2','')}：{a.get('type','')}",
                S('ap',10,PURPLE_MID,True,sb=4,sa=2)))
            story.append(Paragraph(a.get("message",""), S('am',9,sb=0,sa=4)))

    # 数秘術
    section("数秘術")

    # 3つの数字を大きく表示
    nd = [
        [Paragraph("ライフパス",S('nh',10,PURPLE_DARK,True,'CENTER')),
         Paragraph(str(user_data.get("life_path","")),S('nv',20,PURPLE_MID,True,'CENTER')),
         Paragraph("バースデー",S('nh2',10,PURPLE_DARK,True,'CENTER')),
         Paragraph(str(user_data.get("birthday_num","")),S('nv2',20,PURPLE_MID,True,'CENTER')),
         Paragraph("ルーラー",S('nh3',10,PURPLE_DARK,True,'CENTER')),
         Paragraph(str(user_data.get("ruler_num","")),S('nv3',20,PURPLE_MID,True,'CENTER'))],
    ]
    nt = Table(nd, colWidths=[28*mm,18*mm,28*mm,18*mm,25*mm,18*mm])
    nt.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'JP'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BACKGROUND',(0,0),(-1,-1),PURPLE_LIGHT),
        ('BOX',(0,0),(-1,-1),1,PURPLE_BORDER),
        ('INNERGRID',(0,0),(-1,-1),0.5,PURPLE_BORDER),
        ('TOPPADDING',(0,0),(-1,-1),10),
        ('BOTTOMPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(nt)
    story.append(Spacer(1, 8))

    # ライフパスメッセージ（充実版）
    lp_data = user_data.get("life_path_data", {})
    lp_num = user_data.get("life_path","")
    lp_msg = user_data.get("life_path_message","")

    story.append(Paragraph(f"◇ ライフパスナンバー {lp_num}　～人生のテーマ・使命～",
        S('lpth',11,PURPLE_DARK,True,sb=8,sa=4)))

    if lp_msg:
        for line in lp_msg.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1,4))
            elif line.startswith("【"):
                story.append(Paragraph(line, S('lph',10,PURPLE_MID,True,sb=6,sa=2)))
            else:
                story.append(Paragraph(line, S('lpm',9,TEXT_DARK,sb=0,sa=3)))

    story.append(Spacer(1, 6))

    # バースデーナンバー
    bd_num = user_data.get("birthday_num","")
    bd_msg = user_data.get("birthday_message","")
    if bd_msg:
        story.append(Paragraph(f"◇ バースデーナンバー {bd_num}　～生まれ持った才能～",
            S('bdth',11,PURPLE_DARK,True,sb=8,sa=4)))
        story.append(Paragraph(bd_msg, S('bdm',9,TEXT_DARK,sb=0,sa=4)))

    story.append(Spacer(1, 6))

    # ルーラーナンバー
    rl_num = user_data.get("ruler_num","")
    rl_msg = user_data.get("ruler_message","")
    if rl_msg:
        story.append(Paragraph(f"◇ ルーラーナンバー {rl_num}　～生まれた年の使命～",
            S('rlth',11,PURPLE_DARK,True,sb=8,sa=4)))
        story.append(Paragraph(rl_msg, S('rlm',9,TEXT_DARK,sb=0,sa=4)))

    # 総合メッセージは冒頭に移動したため、ここでは省略

    # タロットメッセージ（画像付き）
    tarot_data = user_data.get("tarot_message", {})
    if tarot_data and isinstance(tarot_data, dict):
        section("今日のあなたへのメッセージ 🔮")

        import os
        from PIL import Image as PILImage
        import io as _io

        card_img_path = tarot_data.get("image", "")
        card_name = tarot_data.get("name", "")
        card_position = tarot_data.get("position", "")
        card_msg = tarot_data.get("message", "")
        is_reversed = tarot_data.get("is_reversed", False)

        # カード画像を表示
        if card_img_path and os.path.exists(card_img_path):
            try:
                pil_img = PILImage.open(card_img_path).convert("RGB")
                if is_reversed:
                    pil_img = pil_img.rotate(180)
                img_buf = _io.BytesIO()
                pil_img.save(img_buf, format="PNG")
                img_buf.seek(0)
                card_image = Image(img_buf, width=40*mm, height=65*mm)
                card_image.hAlign = 'CENTER'
                story.append(card_image)
                story.append(Spacer(1, 6))
            except Exception:
                pass

        story.append(Paragraph(
            f"{card_name}（{card_position}）",
            S('tm', 12, PURPLE_MID, True, align='CENTER', sb=4, sa=4)
        ))
        if card_msg:
            story.append(Paragraph(card_msg, S('tmm', 10, TEXT_DARK, align='CENTER', sb=0, sa=6)))

    # 占い師からのメッセージ
    astrologer_msg = user_data.get("astrologer_message","")
    if astrologer_msg and astrologer_msg.strip():
        section("占い師からのメッセージ")
        for line in astrologer_msg.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
            else:
                story.append(Paragraph(line, S('am',10,TEXT_DARK,sb=0,sa=3)))

    # フッター
    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER))
    story.append(Paragraph("Luna 占星術　Luna-compass",
        S('ft',8,TEXT_GRAY,align='CENTER',sb=4,sa=0)))

    doc.build(story)
    buf.seek(0)
    return buf


