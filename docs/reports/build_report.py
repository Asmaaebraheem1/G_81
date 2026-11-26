# -*- coding: utf-8 -*-
"""Generate the Arabic CarbonWise project report (.docx)."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from lxml import etree as ET
from PIL import Image
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "CarbonWise-Project-Report-AR.docx"
OUT.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Palette and constants
# ---------------------------------------------------------------------------
GREEN = "1B5E20"
MID = "2E7D32"
LEAF = "43A047"
LIGHT = "E8F5E9"
PALE = "F4F9F5"
BORDER = "C8D6CB"
TEXT = "263238"
GREY = "5F6B63"
WHITE = "FFFFFF"

FIG_NO = 0
TABLE_NO = 0

FONT = "Arial"
MONO = "Consolas"


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------
def _set_run_rtl(run, rtl: bool = True) -> None:
    rpr = run._r.get_or_add_rPr()
    for old in rpr.findall(qn("w:rtl")):
        rpr.remove(old)
    el = OxmlElement("w:rtl")
    el.set(qn("w:val"), "1" if rtl else "0")
    rpr.append(el)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:cs"), FONT if rtl else MONO)
    sz = rpr.find(qn("w:sz"))
    if sz is not None:
        szcs = OxmlElement("w:szCs")
        szcs.set(qn("w:val"), sz.get(qn("w:val")))
        rpr.append(szcs)


def _set_par_bidi(paragraph, bidi: bool = True) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    for old in ppr.findall(qn("w:bidi")):
        ppr.remove(old)
    el = OxmlElement("w:bidi")
    el.set(qn("w:val"), "1" if bidi else "0")
    ppr.append(el)


def _style_run(run, size=11, bold=False, color=TEXT, name=FONT, italic=False, rtl=True):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), name)
    _set_run_rtl(run, rtl)
    return run


def _shade(cell, fill: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    for old in tcpr.findall(qn("w:shd")):
        tcpr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def _cell_margins(cell, top=70, bottom=70, left=100, right=100) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for side, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(value))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcpr.append(mar)


def _table_borders(table, color=BORDER, size=4) -> None:
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblpr.append(borders)


def _no_borders(table) -> None:
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblpr.append(borders)


def _repeat_header(row) -> None:
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    trpr.append(el)


def _no_split(row) -> None:
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    trpr.append(el)


def _section_rtl(section) -> None:
    sectpr = section._sectPr
    for old in sectpr.findall(qn("w:bidi")):
        sectpr.remove(old)
    el = OxmlElement("w:bidi")
    sectpr.append(el)


def _bottom_border(paragraph, color=MID, size=8, space=2) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), str(space))
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    ppr.append(pbdr)


def _field(paragraph, code: str, placeholder: str = "1") -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {code} "
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(sep)
    run._r.append(text)
    run._r.append(end)


def _hyperlink(paragraph, url: str, label: str) -> None:
    part = paragraph.part
    rid = part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rid)
    new_run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), FONT)
    rpr.append(rfonts)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), MID)
    rpr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rpr.append(u)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "20")
    rpr.append(sz)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "en-US")
    rpr.append(lang)
    new_run.append(rpr)
    t = OxmlElement("w:t")
    t.text = "\u2066" + label + "\u2069"
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


# ---------------------------------------------------------------------------
# Document-level helpers
# ---------------------------------------------------------------------------
def setup_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor.from_string(TEXT)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "en-GB")
    lang.set(qn("w:bidi"), "ar-SA")
    rpr.append(lang)
    pf = normal.paragraph_format
    pf.space_after = Pt(5)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.32

    for name, size, color in (("Heading 1", 19, GREEN), ("Heading 2", 14, MID), ("Heading 3", 12, MID)):
        st = doc.styles[name]
        st.font.name = FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)
        st.font.italic = False
        srpr = st.element.get_or_add_rPr()
        srfonts = srpr.find(qn("w:rFonts"))
        if srfonts is None:
            srfonts = OxmlElement("w:rFonts")
            srpr.insert(0, srfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs"):
            srfonts.set(qn(attr), FONT)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
        st.paragraph_format.space_after = Pt(7 if name == "Heading 1" else 4)

    # TOC styles used after Word refreshes the field.
    for name, indent in (("TOC 1", 0), ("TOC 2", 0.55)):
        try:
            st = doc.styles[name]
        except KeyError:
            continue
        st.font.name = FONT
        st.font.size = Pt(10.5 if name == "TOC 1" else 10)
        st.font.color.rgb = RGBColor.from_string(TEXT)
        st.paragraph_format.space_after = Pt(3)
        st.paragraph_format.left_indent = Cm(indent)


def page_setup(doc: Document) -> None:
    s = doc.sections[0]
    s.page_width = Cm(21)
    s.page_height = Cm(29.7)
    s.top_margin = Cm(1.9)
    s.bottom_margin = Cm(1.8)
    s.left_margin = Cm(2.2)
    s.right_margin = Cm(2.2)
    s.header_distance = Cm(0.8)
    s.footer_distance = Cm(0.8)
    _section_rtl(s)


def add_header_footer(doc: Document) -> None:
    s = doc.sections[0]
    s.different_first_page_header_footer = True

    header = s.header
    hp = header.paragraphs[0]
    hp.text = ""
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(hp)
    r = hp.add_run("CarbonWise  ·  تقرير المشروع  ·  الإصدار 1.0.0")
    _style_run(r, size=8, color=GREY)
    _bottom_border(hp, color=BORDER, size=4, space=1)
    hp.paragraph_format.space_after = Pt(2)

    footer = s.footer
    fp = footer.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(fp)
    r = fp.add_run("صفحة ")
    _style_run(r, size=8.5, color=GREY)
    _field(fp, "PAGE", "1")
    r = fp.add_run(" من ")
    _style_run(r, size=8.5, color=GREY)
    _field(fp, "NUMPAGES", "1")

    # The first-page header and footer stay empty for the cover.
    s.first_page_header.paragraphs[0].text = ""
    s.first_page_footer.paragraphs[0].text = ""


def _enable_update_fields(doc: Document) -> None:
    # `w:updateFields` must precede `w:compat` in CT_Settings.
    settings = doc.settings.element
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "1")
    compat = settings.find(qn("w:compat"))
    if compat is not None:
        compat.addprevious(update)
    else:
        settings.append(update)


# OOXML child order. Word is strict about schema order in several property
# containers; python-docx appends custom elements at the end, so we normalise
# the generated package before handing it to the user.
XML_ORDER = {
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange".split(),
    "rPr": "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath".split(),
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription".split(),
    "tcPr": "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark headers cellIns cellDel cellMerge tcPrChange".split(),
    "trPr": "cnfStyle divId gridBefore gridAfter wBefore wAfter cantSplit trHeight tblHeader tblCellSpacing jc hidden ins del trPrChange".split(),
    "sectPr": "headerReference footerReference footnotePr endnotePr type pgSz pgMar paperSrc pgBorders lnNumType pgNumType cols formProt vAlign noEndnote titlePg textDirection bidi rtlGutter docGrid printerSettings sectPrChange".split(),
}
XML_ORDER = {k: {name: i for i, name in enumerate(v)} for k, v in XML_ORDER.items()}


def _normalise_tree(root) -> bool:
    changed = False
    for parent in list(root.iter()):
        if not isinstance(parent.tag, str):
            continue
        local = parent.tag.rsplit("}", 1)[-1]
        if local == "tblPr":
            for look in parent.findall(qn("w:tblLook")):
                parent.remove(look)
                changed = True
        order = XML_ORDER.get(local)
        if not order:
            continue
        children = list(parent)
        indexed = []
        for pos, child in enumerate(children):
            if not isinstance(child.tag, str):
                indexed.append((len(order), pos, child))
            else:
                cl = child.tag.rsplit("}", 1)[-1]
                indexed.append((order.get(cl, len(order)), pos, child))
        ordered = [c for _, _, c in sorted(indexed, key=lambda item: (item[0], item[1]))]
        if ordered != children:
            for child in children:
                parent.remove(child)
            for child in ordered:
                parent.append(child)
            changed = True
    return changed


def normalise_package(path: Path) -> None:
    tmp = path.with_name(path.stem + ".tmp.docx")
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml") and not item.filename.startswith("word/media/"):
                try:
                    root = ET.fromstring(data)
                    if _normalise_tree(root):
                        data = ET.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                except ET.XMLSyntaxError:
                    pass
            zout.writestr(item, data)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Content helpers
# ---------------------------------------------------------------------------
def h1(doc, text: str, page_break: bool = True) -> None:
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.page_break_before = page_break
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    r = p.add_run(text)
    _style_run(r, size=19, bold=True, color=GREEN)
    _bottom_border(p, color=MID, size=10, space=3)


def h2(doc, text: str) -> None:
    p = doc.add_paragraph(style="Heading 2")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    r = p.add_run(text)
    _style_run(r, size=14, bold=True, color=MID)


def h3(doc, text: str) -> None:
    p = doc.add_paragraph(style="Heading 3")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    r = p.add_run(text)
    _style_run(r, size=12, bold=True, color=MID)


def body(doc, text: str, size=11, color=TEXT, after=5, align=WD_ALIGN_PARAGRAPH.JUSTIFY, italic=False):
    p = doc.add_paragraph()
    p.alignment = align
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.32
    r = p.add_run(text)
    _style_run(r, size=size, color=color, italic=italic)
    return p


def lead(doc, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    _style_run(r, size=12.5, color=MID)
    p.paragraph_format.line_spacing = 1.35


def bullet(doc, text: str, level=0, size=10.5) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.28
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.right_indent = Cm(0.45 + level * 0.55)
    r = p.add_run(text)
    _style_run(r, size=size, color=TEXT)


def numbered(doc, number: int, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.3
    r = p.add_run(f"{number}.  ")
    _style_run(r, size=11, bold=True, color=MID)
    r = p.add_run(text)
    _style_run(r, size=10.5, color=TEXT)


def caption(doc, text: str, kind="شكل") -> None:
    global FIG_NO
    FIG_NO += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(p)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f"{kind} {FIG_NO}: {text}")
    _style_run(r, size=8.5, color=GREY, italic=True)


def table_caption(doc, text: str) -> None:
    global TABLE_NO
    TABLE_NO += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(f"جدول {TABLE_NO}: {text}")
    _style_run(r, size=9, bold=True, color=MID)


def _fill_cell(cell, value, size=9, bold=False, color=TEXT, align=WD_ALIGN_PARAGRAPH.RIGHT, ltr=False):
    value = str(value)
    if value.strip() and any(ch.isalnum() for ch in value) and not any("\u0600" <= ch <= "\u06ff" for ch in value):
        value = "\u2066" + value + "\u2069"
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    _set_par_bidi(p, not ltr)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.12
    r = p.add_run(str(value))
    _style_run(r, size=size, bold=bold, color=color, rtl=not ltr)


def table(doc, headers, rows, widths, caption_text=None, size=9, ltr_cols=(), first_col_bold=False):
    if caption_text:
        table_caption(doc, caption_text)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblpr = t._tbl.tblPr
    bidi = OxmlElement("w:bidiVisual")
    tblpr.append(bidi)
    _table_borders(t)

    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    hdr = t.rows[0]
    _repeat_header(hdr)
    _no_split(hdr)
    for i, htext in enumerate(headers):
        c = hdr.cells[i]
        c.width = Cm(widths[i])
        _shade(c, GREEN)
        _cell_margins(c)
        _fill_cell(c, htext, size=size, bold=True, color=WHITE, align=WD_ALIGN_PARAGRAPH.CENTER, ltr=False)

    for ridx, row in enumerate(rows):
        r = t.add_row()
        _no_split(r)
        for i, value in enumerate(row):
            c = r.cells[i]
            c.width = Cm(widths[i])
            if ridx % 2 == 1:
                _shade(c, PALE)
            _cell_margins(c)
            _fill_cell(
                c,
                value,
                size=size,
                bold=(first_col_bold and i == 0),
                color=TEXT,
                align=WD_ALIGN_PARAGRAPH.CENTER if i in ltr_cols else WD_ALIGN_PARAGRAPH.RIGHT,
                ltr=i in ltr_cols,
            )
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    return t


def callout(doc, title: str, text: str, fill=LIGHT, bar=MID) -> None:
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.columns[0].width = Cm(16.2)
    c = t.rows[0].cells[0]
    c.width = Cm(16.2)
    _shade(c, fill)
    _cell_margins(c, top=120, bottom=120, left=180, right=180)
    _no_borders(t)
    tcpr = c._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    right = OxmlElement("w:right")
    right.set(qn("w:val"), "single")
    right.set(qn("w:sz"), "18")
    right.set(qn("w:color"), bar)
    borders.append(right)
    tcpr.append(borders)
    _no_split(t.rows[0])
    c.text = ""
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    _style_run(r, size=10.5, bold=True, color=GREEN)
    p2 = c.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _set_par_bidi(p2)
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = 1.25
    r = p2.add_run(text)
    _style_run(r, size=9.5, color=TEXT)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def code_block(doc, lines) -> None:
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.columns[0].width = Cm(16.0)
    c = t.rows[0].cells[0]
    c.width = Cm(16.0)
    _shade(c, "F6F8F6")
    _cell_margins(c, top=110, bottom=110, left=160, right=160)
    _no_borders(t)
    _no_split(t.rows[0])
    c.text = ""
    first = True
    for line in lines:
        p = c.paragraphs[0] if first else c.add_paragraph()
        first = False
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        _set_par_bidi(p, False)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        r = p.add_run("\u202A" + line + "\u202C")
        _style_run(r, size=8.5, color=TEXT, name=MONO, rtl=False)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figure(doc, path: Path, cap: str, max_w=16.0, max_h=10.0) -> None:
    w, h = Image.open(path).size
    aspect = w / h
    if max_w / max_h > aspect:
        height = max_h
        width = height * aspect
    else:
        width = max_w
        height = width / aspect
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width), height=Cm(height))
    caption(doc, cap)


def landscape(doc) -> None:
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width = Cm(29.7)
    s.page_height = Cm(21.0)
    s.top_margin = Cm(1.45)
    s.bottom_margin = Cm(1.45)
    s.left_margin = Cm(1.8)
    s.right_margin = Cm(1.8)
    s.different_first_page_header_footer = False
    _section_rtl(s)


def portrait(doc) -> None:
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.PORTRAIT
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.top_margin = Cm(1.9)
    s.bottom_margin = Cm(1.8)
    s.left_margin = Cm(2.2)
    s.right_margin = Cm(2.2)
    s.different_first_page_header_footer = False
    _section_rtl(s)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build() -> None:
    doc = Document()
    setup_styles(doc)
    page_setup(doc)
    add_header_footer(doc)
    _enable_update_fields(doc)

    cp = doc.core_properties
    cp.title = "CarbonWise — تقرير المشروع بالعربية"
    cp.subject = "فكرة المشروع، التفاصيل، والتقنيات المستخدمة"
    cp.author = "CarbonWise project"
    cp.keywords = "CarbonWise, Flutter, Flask, SQLite, OpenRouter, sustainability, Arabic, RTL"
    cp.language = "ar-SA"
    cp.comments = "تقرير مشروع CarbonWise الإصدار 1.0.0 — نوفمبر 2026"

    # ------------------------------------------------------------------
    # COVER
    # ------------------------------------------------------------------
    band = doc.add_table(rows=1, cols=1)
    band.alignment = WD_TABLE_ALIGNMENT.CENTER
    band.autofit = False
    band.columns[0].width = Cm(16.4)
    c = band.rows[0].cells[0]
    c.width = Cm(16.4)
    _shade(c, GREEN)
    _no_borders(band)
    _cell_margins(c, top=150, bottom=150, left=220, right=220)
    c.text = ""
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("تقرير مشروع  ·  الإصدار 1.0.0  ·  نوفمبر 2026")
    _style_run(r, size=9.5, bold=True, color=WHITE)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(26)
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("CarbonWise")
    _style_run(r, size=38, bold=True, color=GREEN, rtl=False)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(p)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("منصة ذكية لتحليل الانبعاثات الكربونية")
    _style_run(r, size=23, bold=True, color=GREEN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(12)
    r = p.add_run("والتخطيط للحد منها بالذكاء الاصطناعي")
    _style_run(r, size=23, bold=True, color=GREEN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run("فكرة المشروع  ·  التفاصيل  ·  التقنيات المستخدمة ووظيفة كل تقنية")
    _style_run(r, size=11.5, color=GREY)

    hero = ROOT / "mobile" / "assets" / "images" / "hero-renewable-energy.webp"
    hero_png = Path(tempfile.gettempdir()) / "cw_report_hero.png"
    Image.open(hero).convert("RGB").save(hero_png, "PNG")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    p.add_run().add_picture(str(hero_png), width=Cm(15.5))

    facts = [
        ("نوع المشروع", "منصة ويب + تطبيق أندرويد للاستدامة"),
        ("المستخدمون", "أفراد وأسر ومنظمات + إدارة المنصة"),
        ("التقنيات الأساسية", "Flutter · Flask · SQLite · OpenRouter"),
        ("حالة الإصدار", "مكتمل ومُختبر — الإصدار 1.0.0"),
    ]
    t = doc.add_table(rows=4, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.columns[0].width = Cm(5.0)
    t.columns[1].width = Cm(11.2)
    _no_borders(t)
    for i, (k, v) in enumerate(facts):
        for j, value in enumerate((k, v)):
            cell = t.rows[i].cells[j]
            cell.width = Cm(5.0 if j == 0 else 11.2)
            _cell_margins(cell, top=70, bottom=70)
            _shade(cell, LIGHT if j == 0 else PALE)
            _fill_cell(cell, value, size=9, bold=(j == 0), color=GREEN if j == 0 else TEXT)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run("github.com/Asmaaebraheem1/G_81  ·  الإصدار v1.0.0")
    _style_run(r, size=8.5, color=GREY, rtl=False)

    # ------------------------------------------------------------------
    # TOC
    # ------------------------------------------------------------------
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("محتويات التقرير")
    _style_run(r, size=22, bold=True, color=GREEN)
    _bottom_border(p, color=MID, size=10, space=3)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run("يُحدَّث الفهرس تلقائيًا عند فتح الملف في Microsoft Word. إذا ظهر فارغًا: اضغط عليه ثم F9 ثم اختر «تحديث الحقل بالكامل».")
    _style_run(r, size=8.8, color=GREY, italic=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r' TOC \o "1-2" \h \z \u '
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = "سيظهر فهرس الأقسام هنا بعد التحديث."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(sep)
    run._r.append(t)
    run._r.append(end)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_par_bidi(p)
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run("خريطة سريعة: ")
    _style_run(r, size=9.5, bold=True, color=MID)
    r = p.add_run("الفصول 1–5 تشرح الفكرة والمستخدمين والميزات؛ الفصل 6 يعرض المخططات؛ الفصل 7 هو جدول التقنيات واستخداماتها؛ الفصول 8–12 تشرح المعمارية والذكاء الاصطناعي والبيانات والأمان والجودة؛ الفصول 13–16 التشغيل والمخرجات والقيود والخلاصة.")
    _style_run(r, size=9.5, color=TEXT)

    # ------------------------------------------------------------------
    # EXECUTIVE SUMMARY
    # ------------------------------------------------------------------
    h1(doc, "ملخص تنفيذي")
    lead(doc, "CarbonWise منصة تجمع بين تطبيق أندرويد ثنائي اللغة، وواجهة برمجية مركزية، ولوحة إدارة، وطبقة ذكاء اصطناعي محكومة. اسمها يجمع بين «الكربون» و«الحكمة»: أن يفهم المستخدم أثر أنشطته اليومية، ثم يتحرك بناءً على أرقام واضحة لا على تخمين.")

    body(doc, "المشكلة التي يعالجها المشروع أن أغلب الناس لا يعرفون أي الأنشطة اليومية تُنتج أكبر قدر من الانبعاثات، كما أن النصائح العامة عن الاستدامة يصعب تحويلها إلى خطوات قابلة للقياس. الحل هو مسار واحد بسيط: يسجّل المستخدم استهلاكه ← يحسب الخادم الانبعاثات من معاملات موثقة ← يعرض التطبيق لوحة وتقارير ← يستخدم الذكاء الاصطناعي لشرح النتائج واقتراح خطة ← يتابع المستخدم التقدم عبر أهداف وتحديات.")

    callout(
        doc,
        "المبدأ الحاكم: الذكاء الاصطناعي يشرح ولا يحسب",
        "كل قيمة انبعاث تُحسب في الخادم من كمية الاستهلاك ومعامل الانبعاث، ثم تُخزَّن مع نسخة من المعامل. الذكاء الاصطناعي يستقبل هذه القيم المحسوبة مسبقًا، ولا يملك صلاحية اختراع رقم أو تعديله أو الكتابة في قاعدة البيانات.",
    )

    table(
        doc,
        ["البُعد", "الخلاصة"],
        [
            ("المستخدمون", "زائر، مستخدم فرد/أسرة، مستخدم منظمة، مدير منصة، محرر محتوى."),
            ("التطبيق", "Flutter للأندرويد، واجهة إنجليزية وعربية مع دعم كامل لاتجاه RTL."),
            ("الخادم", "Flask API بإصدار /api/v1، مصادقة JWT، ولوحة إدارة Jinja2 بجلسات وCSRF."),
            ("البيانات", "SQLite فقط: 29 جدولًا، ترحيلات Alembic، ونسخة تجريبية ثابتة."),
            ("الذكاء الاصطناعي", "OpenRouter بنموذج openrouter/free فقط، من الخادم، مع تحقق من المخرجات وحدود استخدام وبدائل حتمية."),
            ("الإنجاز", "15 ميزة مكتملة، 134 مسار API، 82 لقطة شاشة، 5 مخططات، و15 رسمًا أصليًا."),
        ],
        [4.0, 12.0],
        caption_text="بطاقة تعريف المشروع",
        size=9.3,
        first_col_bold=True,
    )

    table(
        doc,
        ["المؤشر", "النتيجة", "الدلالة"],
        [
            ("اختبارات الخادم", "54 ناجحة", "تغطية 76.22% (الحد الأدنى 50%)."),
            ("اختبارات التطبيق", "23 ناجحة", "تغطية 92.16% من الأسطر."),
            ("تحليل Flutter", "0 ملاحظات", "لا أخطاء ولا تحذيرات في الكود."),
            ("Ruff + Black", "نظيفان", "أسلوب وتنسيق Python متسقان."),
            ("توازن الترجمة", "310 / 310", "مفتاح إنجليزي مقابل مفتاح عربي؛ لا فجوات."),
            ("فحص الدخان", "21/21", "فحص سريع لواجهات API والإدارة."),
        ],
        [4.0, 3.6, 8.4],
        caption_text="أبرز أرقام التحقق",
        size=9,
        ltr_cols=(1,),
    )

    # ------------------------------------------------------------------
    # 1. IDEA
    # ------------------------------------------------------------------
    h1(doc, "1. فكرة المشروع")
    h2(doc, "1.1 ما هو CarbonWise؟")
    body(doc, "CarbonWise منصة تحليل انبعاثات كربونية وتخطيط للخفض، موجّهة للأفراد والأسر والمنظمات. يقوم المستخدم بتسجيل بيانات الاستهلاك — كهرباء، وقود، رحلات، ماء، نفايات، طعام، مشتريات — ويحوّلها الخادم إلى كيلوجرامات مكافئ ثاني أكسيد الكربون (kg CO2e) باستخدام معاملات انبعاث موثقة وقابلة للتحديث من لوحة الإدارة. بعد ذلك يحوّل التطبيق الأرقام إلى لوحة معلومات وتقارير وأهداف وخطط خفض وتحديات، ويستخدم طبقة ذكاء اصطناعي محكومة لشرح النتائج واقتراح خطوات عملية.")

    body(doc, "الفكرة ليست مجرد «حاسبة كربون». القيمة الحقيقية هي حلقة متكاملة: قياس شفاف ← فهم سبب الانبعاث ← خطة قابلة للتنفيذ ← متابعة التقدم ← تحفيز عبر التحديات والإنجازات. وكل خطوة تحافظ على فصل واضح بين الحساب الذي يملكه الخادم والتفسير الذي يقدمه الذكاء الاصطناعي.")

    h2(doc, "1.2 المشكلة")
    for item in [
        "الانبعاثات غير مرئية: يصعب على الشخص العادي ربط فاتورة الكهرباء أو رحلة السيارة برقم كربوني مفهوم.",
        "المعلومات مشتتة: بيانات الاستهلاك موزعة بين فواتير وصور وتطبيقات، ولا توجد صورة موحدة عبر الفترات.",
        "النصيحة عامة: «قلل الطاقة» أو «استخدم المواصلات العامة» لا تخبر المستخدم كم سيوفر، ولا من أين يبدأ.",
        "غياب المتابعة: حتى من يبدأ بتغيير سلوكه لا يجد أداة تقيس التقدم وتحافظ على الاستمرارية.",
        "الثقة في الذكاء الاصطناعي: المخاوف من أرقام مخترعة أو خصوصية البيانات أو إرسال مفاتيح API إلى التطبيق.",
    ]:
        bullet(doc, item)

    h2(doc, "1.3 الحل في خمس ركائز")
    table(
        doc,
        ["الركيزة", "التطبيق العملي في CarbonWise"],
        [
            ("قياس شفاف", "كل سجل يوضح الكمية والوحدة والمعامل المستخدم والمصدر ومعادلة الحساب؛ ولا تُعاد كتابة تاريخ السجلات عند تغيير المعامل."),
            ("فهم شخصي", "لوحة معلومات وتقارير شهرية/سنوية، تفصيل بالفئة، وأعلى الأنشطة تأثيرًا، ومقارنات بين الفترات."),
            ("تخطيط قابل للتنفيذ", "أهداف بنسبة خفض، خطط مقسمة إلى إجراءات، بدائل مستدامة بتأثير محسوب، وتقدم مرئي."),
            ("تحفيز مستمر", "تحديات جماعية، نقاط، شارات، ولوحة متصدرين اختيارية تحترم الخصوصية."),
            ("ذكاء اصطناعي مسؤول", "مساعد ورؤى وخطط واستخراج تجريبي من الفواتير، مع منع الأرقام المخترعة، وتحرير البيانات الشخصية، وحدود استخدام، وبديل حتمي عند تعذر الخدمة."),
        ],
        [3.7, 12.3],
        caption_text="ركائز الفكرة",
        size=9.3,
        first_col_bold=True,
    )

    h2(doc, "1.4 مثال يوضح الفكرة")
    body(doc, "تسجّل «سارة» استهلاك الكهرباء الشهري: 250 كيلوواط·ساعة. يختار التطبيق معامل الشبكة الافتراضي 233 جرامًا لكل كيلوواط·ساعة، فيحسب الخادم 58,250 جرامًا، أي 58.25 كجم CO2e. تعرض الشاشة التفصيل: الكمية × المعامل = الناتج، ومصدر المعامل. يسأل المساعد الذكي: «أين أكبر فرصة للخفض؟» فيستقبل سياقًا محسوبًا مسبقًا ويشرح أن الكهرباء أكبر مصدر، ثم يقترح خطوات مثل ضبط التكييف واستبدال الإضاءة، دون أن يغيّر قيمة 58.25 أو يخترع نسبة توفير من عنده.")

    h2(doc, "1.5 لماذا هذا المشروع؟")
    body(doc, "يجمع المشروع بين ثلاثة مجالات مطلوبة في سوق العمل: تطوير تطبيقات موبايل حديثة، بناء واجهات برمجية آمنة وقابلة للاختبار، وتوظيف الذكاء الاصطناعي بشكل مسؤول فوق بيانات محسوبة. كما أنه يلامس هدفًا عالميًا واضحًا — خفض الانبعاثات — ويقدم تجربة ثنائية اللغة (إنجليزية/عربية) تصلح للعرض الأكاديمي والاستخدام المحلي.")

    # ------------------------------------------------------------------
    # 2. OBJECTIVES & SCOPE
    # ------------------------------------------------------------------
    h1(doc, "2. الأهداف والنطاق")
    h2(doc, "2.1 الهدف العام")
    body(doc, "بناء منصة متكاملة وقابلة للتشغيل محليًا تُمكّن المستخدم من قياس انبعاثاته وفهمها وخفضها، وتُمكّن الإدارة من إدارة الكتالوج والمعاملات والمحتوى والمستخدمين ومراقبة استخدام الذكاء الاصطناعي، مع الالتزام بقيود صارمة في التقنيات والخصوصية.")

    h2(doc, "2.2 الأهداف التفصيلية")
    for i, item in enumerate([
        "تسجيل الاستهلاك بفئات ووحدات ومعاملات واضحة، وحساب الانبعاثات على الخادم فقط.",
        "توفير لوحة معلومات وتقارير قابلة للتصفية والتصدير بصيغة CSV.",
        "دعم أهداف الخفض وخطط الإجراءات والبدائل المستدامة ومتابعة التقدم.",
        "تقديم خمس وظائف ذكاء اصطناعي مفيدة مع منع الأرقام المخترعة وضمان قابلية التراجع.",
        "توفير تجربة عربية كاملة RTL بجانب الإنجليزية، مع تنسيق تواريخ وأرقام مناسب.",
        "توفير لوحة إدارة محمية بجلسات وCSRF لإدارة المنصة والتدقيق.",
        "تحقيق جودة قابلة للقياس: اختبارات، تغطية، تحليل ثابت، CI، وتوثيق كامل.",
        "إنتاج حزمة تسليم: مخططات، لقطات شاشة، أصول بصرية، تقرير عربي، ونسخة APK.",
    ], 1):
        numbered(doc, i, item)

    h2(doc, "2.3 داخل النطاق")
    table(
        doc,
        ["المحور", "ما الذي يشمله؟"],
        [
            ("الحسابات", "تسجيل ودخول، ملف فرد/أسرة/منظمة، تفضيلات، تغيير كلمة المرور، حذف/تعطيل آمن."),
            ("الكتالوج", "فئات انبعاث، معاملات بوحدات ومناطق ومصادر، تفعيل/تعطيل، ونسخ تاريخية داخل السجلات."),
            ("السجلات", "إنشاء/تعديل/حذف منطقي، بحث وتصفية، حساب فوري، وعرض المعادلة والمصدر."),
            ("المستندات", "رفع فاتورة/إيصال، تحقق، تخزين خاص، استخراج تجريبي بالذكاء الاصطناعي، وتأكيد المستخدم."),
            ("التقارير", "لوحة، اتجاهات، مقارنات، تفصيل فئات، أعلى الأنشطة، تصدير CSV."),
            ("الخطط", "أهداف، خطط خفض، إجراءات، بدائل، موافقة/رفض، وتقدم."),
            ("التفاعل", "تحديات، نقاط، شارات، لوحة متصدرين اختيارية، إشعارات وتفضيلات."),
            ("الإدارة", "مستخدمون، منظمات، كتالوج، سجلات، مستندات، خطط، تقارير، تحديات، محتوى، إعدادات، تدقيق، مراقبة AI."),
        ],
        [3.5, 12.5],
        caption_text="نطاق الإصدار الأول",
        size=9.1,
        first_col_bold=True,
    )

    h2(doc, "2.4 خارج النطاق")
    body(doc, "بشكل مقصود، لا يتضمن الإصدار الأول: المدفوعات أو الاشتراكات، iOS أو سطح المكتب أو الويب، تدريب نموذج ذكاء اصطناعي خاص، ضمان استخراج OCR لكل المستندات، سوق تعويضات كربونية، تكامل عدادات ذكية، أو نشر سحابي متعدد المستأجرين. هذه الخيارات موثقة كأعمال مستقبلية وليست نواقص خفية.")

    # ------------------------------------------------------------------
    # 3. USERS & JOURNEYS
    # ------------------------------------------------------------------
    h1(doc, "3. المستخدمون والرحلات")
    h2(doc, "3.1 الأدوار")
    table(
        doc,
        ["الدور", "الهدف", "طريقة الدخول"],
        [
            ("زائر", "تصفح المحتوى التعليمي، تبديل اللغة، فهم المنتج، التسجيل أو الدخول.", "بدون مصادقة"),
            ("مستخدم فرد/أسرة", "تسجيل الاستهلاك، رؤية التقارير، وضع أهداف، استخدام المساعد، المشاركة في التحديات.", "JWT: access + refresh"),
            ("مستخدم منظمة", "نفس القدرات مرتبطة بملف منظمة وسجلاتها ومشاركة التقارير.", "JWT"),
            ("مدير المنصة", "إدارة المستخدمين والكتالوج والمحتوى والبرامج ومراقبة AI والتدقيق.", "جلسة كوكي موقعة + CSRF"),
            ("محرر محتوى", "إدارة المقالات والتحديات، وقراءة بقية الصفحات دون تعديل.", "جلسة كوكي + CSRF"),
            ("OpenRouter", "مزوّد خارجي للذكاء الاصطناعي؛ يستقبل طلبًا منقّحًا ويعيد نصًا، وليس فاعلًا بشريًا.", "مفتاح من الخادم فقط"),
        ],
        [3.0, 10.2, 3.4],
        caption_text="أدوار النظام",
        size=8.8,
        first_col_bold=True,
    )

    h2(doc, "3.2 الرحلات الرئيسية")
    table(
        doc,
        ["الرحلة", "المسار المختصر", "القيمة"],
        [
            ("البصمة الأولى", "تسجيل ← اختيار نوع الحساب ← إكمال الملف ← إضافة كهرباء ونقل ونفايات ← لوحة وتفصيل المعادلة.", "أول فهم ملموس للبصمة."),
            ("من الفاتورة إلى سجل", "رفع صورة ← موافقة على الإرسال ← استخراج تجريبي ← مراجعة المستخدم ← حساب الخادم ← تحديث اللوحة.", "تقليل إدخال البيانات اليدوي."),
            ("الفهم والخفض", "تقرير ← مساعد/رؤى ← هدف بنسبة ← خطة إجراءات ← متابعة التقدم.", "تحويل الأرقام إلى خطة."),
            ("اختيار بديل", "تصفح البدائل ← تصفية حسب الفئة والأثر ← حفظ/اعتماد ← إضافة إلى خطة.", "قرار مدعوم بتأثير محسوب."),
            ("الاستمرارية", "تحدي ← انضمام ← إنجاز نشاط ← نقاط وشارة ← إشعار ← لوحة متصدرين اختيارية.", "تحفيز ومشاركة."),
            ("إدارة المنصة", "دخول الإدارة ← مؤشرات ← إدارة/مراجعة ← تعديل معامل أو محتوى ← تدقيق وتصدير.", "تشغيل ورقابة."),
        ],
        [3.0, 9.8, 3.8],
        caption_text="رحلات المستخدم والإدارة",
        size=8.8,
        first_col_bold=True,
    )

    # ------------------------------------------------------------------
    # 4. FEATURES
    # ------------------------------------------------------------------
    h1(doc, "4. الميزات الرئيسية")
    body(doc, "تم تنظيم المشروع في 15 ميزة (F01–F15). الميزات F01–F12 تظهر في التطبيق، وبعضها له سطح إداري؛ أما F13–F15 فهي إدارية بالكامل ولا تملك مسارات API عامة.")

    table(
        doc,
        ["#", "الميزة", "ماذا تفعل؟", "القيمة للمستخدم"],
        [
            ("F01", "الحسابات والملفات والتفضيلات", "تسجيل ودخول وتجديد جلسة، ملف فرد/أسرة/منظمة، لغة ومنطقة زمنية، تفضيلات الخصوصية.", "حساب شخصي آمن ومخصص."),
            ("F02", "فئات الانبعاثات ومعاملاتها", "كتالوج فئات ومعاملات بوحدات ومناطق ومصادر وتواريخ صلاحية.", "حساب موثق وقابل للتفسير."),
            ("F03", "سجلات الاستهلاك والحساب", "إدخال كمية ووحدة وتاريخ، اختيار معامل، حساب فوري، وتخزين لقطة من المعامل.", "تتبع يومي دقيق."),
            ("F04", "رفع الفواتير والاستخراج", "رفع صورة/PDF، موافقة، استخراج تجريبي بالذكاء الاصطناعي، ثم تأكيد يدوي قبل الحفظ.", "إدخال أسرع مع تحكم كامل."),
            ("F05", "لوحة المعلومات والتقارير", "إجماليات وفترات واتجاهات وتفصيل فئات وأعلى الأنشطة وتصدير CSV.", "رؤية واضحة للبصمة."),
            ("F06", "أهداف الاستدامة", "هدف نسبة خفض وفترة وحالة وتقدم مرتبط بالبصمة.", "هدف قابل للقياس."),
            ("F07", "المساعد الذكي", "محادثة عربية/إنجليزية بسياق محسوب مسبقًا، مع اقتراحات وحدود استخدام.", "إجابات مفسرة وليست أرقامًا."),
            ("F08", "الرؤى والملخصات", "تحليل أفضل المصادر والاتجاهات والفرص، مع ملخص قابل للتحديث.", "اكتشاف الفرص بسرعة."),
            ("F09", "خطط الخفض", "توليد خطة منظمة إلى إجراءات، اعتماد/رفض، وتقدم.", "خطة عملية بدل نصائح عامة."),
            ("F10", "البدائل المستدامة", "كتالوج بدائل مع تقدير أثر وتصفية وحفظ وإضافة إلى خطة.", "قرارات أفضل موثقة."),
            ("F11", "التحديات والإنجازات", "تحديات ونقاط وشارات ولوحة متصدرين اختيارية.", "استمرارية وتحفيز."),
            ("F12", "الإشعارات والتذكيرات", "صندوق إشعارات وتفضيلات وتذكيرات.", "متابعة دون إزعاج."),
        ],
        [1.1, 4.0, 8.5, 3.0],
        caption_text="ميزات التطبيق والمنصة (F01–F12)",
        size=8.4,
        ltr_cols=(0,),
    )

    table(
        doc,
        ["#", "الميزة الإدارية", "ماذا تفعل؟"],
        [
            ("F13", "إدارة المستخدمين والمنظمات", "بحث وعرض وتفعيل/تعليق وإعادة تعيين كلمة مرور، وبيانات المنظمات وحالتها."),
            ("F14", "إدارة الكتالوج والسجلات والمستندات", "إدارة الفئات والمعاملات، مراجعة السجلات وتفصيل الحساب، وتنزيل المستندات المحمية."),
            ("F15", "البرامج والمحتوى والتحليلات وAI", "تحديات وشارات وإشعارات ومقالات وCSV وإعدادات وتدقيق ومراقبة استخدام الذكاء الاصطناعي."),
        ],
        [1.2, 5.0, 10.0],
        caption_text="الميزات الإدارية (F13–F15)",
        size=8.8,
        ltr_cols=(0,),
    )

    doc.add_page_break()
    h2(doc, "4.1 لمحة بصرية")
    body(doc, "هذه لقطات من التطبيق ولوحة الإدارة أثناء الاختبار. واجهة التطبيق متاحة بالإنجليزية والعربية، مع قلب التخطيط إلى RTL وتثبيت الأرقام والمعادلات والوحدات في اتجاه LTR داخل النص العربي.")
    phone_files = [
        (ROOT / "docs" / "screenshots" / "mobile-en-03-dashboard.png", "لوحة المعلومات — EN"),
        (ROOT / "docs" / "screenshots" / "mobile-ar-03-dashboard.png", "لوحة المعلومات — AR"),
        (ROOT / "docs" / "screenshots" / "mobile-ar-04-records.png", "سجلات الاستهلاك — AR"),
    ]
    t = doc.add_table(rows=1, cols=3)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _no_borders(t)
    for i, (path, label) in enumerate(phone_files):
        c = t.rows[0].cells[i]
        c.width = Cm(5.1)
        _cell_margins(c, top=40, bottom=40)
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        p.add_run().add_picture(str(path), width=Cm(4.4))
        p2 = c.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_par_bidi(p2)
        p2.paragraph_format.space_after = Pt(1)
        r = p2.add_run(label)
        _style_run(r, size=7.5, color=GREY)
    caption(doc, "ثلاث شاشات من التطبيق: اللوحة الإنجليزية، اللوحة العربية RTL، وقائمة السجلات العربية")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(ROOT / "docs" / "screenshots" / "admin-02-dashboard.png"), width=Cm(15.8))
    caption(doc, "لوحة إدارة المنصة — مؤشرات المستخدمين والانبعاثات والنشاط (Jinja2)")

    # ------------------------------------------------------------------
    # 5. HOW IT WORKS
    # ------------------------------------------------------------------
    h1(doc, "5. كيف يعمل النظام؟")
    h2(doc, "5.1 المسار من الإدخال إلى الرؤية")
    for i, item in enumerate([
        "يفتح المستخدم التطبيق، فيتحقق من الجلسة المحفوظة ويوجّهه الموجّه (go_router) إلى الشاشة المناسبة.",
        "يسجّل الدخول عبر /api/v1/auth/login، فيحصل على access token قصير العمر وrefresh token دوّار يُخزَّنان في التخزين الآمن.",
        "يضيف سجل استهلاك: الفئة ← المعامل النشط ← الكمية والوحدة والتاريخ. يتحقق الخادم من كل حقل.",
        "يحسب الخادم الانبعاثات بالجرامات كأعداد صحيحة (ROUND_HALF_UP)، ويحفظ نسخة من قيمة المعامل ومصدره داخل السجل.",
        "تجمع خدمات التقارير السجلات حسب الفترة والفئة، وترسل النتائج إلى لوحة المعلومات والتقارير.",
        "عند طلب مساعدة ذكية، يبني الخادم سياقًا من الأرقام المحسوبة فقط، ويستدعي OpenRouter، ثم يتحقق من بنية الرد.",
        "إذا كان الطلب صورة فاتورة، يُرسل بعد موافقة صريحة؛ الاستخراج تجريبي، ولا يُحفظ سجل إلا بعد مراجعة المستخدم وتأكيده.",
        "تسجل الإدارة المعاملات والمحتوى والتحديات، وتراقب الاستخدام والأخطاء والردود الموسومة في لوحة التدقيق.",
    ], 1):
        numbered(doc, i, item)

    h2(doc, "5.2 معادلة الحساب")
    callout(
        doc,
        "الحساب مملوك للخادم",
        "تُحسب الانبعاثات بضرب كمية الاستهلاك في قيمة المعامل، ثم تُحوَّل الجرامات إلى كيلوجرامات للعرض. تُخزَّن القيمة الداخلية بالجرامات كعدد صحيح، ولا يشارك الذكاء الاصطناعي في هذه العملية.",
        fill="F1F8E9",
        bar=LEAF,
    )
    body(doc, "مثال حسابي:", after=2)
    code_block(doc, ["250 kWh x 233 g/kWh = 58,250 g = 58.25 kg CO2e"])
    body(doc, "المعاملات الأولية المستخدمة في النسخة التجريبية موثقة المصدر، وليست شهادة كربونية معتمدة. تشمل أمثلة الكهرباء 233 g/kWh، سيارة البنزين 170 g/km، الرحلات القصيرة 255 g/passenger-km، الماء 344 g/m³ للإمداد، والطعام 60,000 g/kg للحوم البقر. يمكن للإدارة تعديل المعامل، لكن السجلات القديمة تحتفظ باللقطة التاريخية ولا تتغير بأثر رجعي.")

    table(
        doc,
        ["الفئة", "أمثلة على المعاملات الافتراضية", "المصدر المرجعي"],
        [
            ("الكهرباء", "شبكة كهرباء 233 g/kWh؛ غاز طبيعي 2,020 g/m³", "DEFRA/BEIS 2025"),
            ("النقل", "بنزين 170 g/km؛ ديزل 171؛ هايبرد 90؛ حافلة 82؛ قطار 35 g/passenger-km", "DEFRA/BEIS 2025"),
            ("الطيران", "قصير المدى 255؛ طويل المدى 150 g/passenger-km", "DEFRA/BEIS 2025"),
            ("الماء", "إمداد 344؛ مياه عادمة 272 g/m³", "UK Water Industry 2024"),
            ("النفايات", "مكب 586؛ إعادة تدوير 21 g/kg", "DEFRA/BEIS 2025"),
            ("الطعام", "لحم بقري 60,000؛ دجاج 6,900؛ خضروات 2,000؛ ألبان 3,200 g/kg", "Poore & Nemecek / OWID 2018"),
        ],
        [2.8, 9.2, 4.0],
        caption_text="أمثلة على معاملات الانبعاثات الافتراضية",
        size=8.4,
        first_col_bold=True,
    )
    body(doc, "ملاحظة منهجية: هذه القيم تعليمية/تجريبية مستندة إلى مصادر منشورة، وتُستخدم لبناء تجربة متسقة، وليست بديلًا عن حساب معتمد أو مراجعة بيئية رسمية.", size=8.8, color=GREY)

    # ------------------------------------------------------------------
    # 6. DIAGRAMS (landscape)
    # ------------------------------------------------------------------
    landscape(doc)
    h1(doc, "6. مخططات النظام", page_break=False)
    body(doc, "تُعرض المخططات الخمسة بالأسود والأبيض بدقة 300 DPI، وهي مخرجات تحليل النظام المطلوبة: مخطط السياق، مخطط تدفق البيانات المستوى 0، المستوى 1، حالات الاستخدام، ومخطط قاعدة البيانات. المصادر القابلة للتعديل موجودة في docs/diagrams/generate_diagrams.py.")
    body(doc, "قراءة المخططات: السياق يحدد النظام وحدوده والفاعلين؛ DFD-0 يوضح التدفق العام بين المستخدم والعمليات والمخازن؛ DFD-1 يفصّل تسع عمليات وسبعة مخازن بيانات؛ حالات الاستخدام تربط الفاعلين بالوظائف؛ وERD يوضح الجداول الـ29 وعلاقاتها.", size=9.8)
    table(
        doc,
        ["#", "المخطط", "ماذا يوضح؟"],
        [
            ("1", "مخطط السياق", "حدود النظام، الفاعلون الأربعة، وتكامل OpenRouter الخارجي."),
            ("2", "DFD — المستوى 0", "النظام كعملية واحدة والتدفق العام مع المستخدمين والمخازن."),
            ("3", "DFD — المستوى 1", "تسع عمليات رئيسية وسبعة مخازن بيانات D1–D7."),
            ("4", "حالات الاستخدام", "الزائر والمستخدم والمنظمة والإدارة وعلاقتهم بالوظائف."),
            ("5", "ERD", "الجداول الـ29 والعلاقات الأساسية في SQLite."),
        ],
        [1.0, 6.2, 17.0],
        caption_text="قائمة المخططات الخمسة",
        size=9,
        ltr_cols=(0,),
    )

    diagrams = [
        ("01-context.png", "مخطط السياق: النظام، الفاعلون، وحدود التكامل مع OpenRouter."),
        ("02-dfd-level-0.png", "مخطط تدفق البيانات — المستوى 0: التدفق العام بين المستخدم والعمليات والمخازن."),
        ("03-dfd-level-1.png", "مخطط تدفق البيانات — المستوى 1: تسع عمليات رئيسية ومخازن البيانات D1–D7."),
        ("04-use-case.png", "مخطط حالات الاستخدام: الزائر، المستخدم، المنظمة، الإدارة، ومزوّد الذكاء الاصطناعي."),
        ("05-erd.png", "مخطط الكيانات والعلاقات: 29 جدولًا وعلاقاتها الأساسية في SQLite."),
    ]
    for idx, (name, cap) in enumerate(diagrams):
        doc.add_page_break()
        h2(doc, f"6.{idx + 1}  {cap.split(':')[0]}")
        figure(doc, ROOT / "docs" / "diagrams" / name, cap, max_w=25.5, max_h=16.0)

    # ------------------------------------------------------------------
    # 7. TECHNOLOGIES
    # ------------------------------------------------------------------
    portrait(doc)
    h1(doc, "7. التقنيات المستخدمة ووظيفة كل تقنية", page_break=False)
    lead(doc, "الفكرة قوية فقط إذا اختيرت لها أدوات مناسبة. هذا الفصل يشرح كل تقنية في المشروع، وإصدارها، وأين تُستخدم فعليًا، وليس مجرد قائمة أسماء.")

    h2(doc, "7.1 لماذا هذه الاختيارات؟")
    body(doc, "اختيرت Flutter لأنها تسمح بواجهة أندرويد متسقة وسريعة مع دعم RTL من نظام التصميم، وFlask لأنه إطار خفيف يسمح بفصل واضح بين الواجهة والخدمات وقاعدة البيانات، وSQLite لأن المشروع محلي وتعليمي ويحتاج ملفًا واحدًا قابلًا للنقل والنسخ مع الحفاظ على المعاملات والعلاقات. اختير OpenRouter لأنه يقدم مسارًا مجانيًا موحدًا، مع فرض استخدام openrouter/free على مستوى إعدادات الخادم، وليس على مستوى التطبيق.")

    h2(doc, "7.2 تطبيق الأندرويد (Flutter)")
    table(
        doc,
        ["التقنية", "الإصدار", "استخدامها في المشروع"],
        [
            ("Flutter", "3.47.9", "بناء واجهة Android واحدة، Material 3، دعم RTL والوضعين الفاتح/الداكن حسب الثيم."),
            ("Dart", "3.13.7", "لغة التطبيق مع null safety وasync/await لإدارة الطلبات."),
            ("flutter_bloc", "9.1.1", "إدارة الحالة: كل شاشة لها Cubit/Bloc وحالات Initial/Loading/Success/Failure."),
            ("equatable", "3.0.0", "مقارنة الحالات والنماذج بالقيمة، مما يجعل اختبارات BLoC حتمية."),
            ("Dio", "5.11.1", "عميل HTTP الوحيد؛ يضيف التوكن، يحاول تجديده مرة واحدة عند 401، ويحوّل الأخطاء إلى استثناءات مفهومة."),
            ("go_router", "18.1.4", "التنقل التصريحي، حماية المسارات، وإعادة التوجيه حسب حالة المصادقة."),
            ("flutter_secure_storage", "11.2.0", "تخزين access/refresh tokens في Android Keystore؛ لا تُخزَّن في sqflite أو logs."),
            ("sqflite", "2.4.6", "كاش قراءة محلي للوحة والسجلات؛ الكتابة دائمًا إلى الـAPI حتى يبقى الخادم مرجع الحقيقة."),
            ("path + path_provider", "1.9.1 / 2.1.6", "مسارات قاعدة البيانات المحلية والملفات المؤقتة للتصدير/المشاركة."),
            ("intl", "0.20.3", "تنسيق التواريخ والأرقام والعملات/الوحدات وفق اللغة والمنطقة."),
            ("image_picker", "1.2.4", "التقاط صورة فاتورة أو اختيارها من المعرض قبل الرفع."),
            ("fl_chart", "1.3.1", "رسوم الاتجاهات وتوزيع الفئات وتقدم الأهداف."),
            ("shared_preferences", "2.5.6", "إعدادات غير حساسة مثل اللغة والتفضيلات المحلية؛ لا يستخدم للتوكنات."),
            ("flutter_localizations + l10n", "SDK", "تفعيل العربية واتجاه RTL وتوفير 310 مفاتيح لكل لغة عبر قاموس مركزي."),
            ("flutter_lints", "6.0.0", "قواعد تحليل صارمة؛ الهدف صفر ملاحظات من flutter analyze."),
        ],
        [4.1, 2.2, 9.7],
        caption_text="تقنيات تطبيق الأندرويد",
        size=8.5,
        ltr_cols=(0, 1),
        first_col_bold=True,
    )

    h2(doc, "7.3 الخادم وواجهة API")
    table(
        doc,
        ["التقنية", "الإصدار", "استخدامها في المشروع"],
        [
            ("Python", "3.15.2", "بيئة تشغيل الخادم والاختبارات والسكربتات."),
            ("Flask", "3.1.3", "application factory، Blueprints، وربط مسارات /api/v1 و/admin."),
            ("Jinja2", "3.1.6", "قوالب لوحة الإدارة الإنجليزية، مع وراثة base.html وmacros."),
            ("Flask-SQLAlchemy", "3.1.1", "ربط SQLAlchemy بدورة حياة Flask وإدارة الجلسات."),
            ("SQLAlchemy", "2.1.9", "نماذج ORM، علاقات، استعلامات، ومعاملات."),
            ("Flask-Migrate + Alembic", "4.1.0 / 1.20.1", "ترحيلات مخطط قاعدة البيانات (المراجعة 88ef867c03ab)."),
            ("SQLite", "3.x", "قاعدة البيانات الوحيدة؛ WAL، foreign_keys=ON، busy_timeout=5000."),
            ("Flask-JWT-Extended + PyJWT", "4.7.4 / 2.15.1", "مصادقة التطبيق: access قصير + refresh دوّار، وإبطال الجلسات."),
            ("Flask-WTF + WTForms", "1.3.0 / 3.3.2", "حماية CSRF، نماذج الإدارة، والتحقق من المدخلات."),
            ("flask-openapi3 + pydantic", "4.3.2 / 2.14.3", "توثيق OpenAPI 3، مخططات الطلب/الرد، وSwagger على /api/."),
            ("httpx", "0.28.1", "استدعاء OpenRouter عبر HTTPS مع مهلة وإعادة محاولة محدودة."),
            ("pypdf", "6.5.0", "استخراج نص بعض ملفات PDF المرفوعة كخطوة مساعدة قبل التحليل."),
            ("Pillow", "13.0.0", "التحقق من الصور وتغيير حجمها، وتوليد المخططات والأصول البصرية."),
            ("Werkzeug", "3.1.9", "تجزئة كلمات المرور والتحقق الآمن."),
            ("python-dotenv", "1.2.4", "تحميل الإعدادات والأسرار من .env على الخادم."),
            ("email-validator", "2.4.0", "التحقق من صيغة البريد الإلكتروني."),
            ("itsdangerous", "2.2.0", "توقيع كوكي جلسة الإدارة (عبر Flask)."),
            ("csv (stdlib)", "—", "تصدير التقارير والتحليلات بصيغة CSV."),
        ],
        [4.4, 2.2, 9.4],
        caption_text="تقنيات الخادم وقاعدة البيانات",
        size=8.4,
        ltr_cols=(0, 1),
        first_col_bold=True,
    )

    h2(doc, "7.4 طبقة الذكاء الاصطناعي")
    table(
        doc,
        ["العنصر", "كيف يُستخدم؟"],
        [
            ("OpenRouter API", "بوابة HTTPS خارجية؛ المفتاح موجود على الخادم فقط ولا يصل إلى التطبيق."),
            ("openrouter/free", "النموذج الوحيد المسموح، يختار موجّهًا مجانيًا؛ لا يوجد نموذج مدفوع كبديل."),
            ("قوالب الأوامر + مخططات JSON", "كل وظيفة لها تعليمات ومخطط حقول محدد، لمنع الردود الحرة غير القابلة للتحقق."),
            ("pydantic", "التحقق من بنية المخرجات وأنواعها قبل عرضها أو حفظها."),
            ("حاجز الأرقام", "فحص النص العائد بحثًا عن أرقام غير موجودة في السياق المحسوب؛ عند الشك يُرفض الرد ويُستخدم البديل."),
            ("ai_cache", "تخزين مؤقت بمفتاح بصمة الطلب لتقليل التكلفة والزمن وتكرار النتائج."),
            ("ai_usage / ai_flagged_responses", "تسجيل الميزة والنموذج والتوكنات والزمن والحالة؛ حفظ الردود الموسومة للمراجعة بعد تنقية PII."),
            ("بديل حتمي", "عند غياب المفتاح أو فشل الخدمة: ملخصات وقواعد ورسائل واضحة (ai_disabled) بدل تعطيل التطبيق."),
        ],
        [4.6, 11.4],
        caption_text="مكوّنات الذكاء الاصطناعي",
        size=8.7,
        first_col_bold=True,
    )

    h2(doc, "7.5 الجودة والتشغيل")
    table(
        doc,
        ["الأداة", "استخدامها"],
        [
            ("Git + GitHub", "إدارة الإصدارات، فرع لكل مشكلة، Pull Request، ومراجعة قبل الدمج."),
            ("GitHub Actions", "تشغيل lint/format/tests/coverage تلقائيًا للخادم والتطبيق."),
            ("pytest + pytest-cov", "54 اختبار خادم وتغطية 76.22% (الحد 50%)."),
            ("ruff + black", "فحص وتنسيق Python على 95 ملفًا دون مخالفات."),
            ("flutter analyze + flutter test", "23 اختبار تطبيق وتغطية 92.16% وصفر ملاحظات تحليل."),
            ("lcov + check_lcov.py", "قراءة تقرير التغطية وفرض حد أدنى 50% في CI."),
            ("smoke.py / smoke.cmd", "21 فحصًا سريعًا لواجهات الصحة والدخول والكتالوج والسجلات والأهداف والإدارة."),
            ("Pillow scripts", "توليد المخططات الخمسة والأصول البصرية الأصلية بشكل ثابت."),
            ("python-docx", "توليد هذا التقرير العربي (أداة محلية، ليست اعتمادًا تشغيليًا)."),
            ("سكربتات cmd", "تشغيل التجربة والفحص على Windows دون افتراض PowerShell."),
        ],
        [4.6, 11.4],
        caption_text="أدوات الجودة والتشغيل",
        size=8.8,
        first_col_bold=True,
    )

    # ------------------------------------------------------------------
    # 8. ARCHITECTURE
    # ------------------------------------------------------------------
    h1(doc, "8. معمارية النظام")
    h2(doc, "8.1 الطبقات والمسؤوليات")
    table(
        doc,
        ["الطبقة", "المسؤولية", "أمثلة من المشروع"],
        [
            ("واجهة Flutter", "العرض والتفاعل فقط؛ لا SQL ولا منطق أعمال.", "شاشات، Widgets، حوارات، رسوم fl_chart."),
            ("إدارة الحالة (BLoC)", "استقبال الأحداث وإصدار الحالات، وتنسيق حالات التحميل/النجاح/الفشل.", "AuthCubit، SettingsCubit، AsyncCubit، Cubits الشاشات."),
            ("مستودعات التطبيق", "إخفاء Dio وsqflite عن الواجهة، وتطبيق سياسة القراءة/الكتابة.", "AuthRepository، CarbonRepository، Repositories الميزات."),
            ("Dio / ApiClient", "HTTP، التوكن، التجديد لمرة واحدة، الأخطاء، المهلة.", "Interceptor واحد، رؤوس موحدة، ربط 401."),
            ("مسارات Flask", "استقبال HTTP والتحقق الأولي واستدعاء الخدمة؛ لا SQL.", "Blueprints لـ auth/records/goals/plans/ai..."),
            ("خدمات Flask", "منطق الأعمال والمعاملات والقرارات.", "حساب الانبعاثات، اختيار المعامل، توليد الخطة، صلاحيات الإدارة."),
            ("SQLAlchemy / SQLite", "الوصول الوحيد للبيانات، العلاقات، الفهارس، الترحيلات.", "29 نموذجًا، لقطات المعامل، سجلات التدقيق."),
            ("OpenRouter", "خدمة خارجية للذكاء الاصطناعي، تُستدعى من خدمة الخادم فقط.", "مساعد، رؤى، خطط، بدائل، استخراج."),
        ],
        [3.4, 7.4, 5.2],
        caption_text="طبقات النظام",
        size=8.9,
        first_col_bold=True,
    )

    h2(doc, "8.2 فصل واجهتي الوصول")
    body(doc, "هناك مساران لا يختلطان: /api/v1 مسار JSON للتطبيق، محمي بـJWT، ويعيد غلافًا موحدًا للنجاح (المفتاح data) وللأخطاء (كائن error يحوي code وmessage وdetails). و/admin مسار HTML للوحة الإدارة، محمي بجلسة كوكي موقعة وCSRF، ولا يقبل JWT. الخادم يمنع تمرير كوكي الإدارة إلى API والعكس، ويستخدم خدمات مشتركة حتى لا تتكرر قواعد العمل.")

    h2(doc, "8.3 هيكل المستودع")
    code_block(doc, [
        "G_81/",
        "├─ backend/        Flask API + Jinja admin + SQLite + migrations + tests",
        "├─ mobile/         Flutter Android app (BLoC + Dio + sqflite)",
        "├─ docs/           Documentation, diagrams, screenshots, assets, report",
        "├─ scripts/        smoke, demo, coverage, diagram wrapper",
        "├─ .github/        CI workflows, issue and PR templates",
        "├─ agent.md        Engineering rules",
        "└─ README.md       Quick start and demo accounts",
    ])

    body(doc, "داخل الخادم: app/core (إعدادات/أخطاء/أمان/فترات/حدود)، app/modules (كل ميزة بنماذجها وخدماتها)، app/api/v1 (المسارات والمخططات)، app/templates (الإدارة)، backend/tests (اختبارات معزولة). وداخل التطبيق: lib/core (شبكة/تخزين/توجيه/ثيم/ترجمة) وlib/features (كل ميزة ببياناتها وعرضها)، وهو تنظيم feature-first يسهل إضافة ميزة دون كسر الباقي.")

    # ------------------------------------------------------------------
    # 9. AI
    # ------------------------------------------------------------------
    h1(doc, "9. الذكاء الاصطناعي: الوظائف والضوابط")
    h2(doc, "9.1 الوظائف الخمس")
    table(
        doc,
        ["الوظيفة", "المدخل", "المخرج", "الحدود"],
        [
            ("المساعد", "سؤال + سياق أرقام محسوبة + لغة المستخدم", "رد نصي منظم مع تفسير وخطوات", "لا أرقام جديدة؛ حد استخدام ومهلة."),
            ("الرؤى", "ملخص فترة/فئات/اتجاهات", "أهم المصادر والفرص والاتجاهات", "البديل الحتمي عند تعذر الخدمة."),
            ("خطط الخفض", "هدف/نسبة/فئة/سياق", "خطة JSON بإجراءات ومدة وأثر وصعوبة", "تتحقق المخططات قبل العرض؛ لا حفظ تلقائي."),
            ("البدائل", "فئة/سياق/تفضيلات", "بدائل مرتبة مع سبب وتأثير محسوب", "التأثير من الخادم، لا من النموذج."),
            ("استخراج الفواتير", "صورة/PDF بعد موافقة", "حقول مرشحة بدرجة ثقة", "best-effort؛ يدوي دائمًا؛ لا حفظ تلقائي."),
        ],
        [3.0, 5.0, 5.0, 3.0],
        caption_text="وظائف الذكاء الاصطناعي",
        size=8.4,
        first_col_bold=True,
    )

    h2(doc, "9.2 الفصل بين AI والحساب")
    table(
        doc,
        ["السؤال", "الإجابة في CarbonWise"],
        [
            ("من يحسب الانبعاثات؟", "الخادم فقط، من الكمية × المعامل، ويحفظ الناتج ولقطة المعامل."),
            ("من يختار المعامل؟", "الخادم من الكتالوج النشط؛ الإدارة تعدّله، ولا يعدله النموذج."),
            ("ماذا يرى النموذج؟", "سياقًا محسوبًا ومنقّحًا من PII، وليس قاعدة البيانات كاملة."),
            ("هل يمكنه الكتابة في قاعدة البيانات؟", "لا. أي إنشاء/تعديل يمر بمسار API يتحقق من الصلاحيات والمدخلات."),
            ("ماذا لو اخترع رقمًا؟", "حاجز الأرقام يرفض/يستبدل الرد؛ الواجهة تعرض القيم المحسوبة فقط."),
            ("ماذا لو غاب المفتاح؟", "يعمل التطبيق في وضع بديل حتمي، وتظهر حالة ai_disabled بوضوح."),
        ],
        [5.2, 10.8],
        caption_text="حدود مسؤولية الذكاء الاصطناعي",
        size=8.8,
        first_col_bold=True,
    )

    h2(doc, "9.3 الضوابط الأمنية والتشغيلية")
    for item in [
        "المفتاح على الخادم فقط، ويُرفض أي نموذج غير openrouter/free عند بدء التشغيل، ولا يوجد تدريب أو ضبط نموذج.",
        "تحقق بنيوي من JSON عبر pydantic، مع رفض الحقول الناقصة أو غير المتوقعة.",
        "حاجز أرقام: مقارنة الأرقام في الرد بالسياق المحسوب؛ تكرار المخالفة يُسجَّل للمراجعة.",
        "حدود استخدام: ميزانية يومية، حد ساعي، ومهلة، وإعادة محاولة محدودة مع تراجع.",
        "تخزين مؤقت ببصمة الطلب، وتسجيل usage (الميزة/النموذج/التوكنات/الزمن/الحالة).",
        "تنقية PII قبل الإرسال أو التسجيل؛ لا تُسجَّل الأوامر الخام الحساسة في الإنتاج.",
        "موافقة صريحة قبل إرسال صورة فاتورة إلى الموجّه المجاني، مع بديل الإدخال اليدوي.",
        "الردود الموسومة تُحفظ بعد التنقية لمراجعة الإدارة، لا للمستخدم.",
    ]:
        bullet(doc, item)

    callout(
        doc,
        "لماذا لا نستخدم نموذجًا مدفوعًا كاحتياطي؟",
        "لأن قاعدة المشروع تمنع أي نموذج مدفوع حتى عند الفشل. عند تعذر المجاني، يظهر خطأ واضح أو يعمل البديل الحتمي؛ لا يوجد مسار خفي يخالف السياسة.",
    )

    # ------------------------------------------------------------------
    # 10. DATA MODEL
    # ------------------------------------------------------------------
    h1(doc, "10. نموذج البيانات")
    body(doc, "قاعدة البيانات SQLite واحدة، وتحتوي 29 جدولًا. الترحيلات تُدار بـAlembic، وكل اتصال يفعّل foreign_keys=ON وWAL. السجلات المالية/البيئية لا تُحذف فعليًا من واجهة المستخدم، بل تُستخدم حالة/حذف منطقي حيث يلزم، وتُحفظ لقطة المعامل داخل السجل حتى لا يتغير التاريخ عند تحديث الكتالوج.")

    table(
        doc,
        ["المجال", "الجداول", "الوظيفة"],
        [
            ("الهوية والوصول", "organizations، users، user_profiles، refresh_tokens، admins، admin_audit_logs", "حسابات، ملفات، جلسات تجديد، إدارة، وتدقيق."),
            ("الكتالوج والحساب", "emission_categories، emission_factors، consumption_records، documents", "فئات ومعاملات وسجلات ومستندات مرتبطة."),
            ("الأهداف والخطط", "goals، reduction_plans، plan_actions، alternatives، saved_alternatives", "أهداف، خطط، إجراءات، بدائل محفوظة."),
            ("التفاعل", "challenges، challenge_participants، points_ledger، badges، user_badges، notifications، notification_preferences", "تحديات ومشاركة ونقاط وشارات وإشعارات."),
            ("المحتوى والإعدادات", "articles، app_settings", "مقالات ثنائية اللغة وإعدادات المنصة."),
            ("الذكاء الاصطناعي", "ai_conversations، ai_messages، ai_usage، ai_flagged_responses، ai_cache", "محادثات، رسائل، استخدام، ردود للمراجعة، وكاش."),
        ],
        [3.0, 9.0, 4.0],
        caption_text="مجموعات الجداول الـ29",
        size=8.2,
        first_col_bold=True,
    )

    h2(doc, "10.1 قواعد ثابتة")
    for item in [
        "كل جدول له مفتاح أساسي id، وcreated_at/updated_at بتوقيت UTC دون منطقة زمنية (naive UTC).",
        "العلاقات مفاتيح خارجية صريحة وفهارس للبحث والتصفية؛ لا حذف يتيمًا.",
        "السجل يحتفظ بقيمة المعامل ووحدته ومصدره وقت الحساب، حتى لو تغير المعامل لاحقًا.",
        "الجداول المحتوى تحتوي نسختين en/ar، والإدارة تحررهما معًا.",
        "التوكنات وكلمات المرور لا تُخزَّن خامًا: كلمة المرور مجزأة، وrefresh يُخزَّن مجزأً.",
        "كل استدعاء AI له سجل usage، والردود الموسومة فقط تُحفظ بعد تنقية PII.",
    ]:
        bullet(doc, item)

    h2(doc, "10.2 العلاقات الأساسية")
    body(doc, "المستخدم يملك ملفًا شخصيًا وسجلات وأهدافًا وخططًا ومشاركات؛ السجل مرتبط بفئة ومعامل ومستخدم/منظمة؛ الخطة مرتبطة بهدف وإجراءات؛ التحدي له مشاركون ونقاط وشارات؛ والمستند مرتبط بمستخدم وسجل/استخراج. مخطط ERD في الفصل 6 يوضح هذه العلاقات بصريًا.")

    # ------------------------------------------------------------------
    # 11. SECURITY
    # ------------------------------------------------------------------
    h1(doc, "11. الأمان والخصوصية")
    h2(doc, "11.1 المصادقة والجلسات")
    table(
        doc,
        ["السطح", "الآلية", "الحماية"],
        [
            ("تطبيق الموبايل", "JWT access قصير + refresh دوّار", "تخزين آمن، تجديد مرة واحدة، إبطال refresh، رفض 401."),
            ("لوحة الإدارة", "جلسة كوكي موقعة + CSRF", "login_required، نماذج CSRF، أدوار super_admin/content_editor."),
            ("كلمات المرور", "Werkzeug hash", "لا تخزين/تسجيل النص الأصلي، تحقق خادمي دائم."),
            ("الملفات", "تخزين خاص + تنزيل مصادق", "لا روابط عامة، تحقق نوع/حجم، منع path traversal."),
            ("AI", "مفتاح خادم + تنقية PII", "لا مفتاح على الجهاز، لا سجلات حساسة، حد استخدام."),
        ],
        [3.5, 6.4, 6.1],
        caption_text="آليات الأمان",
        size=8.8,
        first_col_bold=True,
    )

    h2(doc, "11.2 ضوابط إضافية")
    for item in [
        "تحقق خادمي من كل مدخل عبر pydantic/WTForms، وأخطاء موحدة دون كشف stack traces.",
        "استعلامات SQLAlchemy بمعاملات، ومنع تركيب SQL من مدخلات المستخدم.",
        "CSRF وسياسات الكوكي مناسبة لكل سطح، وعدم خلط JWT مع كوكي الإدارة.",
        "تصدير CSV محمي بصلاحية super_admin، ويقيّد الأعمدة والفترة الزمنية.",
        "حدود معدل على الدخول والذكاء الاصطناعي والرفع، مع رسائل 429 واضحة.",
        "عدم تسجيل التوكنات أو المفاتيح أو محتوى الفواتير أو الأوامر الحساسة.",
        "النسخ الاحتياطي المحلي لقاعدة SQLite ممكن لأنها ملف واحد، مع WAL.",
    ]:
        bullet(doc, item)

    # ------------------------------------------------------------------
    # 12. TESTING
    # ------------------------------------------------------------------
    h1(doc, "12. الاختبارات والجودة")
    body(doc, "الجودة ليست ادعاءً؛ المشروع يملك بوابات قابلة للتشغيل. الاختبارات معزولة بقاعدة SQLite مؤقتة، والذكاء الاصطناعي مُموَّه بالكامل، ولا توجد اتصالات شبكة حقيقية في الاختبارات. الحد الأدنى للتغطية 50% لكل جهة، وقد تجاوزه المشروع بفارق كبير.")

    table(
        doc,
        ["النوع", "الأدوات", "النتيجة"],
        [
            ("اختبارات خادم", "pytest + pytest-cov + Flask test client", "54 ناجحة، 0 فاشلة، تغطية 76.22%."),
            ("اختبارات تطبيق", "flutter test + bloc_test/Widget tests", "23 ناجحة، تغطية 92.16% (247/268 سطرًا)."),
            ("تحليل ثابت", "ruff + black + flutter analyze + flutter_lints", "Ruff/Black نظيفان؛ 0 ملاحظات Flutter."),
            ("ترجمة", "mobile/tool/check_l10n.py", "310 مفاتيح إنجليزية = 310 عربية."),
            ("فحص دخان", "scripts/smoke.py (stdlib urllib)", "21/21: صحة، دخول، مستخدم، كتالوج، سجلات، أهداف، لوحة، AI، 401، إدارة."),
            ("CI", "GitHub Actions: backend.yml + mobile.yml", "أخضر على PR #2 وعلى main."),
        ],
        [3.3, 7.0, 5.7],
        caption_text="نتائج التحقق",
        size=8.7,
        first_col_bold=True,
    )

    body(doc, "أمثلة على ما تغطيه الاختبارات: تسجيل/دخول/تجديد/خروج، رفض التوكن المنتهي، التحقق من السجلات، حساب الانبعاثات ولقطة المعامل، التقارير والتصدير، الأهداف والخطط، التحديات والنقاط، رفض AI للأرقام المخترعة، استخراج المستندات وحدود الحجم، صلاحيات الإدارة وCSRF، وأخطاء 401/403/404/422.")

    h2(doc, "12.1 أوامر التحقق")
    code_block(doc, [
        "cd /d D:\\projects_is_2026\\G_81\\backend",
        ".venv\\Scripts\\python.exe -m pytest --cov=app --cov-report=term-missing",
        ".venv\\Scripts\\ruff.exe check app tests",
        ".venv\\Scripts\\black.exe --check app tests",
        "",
        "cd /d D:\\projects_is_2026\\G_81\\mobile",
        "flutter analyze",
        "flutter test --coverage",
        "python tool\\check_l10n.py",
        "",
        "cd /d D:\\projects_is_2026\\G_81",
        "python scripts\\check_lcov.py mobile\\coverage\\lcov.info --min 50",
    ])

    # ------------------------------------------------------------------
    # 13. RUNNING
    # ------------------------------------------------------------------
    h1(doc, "13. التشغيل والتجربة")
    h2(doc, "13.1 المتطلبات")
    body(doc, "Windows مع Python 3.15 وFlutter 3.47.9، ومتصفح حديث. المشروع لا يحتاج خادم قاعدة بيانات خارجيًا ولا Redis ولا خدمة سحابية. للذكاء الاصطناعي الحي يلزم مفتاح OpenRouter على الخادم فقط؛ وبدونه يعمل التطبيق في الوضع البديل.")

    h2(doc, "13.2 تشغيل الخادم")
    code_block(doc, [
        "cd /d D:\\projects_is_2026\\G_81\\backend",
        ".venv\\Scripts\\activate",
        "flask --app app db upgrade",
        "flask --app app seed",
        "flask --app app run --host 127.0.0.1 --port 5001",
    ])
    body(doc, "المنفذ 5001 مستخدم في بيئة العرض لأن المنفذ 5000 مشغول بتطبيق آخر على الجهاز. بعد التشغيل: لوحة الإدارة http://127.0.0.1:5001/admin/login، وتوثيق API http://127.0.0.1:5001/api/.")

    h2(doc, "13.3 تشغيل التطبيق")
    code_block(doc, [
        "cd /d D:\\projects_is_2026\\G_81\\mobile",
        "flutter pub get",
        "flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5001/api/v1",
    ])
    body(doc, "10.0.2.2 هو عنوان جهاز الكمبيوتر من داخل محاكي Android. على جهاز حقيقي، استبدله بعنوان IP للكمبيوتر على نفس الشبكة. التطبيق لا يخزّن مفتاح OpenRouter ولا يتصل بمزوّد AI مباشرة.")

    h2(doc, "13.4 حسابات العرض")
    table(
        doc,
        ["الدور", "البريد", "كلمة المرور"],
        [
            ("مستخدم فرد", "sara@carbonwise.demo", "User123!"),
            ("مستخدم فرد", "ahmad@carbonwise.demo", "User123!"),
            ("مستخدم منظمة", "org@carbonwise.demo", "Org123!"),
            ("مدير المنصة", "admin@carbonwise.demo", "Admin123!"),
            ("محرر محتوى", "editor@carbonwise.demo", "Editor123!"),
        ],
        [3.6, 7.6, 4.8],
        caption_text="حسابات النسخة التجريبية",
        size=9,
        ltr_cols=(1, 2),
        first_col_bold=True,
    )
    body(doc, "للتشغيل السريع: scripts\\demo.cmd يهيّئ قاعدة البيانات إن لزم، يشغّل الخادم على 5001، ويفتح لوحة الإدارة. وscripts\\smoke.cmd يتحقق من 21 نقطة أساسية بعد التشغيل.", size=9.5)

    # ------------------------------------------------------------------
    # 14. DELIVERABLES
    # ------------------------------------------------------------------
    h1(doc, "14. مخرجات المشروع")
    table(
        doc,
        ["المخرج", "التفاصيل", "المكان"],
        [
            ("تطبيق Android", "Flutter، EN/AR، جميع الشاشات والرحلات، APK للإصدار v1.0.0.", "mobile/ + GitHub Release"),
            ("API v1", "134 مسارًا، JWT، OpenAPI/Swagger، أغلفة نجاح/خطأ موحدة.", "backend/app/api/v1"),
            ("لوحة الإدارة", "Jinja2 + جلسات + CSRF، أدوار، تدقيق، تصدير CSV.", "backend/app/templates/admin"),
            ("قاعدة البيانات", "29 جدولًا، ترحيل Alembic، بذرة تجريبية حتمية.", "backend/instance/carbonwise.sqlite3"),
            ("مخططات", "5 مخططات B&W بدقة 300 DPI + مولّد قابل للتعديل.", "docs/diagrams/"),
            ("لقطات شاشة", "29 إدارة + 27 EN + 26 AR، وفجوات موثقة.", "docs/screenshots/"),
            ("أصول بصرية", "15 رسمًا أصليًا WebP مع سجل حقوق.", "mobile/assets/images/ + backend/app/static/assets/images/ (السجل في docs/assets/)"),
            ("توثيق", "أكثر من 40 صفحة: معمارية، API، بيانات، ميزات، ADRs، تشغيل، اختبار.", "docs/"),
            ("تقرير عربي", "هذا الملف، Word قابل للتعديل.", "docs/reports/"),
            ("CI وسكربتات", "backend.yml + mobile.yml + smoke/demo/coverage.", ".github/workflows + scripts/"),
        ],
        [3.0, 9.3, 3.7],
        caption_text="حزمة التسليم",
        size=8.4,
        first_col_bold=True,
    )

    body(doc, "النسخة المنشورة على GitHub: v1.0.0، وتضم ثلاثة APK مقسمة حسب معمارية المعالج (arm64-v8a، armeabi-v7a، x86_64). التوقيع الحالي تجريبي (debug key) لأغراض العرض والاختبار، وليس للنشر على متجر Google Play.")

    # ------------------------------------------------------------------
    # 15. LIMITATIONS
    # ------------------------------------------------------------------
    h1(doc, "15. القيود والتحسينات المستقبلية")
    table(
        doc,
        ["القيد الحالي", "الأثر", "الخطوة التالية المقترحة"],
        [
            ("مفتاح OpenRouter فارغ في بيئة العرض", "يعمل AI في وضع بديل حتمي، لا استدعاء حي.", "ضبط المفتاح على الخادم ومراقبة ai_usage."),
            ("الرؤية تعتمد على النموذج المجاني الموجّه", "قد يكون vision_unavailable لبعض الطلبات.", "إبقاء الإدخال اليدوي، ورسالة واضحة، وقياس نسبة النجاح."),
            ("فجوات في لقطات الحالات", "بعض حالات التحميل/الفراغ/الفشل غير مصورة.", "التقاطها عند تجميد الواجهة التالي دون اختلاق."),
            ("APK بتوقيع debug", "غير مناسب للنشر العام.", "إنشاء keystore إصدار وتوقيع APK/AAB."),
            ("CI لا يبني APK", "البناء يتم محليًا على Windows.", "عامل بناء مثبت أو Gradle cache مناسب."),
            ("SQLite أحادي العقدة", "لا يخدم تعدد مستأجرين/تحميلًا عاليًا.", "توثيق حدود النشر المحلي؛ أي توسع سحابي يحتاج قرارًا معماريًا جديدًا قبل تغيير القاعدة."),
            ("لا iOS/ويب/سطح مكتب", "النطاق أندرويد فقط.", "إعادة استخدام طبقة الأعمال مع واجهات لاحقة."),
            ("الإدارة إنجليزية فقط", "المحتوى ثنائي اللغة لكن واجهة الإدارة EN.", "ترجمة واجهة الإدارة إذا لزم."),
            ("بدون عدادات ذكية/مدفوعات", "الإدخال يدوي أو من فاتورة.", "تكاملات مستقبلية ضمن نطاق جديد."),
        ],
        [4.3, 6.2, 5.5],
        caption_text="القيود المعلنة",
        size=8.2,
        first_col_bold=True,
    )

    body(doc, "هذه القيود ليست فشلًا مخفيًا؛ كلها موثقة في docs/status.md وdocs/screenshots/README.md. المبدأ هو عدم تزييف دليل أو لقطة، وعدم إخفاء حد تقني.")

    # ------------------------------------------------------------------
    # 16. CONCLUSION
    # ------------------------------------------------------------------
    h1(doc, "16. الخلاصة")
    body(doc, "CarbonWise يقدم نموذجًا متكاملًا لمنصة استدامة عملية: يبدأ من بيانات يومية بسيطة، يمر بحساب خادمي شفاف، ينتهي بخطة وتقدم وتحديات. التقنيات ليست مكدسة بلا سبب: Flutter يبني تجربة عربية/إنجليزية متسقة، Flask ينظم الوصول والمنطق، SQLite يحفظ العلاقات والتاريخ، وOpenRouter يضيف تفسيرًا ذكيًا داخل حدود صارمة. والنتيجة أن المستخدم يرى رقمًا يمكنه الوثوق به، ويفهم من أين جاء، ويعرف خطوته التالية.")

    body(doc, "ما يجعل المشروع مكتملًا ليس عدد الشاشات فقط، بل وجود اختبارات وتغطية وCI وتوثيق ومخططات وحزمة تسليم قابلة للمراجعة. الإصدار 1.0.0 جاهز للعرض والتشغيل المحلي، والتحسينات المستقبلية واضحة ومحددة بدل أن تكون وعودًا غامضة.")

    # ------------------------------------------------------------------
    # LINKS
    # ------------------------------------------------------------------
    h1(doc, "روابط ومراجع")
    links = [
        ("المستودع على GitHub", "https://github.com/Asmaaebraheem1/G_81", "https://github.com/Asmaaebraheem1/G_81"),
        ("الإصدار v1.0.0 وملفات APK", "GitHub Releases", "https://github.com/Asmaaebraheem1/G_81/releases/tag/v1.0.0"),
        ("فهرس التوثيق", "docs/README.md", "https://github.com/Asmaaebraheem1/G_81/blob/main/docs/README.md"),
        ("المخططات", "docs/diagrams/", "https://github.com/Asmaaebraheem1/G_81/tree/main/docs/diagrams"),
        ("لقطات الشاشة", "docs/screenshots/", "https://github.com/Asmaaebraheem1/G_81/tree/main/docs/screenshots"),
        ("تقرير الذكاء الاصطناعي", "docs/ai-features.md", "https://github.com/Asmaaebraheem1/G_81/blob/main/docs/ai-features.md"),
        ("نموذج البيانات", "docs/05-data-model.md", "https://github.com/Asmaaebraheem1/G_81/blob/main/docs/05-data-model.md"),
    ]
    for label, text, url in links:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _set_par_bidi(p)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(f"{label}:  ")
        _style_run(r, size=10, bold=True, color=GREEN)
        _hyperlink(p, url, text)

    table(
        doc,
        ["المصدر", "ما يغطيه؟"],
        [
            ("docs/status.md", "الحالة الحالية، نتائج الاختبارات، والفجوات المعلنة."),
            ("docs/05-data-model.md", "الجداول الـ29 والعلاقات وقواعد البيانات."),
            ("docs/06-api-reference.md", "مسارات API v1 والمصادقة والأخطاء."),
            ("docs/ai-features.md", "وظائف AI وحدودها وضوابط الأرقام والخصوصية."),
            ("backend/requirements.txt", "إصدارات حزم الخادم."),
            ("mobile/pubspec.yaml", "إصدارات حزم التطبيق."),
        ],
        [5.0, 11.0],
        caption_text="مصادر بيانات التقرير",
        size=8.8,
        ltr_cols=(0,),
    )
    body(doc, "بيانات التقرير مأخوذة من المستودع في 20 نوفمبر 2026، مع نتائج الاختبارات الموثقة. التقرير وثيقة قابلة للتعديل، وليس بديلًا عن التوثيق الفني التفصيلي.", size=9, color=GREY)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    doc.save(OUT)
    normalise_package(OUT)
    print(f"WROTE {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
