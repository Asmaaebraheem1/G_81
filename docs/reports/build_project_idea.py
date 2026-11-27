# -*- coding: utf-8 -*-
"""Generate the two-page Arabic project-idea sheet (project G_81)."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "G_81-Project-Idea-AR.docx"
PROJECT_NO = "G_81"

GREEN = "1B5E20"
MID = "2E7D32"
GREY = "5F6B63"
TEXT = "263238"
LIGHT = "E8F5E9"

FONT = "Arial"

IDEA = (
    "كربونوايز منصة رقمية متكاملة تساعد الأفراد والأسر والمنظمات على قياس "
    "انبعاثاتهم الكربونية، وفهم مصادرها، ثم خفضها بخطوات عملية واضحة. يسجّل "
    "المستخدم استهلاكه من الكهرباء والوقود والرحلات والطعام والمياه والسلع، "
    "ويتولى الخادم تحويل هذه البيانات إلى كيلوجرامات من ثاني أكسيد الكربون "
    "المكافئ باستخدام معاملات انبعاث موثقة ووحدات واضحة، مع حفظ نسخة المعامل "
    "داخل كل سجل حتى لا تتغير الأرقام التاريخية عند تحديث الكتالوج. ويستطيع "
    "المستخدم مراجعة تفصيل كل حساب: الكمية والوحدة والمعامل ومصدره وتاريخ "
    "الإدخال، ثم تعديل السجل أو حذفه منطقيًا مع بقاء أثر للتدقيق. وتعرض لوحة "
    "المعلومات إجمالي البصمة وتفصيل الفئات والاتجاهات الشهرية والمقارنات، "
    "وتمكّن المستخدم من وضع أهداف للخفض وبناء خطط إجراءات وبدائل مستدامة، "
    "ومتابعة التقدم عبر التقارير. ويبدأ الاستخدام بتسجيل حساب فردي أو أسري أو "
    "منظمة، ثم إدخال أول سجل استهلاك في دقائق لتظهر النتيجة فورًا مع مقارنة "
    "بالفترة السابقة. وتضيف طبقة الذكاء الاصطناعي شرحًا وتوصيات "
    "مبنية على الأرقام المحسوبة فقط، ولا تحسب الانبعاثات ولا تخترع قيمًا من "
    "عندها. كما يضم التطبيق مساعدًا محادثًا، وتحديات وشارات ولوحة متصدرين "
    "اختيارية، ورفع فواتير مع استخراج تجريبي، وتنبيهات، ومحتوى تعليميًا. وتدير "
    "لوحة إدارة مركزية المستخدمين والمنظمات والكتالوج والمعاملات والمحتوى "
    "والبرامج والتدقيق ومراقبة الذكاء الاصطناعي. صُمم النظام ليُشغّل محليًا "
    "بسهولة، بواجهة عربية وإنجليزية كاملة تدعم الاتجاه من اليمين إلى اليسار، "
    "وبخادم يملك كل الحسابات، وبأقل اعتماد ممكن على خدمات خارجية."
)

TECHS = [
    "Flutter",
    "Dart",
    "BLoC",
    "Dio",
    "sqflite",
    "go_router",
    "flutter_secure_storage",
    "intl",
    "fl_chart",
    "shared_preferences",
    "Flask",
    "Jinja2",
    "SQLAlchemy",
    "Alembic",
    "SQLite",
    "Flask-JWT-Extended",
    "Flask-WTF",
    "flask-openapi3",
    "pydantic",
    "OpenRouter",
    "httpx",
    "Pillow",
    "pypdf",
    "pytest",
    "ruff",
    "black",
    "Git",
    "GitHub Actions",
]


def _set_cs_font(run) -> None:
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), FONT)
    rfonts.set(qn("w:hAnsi"), FONT)
    rfonts.set(qn("w:cs"), FONT)


def _set_rtl(run, rtl: bool = True) -> None:
    rpr = run._r.get_or_add_rPr()
    el = OxmlElement("w:rtl")
    el.set(qn("w:val"), "1" if rtl else "0")
    rpr.insert_element_before(
        el,
        "w:cs",
        "w:em",
        "w:lang",
        "w:eastAsianLayout",
        "w:specVanish",
        "w:oMath",
    )
    sz = rpr.find(qn("w:sz"))
    if sz is not None and rpr.find(qn("w:szCs")) is None:
        szcs = OxmlElement("w:szCs")
        szcs.set(qn("w:val"), sz.get(qn("w:val"), "28"))
        sz.addnext(szcs)
    bold = rpr.find(qn("w:b"))
    if bold is not None and rpr.find(qn("w:bCs")) is None:
        bcs = OxmlElement("w:bCs")
        bcs.set(qn("w:val"), "1")
        bold.addnext(bcs)


def _par_rtl(p) -> None:
    ppr = p._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    ppr.insert_element_before(
        bidi,
        "w:adjustRightInd",
        "w:snapToGrid",
        "w:spacing",
        "w:ind",
        "w:contextualSpacing",
        "w:mirrorIndents",
        "w:suppressOverlap",
        "w:jc",
        "w:textDirection",
        "w:textAlignment",
        "w:textboxTightWrap",
        "w:outlineLvl",
        "w:divId",
        "w:cnfStyle",
        "w:rPr",
        "w:sectPr",
        "w:pPrChange",
    )
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def _run(p, text: str, size: float, bold: bool = False, color: str = TEXT, rtl: bool = True):
    run = p.add_run(text)
    _set_cs_font(run)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)
    _set_rtl(run, rtl=rtl)
    return run


def _para(doc, *, size: float = 14, bold: bool = False, color: str = TEXT,
          before: float = 0, after: float = 0, line: float = 1.0,
          align=WD_ALIGN_PARAGRAPH.RIGHT):
    p = doc.add_paragraph()
    _par_rtl(p)
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    return p


def _rule(p, color: str = GREEN, size: int = 12) -> None:
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    ppr.insert_element_before(
        pbdr,
        "w:shd",
        "w:tabs",
        "w:suppressAutoHyphens",
        "w:kinsoku",
        "w:wordWrap",
        "w:overflowPunct",
        "w:topLinePunct",
        "w:autoSpaceDE",
        "w:autoSpaceDN",
        "w:bidi",
        "w:adjustRightInd",
        "w:snapToGrid",
        "w:spacing",
        "w:ind",
        "w:contextualSpacing",
        "w:mirrorIndents",
        "w:suppressOverlap",
        "w:jc",
        "w:textDirection",
        "w:textAlignment",
        "w:textboxTightWrap",
        "w:outlineLvl",
        "w:divId",
        "w:cnfStyle",
        "w:rPr",
        "w:sectPr",
        "w:pPrChange",
    )


def _section_rtl(section) -> None:
    sect_pr = section._sectPr
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    sect_pr.insert_element_before(
        bidi,
        "w:rtlGutter",
        "w:docGrid",
        "w:printerSettings",
        "w:sectPrChange",
    )


def _table_rtl(table) -> None:
    tbl_pr = table._tbl.tblPr
    bidi = OxmlElement("w:bidiVisual")
    tbl_pr.insert_element_before(
        bidi,
        "w:tblStyleRowBandSize",
        "w:tblStyleColBandSize",
        "w:tblW",
        "w:jc",
        "w:tblCellSpacing",
        "w:tblInd",
        "w:tblBorders",
        "w:shd",
        "w:tblLayout",
        "w:tblCellMar",
        "w:tblLook",
        "w:tblCaption",
        "w:tblDescription",
        "w:tblPrChange",
    )


def _cell_margins(cell, top: int = 55, bottom: int = 55) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    for old in tc_pr.findall(qn("w:tcMar")):
        tc_pr.remove(old)
    mar = OxmlElement("w:tcMar")
    for tag, value in (("top", top), ("bottom", bottom)):
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:w"), str(value))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tc_pr.insert_element_before(
        mar,
        "w:textDirection",
        "w:tcFitText",
        "w:vAlign",
        "w:hideMark",
        "w:headers",
        "w:cellIns",
        "w:cellDel",
        "w:cellMerge",
        "w:tcPrChange",
    )


def build() -> None:
    doc = Document()

    # Normal style: Arabic-capable font, 14 pt body.
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(14)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), FONT)
    rfonts.set(qn("w:hAnsi"), FONT)
    rfonts.set(qn("w:cs"), FONT)

    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)
    _section_rtl(section)

    # ---------------------------------------------------------------- page 1
    p = _para(doc, size=9, bold=True, color=MID, after=2)
    _run(p, "المشروع رقم: \u2066G_81\u2069", 9, bold=True, color=MID)
    _rule(p, MID, 10)

    p = _para(doc, size=33, bold=True, color=GREEN, before=30, after=2, line=1.0)
    _run(p, "فكرة المشروع", 33, bold=True, color=GREEN)

    p = _para(doc, size=14.5, bold=True, color=MID, after=18, line=1.25)
    _run(
        p,
        "منصة ذكية لتحليل الانبعاثات الكربونية والتخطيط للحد منها",
        14.5,
        bold=True,
        color=MID,
    )
    _rule(p, "C8D6CB", 8)

    p = _para(doc, size=14.5, color=TEXT, before=8, after=0, line=2.1)
    _run(p, IDEA, 14.5, color=TEXT)

    # ---------------------------------------------------------------- page 2
    doc.add_page_break()

    p = _para(doc, size=9, bold=True, color=MID, after=2)
    _run(p, "المشروع رقم: \u2066G_81\u2069", 9, bold=True, color=MID)
    _rule(p, MID, 10)

    p = _para(doc, size=30, bold=True, color=GREEN, before=25, after=14, line=1.0)
    _run(p, "التقنيات المستخدمة", 30, bold=True, color=GREEN)
    _rule(p, "C8D6CB", 8)

    rows = (len(TECHS) + 1) // 2
    table = doc.add_table(rows=rows, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _table_rtl(table)
    for col in table.columns:
        col.width = Cm(7.7)
    for i in range(rows):
        for c in range(2):
            cell = table.cell(i, c)
            cell.width = Cm(7.7)
            _cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.25
            idx = i + c * rows
            if idx < len(TECHS):
                name = "\u2066•  " + TECHS[idx] + "\u2069"
                _run(p, name, 14, color=TEXT, rtl=False)

    # python-docx writes legacy tblLook attributes that strict OOXML rejects.
    for look in table._tbl.tblPr.findall(qn("w:tblLook")):
        table._tbl.tblPr.remove(look)

    # ---------------------------------------------------------------- meta
    cp = doc.core_properties
    cp.title = "فكرة المشروع — G_81"
    cp.subject = "CarbonWise — Arabic project-idea sheet"
    cp.author = "CarbonWise / G_81"
    cp.keywords = "G_81, CarbonWise, Flutter, Flask, SQLite, OpenRouter, Arabic"
    cp.comments = "Two-page Arabic project-idea sheet; page 2 lists technology names only."

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"WROTE {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
