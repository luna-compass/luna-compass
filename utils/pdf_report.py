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

def S(name, size=10, color=TEXT_DARK, bold=False, align='LEFT', sb=4, sa=4):
    return ParagraphStyle(name, fontName='JPB' if bold else 'JP',
        fontSize=size, textColor=color,
        alignment={'LEFT':0,'CENTER':1,'RIGHT':2}.get(align,0),
        spaceBefore=sb, spaceAfter=sa, leading=size*1.7)

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

    def planet_row(symbol, label, sign, deg, house, msg):
        if not sign: return
        story.append(Paragraph(f"{symbol} {label}　{sign} {deg}　{house}ハウス",
            S('p',10,PURPLE_MID,True,sb=4,sa=2)))
        story.append(Paragraph(msg, S('m',9,TEXT_DARK,sb=0,sa=4)))

    # ASC
    section("第一印象（ASC）")
    story.append(Paragraph(f"☺ アセンダント　{user_data.get('asc_sign','')} {user_data.get('asc_deg','')}",
        S('p',10,PURPLE_MID,True,sb=4,sa=2)))
    story.append(Paragraph(user_data.get("asc_message",""), S('m',9,sb=0,sa=4)))

    # 内惑星
    section("主要天体")
    for sym, lbl, ks, kd, kh, km in [
        ("☀","太陽（本質）","sun_sign","sun_deg","sun_house","sun_message"),
        ("☽","月（感情）","moon_sign","moon_deg","moon_house","moon_message"),
        ("☿","水星（思考）","mercury_sign","mercury_deg","mercury_house","mercury_message"),
        ("♀","金星（愛・好み）","venus_sign","venus_deg","venus_house","venus_message"),
        ("♂","火星（行動）","mars_sign","mars_deg","mars_house","mars_message"),
    ]:
        planet_row(sym, lbl, user_data.get(ks,""), user_data.get(kd,""),
                   user_data.get(kh,""), user_data.get(km,""))

    # 外惑星
    section("外惑星")
    for sym, lbl, ks, kd, kh, km in [
        ("♃","木星（発展）","jupiter_sign","jupiter_deg","jupiter_house","jupiter_message"),
        ("♄","土星（課題）","saturn_sign","saturn_deg","saturn_house","saturn_message"),
        ("♅","天王星（覚醒）","uranus_sign","uranus_deg","uranus_house","uranus_message"),
        ("♆","海王星（夢）","neptune_sign","neptune_deg","neptune_house","neptune_message"),
        ("♇","冥王星（変容）","pluto_sign","pluto_deg","pluto_house","pluto_message"),
    ]:
        planet_row(sym, lbl, user_data.get(ks,""), user_data.get(kd,""),
                   user_data.get(kh,""), user_data.get(km,""))

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
    nd = [
        [Paragraph("ライフパス",S('nh',10,PURPLE_DARK,True,'CENTER')),
         Paragraph(str(user_data.get("life_path","")),S('nv',16,PURPLE_MID,True,'CENTER')),
         Paragraph("バースデー",S('nh2',10,PURPLE_DARK,True,'CENTER')),
         Paragraph(str(user_data.get("birthday_num","")),S('nv2',16,PURPLE_MID,True,'CENTER')),
         Paragraph("ルーラー",S('nh3',10,PURPLE_DARK,True,'CENTER')),
         Paragraph(str(user_data.get("ruler_num","")),S('nv3',16,PURPLE_MID,True,'CENTER'))],
    ]
    nt = Table(nd, colWidths=[28*mm,18*mm,28*mm,18*mm,25*mm,18*mm])
    nt.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'JP'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BACKGROUND',(0,0),(-1,-1),PURPLE_LIGHT),
        ('BOX',(0,0),(-1,-1),1,PURPLE_BORDER),
        ('INNERGRID',(0,0),(-1,-1),0.5,PURPLE_BORDER),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(nt)
    lp_msg = user_data.get("life_path_message","")
    if lp_msg:
        story.append(Paragraph(f"ライフパス{user_data.get('life_path','')}：{lp_msg}",
            S('lpm',9,TEXT_DARK,sb=4,sa=4)))

    # 総合メッセージ
    overall = user_data.get("overall_message","")
    if overall:
        section("総合メッセージ")
        story.append(Paragraph(overall, S('ov',10,TEXT_DARK,sb=2,sa=6)))

    # フッター
    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_BORDER))
    story.append(Paragraph("Luna 占星術　Luna-compass",
        S('ft',8,TEXT_GRAY,align='CENTER',sb=4,sa=0)))

    doc.build(story)
    buf.seek(0)
    return buf


