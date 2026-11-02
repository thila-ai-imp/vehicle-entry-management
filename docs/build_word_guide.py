"""Build the CMDA setup guide as a Microsoft Word (.docx) file."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x0C, 0x27, 0x44)
GOLD = RGBColor(0xC4, 0xA3, 0x5A)
MUTED = RGBColor(0x4B, 0x5A, 0x6C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ROW_ALT = "F4F7FB"
CODE_BG = "EEF2F7"

HERE = Path(__file__).resolve().parent
MD_PATH = HERE / "CMDA-Vehicle-Entry-Complete-Setup-Guide.md"
DOCX_PATH = HERE / "CMDA-Vehicle-Entry-Complete-Setup-Guide.docx"


def set_run_font(run, name="Calibri", size=11, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def shade_cell(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_borders(cell, color="C5CDD8"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), color)
        tcBorders.append(el)
    tcPr.append(tcBorders)


def set_paragraph_spacing(p, before=0, after=8, line=1.15):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line


def add_page_number(paragraph):
    run1 = paragraph.add_run("Page ")
    set_run_font(run1, size=9, color=MUTED)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    r2 = paragraph.add_run()
    r2._r.append(fld1)
    r2._r.append(instr)
    r2._r.append(fld2)
    set_run_font(r2, size=9, color=MUTED)
    run3 = paragraph.add_run(" of ")
    set_run_font(run3, size=9, color=MUTED)
    fld3 = OxmlElement("w:fldChar")
    fld3.set(qn("w:fldCharType"), "begin")
    instr2 = OxmlElement("w:instrText")
    instr2.set(qn("xml:space"), "preserve")
    instr2.text = " NUMPAGES "
    fld4 = OxmlElement("w:fldChar")
    fld4.set(qn("w:fldCharType"), "end")
    r4 = paragraph.add_run()
    r4._r.append(fld3)
    r4._r.append(instr2)
    r4._r.append(fld4)
    set_run_font(r4, size=9, color=MUTED)


INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def add_inline(paragraph, text, base_size=11, base_color=None):
    parts = INLINE_RE.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            set_run_font(run, size=base_size, bold=True, color=base_color or NAVY)
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, name="Consolas", size=base_size - 0.5, color=NAVY)
        elif part.startswith("[") and "](" in part:
            label = part[1 : part.index("]")]
            run = paragraph.add_run(label)
            set_run_font(run, size=base_size, color=RGBColor(0x14, 0x5D, 0xA0))
            run.underline = True
        else:
            run = paragraph.add_run(part)
            set_run_font(run, size=base_size, color=base_color)


def is_table_separator(line):
    return bool(re.match(r"^\|?\s*:?-{3,}", line.replace(" ", ""))) or bool(
        re.match(r"^\|?\s*[-:| ]+$", line)
    ) and "-" in line


def parse_table_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def add_table(doc, rows):
    if not rows:
        return
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for i, row in enumerate(rows):
        for j in range(cols):
            cell = table.rows[i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            set_paragraph_spacing(p, 2, 2, 1.08)
            value = row[j] if j < len(row) else ""
            add_inline(p, value, base_size=10, base_color=WHITE if i == 0 else None)
            set_cell_borders(cell)
            if i == 0:
                shade_cell(cell, "0C2744")
                for run in p.runs:
                    run.bold = True
                    run.font.color.rgb = WHITE
            elif i % 2 == 0:
                shade_cell(cell, ROW_ALT)
    doc.add_paragraph()


def add_code_block(doc, lines):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 6, 10, 1.1)
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.right_indent = Cm(0.3)
    run = p.add_run("\n".join(lines))
    set_run_font(run, name="Consolas", size=9.5, color=NAVY)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), CODE_BG)
    shd.set(qn("w:val"), "clear")
    pPr.append(shd)


def configure_styles(doc):
    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(11)
    styles["Normal"].font.color.rgb = RGBColor(0x15, 0x20, 0x33)
    for name, size in (("Heading 1", 18), ("Heading 2", 14), ("Heading 3", 12)):
        st = styles[name]
        st.font.name = "Calibri"
        st.font.color.rgb = NAVY
        st.font.size = Pt(size)
        st.font.bold = True


def add_cover(doc):
    for _ in range(3):
        doc.add_paragraph()
    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(kicker, 0, 8)
    run = kicker.add_run("CMDA MARKET MANAGEMENT COMMITTEE")
    set_run_font(run, size=12, bold=True, color=GOLD)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(title, 6, 8)
    run = title.add_run("Vehicle Entry Management System")
    set_run_font(run, name="Georgia", size=28, bold=True, color=NAVY)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(sub, 0, 18)
    run = sub.add_run("Complete Setup and Operations Guide")
    set_run_font(run, size=16, color=NAVY)

    rule = doc.add_paragraph()
    rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = rule.add_run("Chennai Iron & Steel Yard  ·  Intranet portal")
    set_run_font(run, size=12, italic=True, color=MUTED)

    meta = [
        ("Version", "1.0.0"),
        ("Default sign-in", "admin  /  admin"),
        ("Server address (this PC)", "http://localhost:3000"),
        ("LAN clients", "http://SERVER-IP:3000"),
        ("Last updated", "1 November 2026"),
    ]
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, 18, 6)
    table = doc.add_table(rows=len(meta), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(meta):
        left, right = table.rows[i].cells
        left.text = ""
        right.text = ""
        lp, rp = left.paragraphs[0], right.paragraphs[0]
        set_paragraph_spacing(lp, 4, 4)
        set_paragraph_spacing(rp, 4, 4)
        lr = lp.add_run(k)
        rr = rp.add_run(v)
        set_run_font(lr, size=11, bold=True, color=NAVY)
        set_run_font(rr, size=11)
        shade_cell(left, "F4F7FB")
        set_cell_borders(left)
        set_cell_borders(right)

    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(note, 28, 0)
    run = note.add_run(
        "For IT staff and yard supervisors. Print this file or keep a copy with the server PC."
    )
    set_run_font(run, size=10, color=MUTED)
    doc.add_page_break()


def convert(md_text: str, doc: Document):
    lines = md_text.replace("\r\n", "\n").split("\n")
    i = 0
    skipped_title = False
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip()
        stripped = raw.strip()

        if not skipped_title and stripped.startswith("# "):
            skipped_title = True
            i += 1
            continue
        if stripped == "## Complete Setup and Operations Guide":
            i += 1
            continue
        if stripped == "---":
            i += 1
            continue
        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i].rstrip())
                i += 1
            i += 1
            add_code_block(doc, block)
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1].strip()):
            rows = [parse_table_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(parse_table_row(lines[i].strip()))
                i += 1
            add_table(doc, rows)
            continue

        if stripped.startswith("### "):
            p = doc.add_heading(stripped[4:], level=2)
            set_paragraph_spacing(p, 14, 6)
            i += 1
            continue
        if stripped.startswith("## "):
            p = doc.add_heading(stripped[3:], level=1)
            set_paragraph_spacing(p, 18, 8)
            i += 1
            continue

        checkbox = re.match(r"^- \[ \] (.+)$", stripped)
        if checkbox:
            p = doc.add_paragraph(style="List Bullet")
            set_paragraph_spacing(p, 0, 4)
            add_inline(p, "☐  " + checkbox.group(1), base_size=11)
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            p = doc.add_paragraph(style="List Number")
            set_paragraph_spacing(p, 0, 4)
            add_inline(p, re.sub(r"^\d+\.\s+", "", stripped), base_size=11)
            i += 1
            continue

        if stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            set_paragraph_spacing(p, 0, 4)
            add_inline(p, stripped[2:], base_size=11)
            i += 1
            continue

        p = doc.add_paragraph()
        set_paragraph_spacing(p, 0, 8, 1.15)
        add_inline(p, stripped, base_size=11)
        i += 1


def main():
    md = MD_PATH.read_text(encoding="utf-8")
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.2)

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = hp.add_run("CMDA Steel Yard  ·  Vehicle Entry  ·  Confidential intranet")
    set_run_font(run, size=9, color=MUTED)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(fp)

    configure_styles(doc)
    add_cover(doc)
    convert(md, doc)
    doc.save(DOCX_PATH)
    print(f"Wrote {DOCX_PATH}")


if __name__ == "__main__":
    main()
