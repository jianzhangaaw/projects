"""通用 markdown → docx 转换（支持标题、段落、加粗、表格、有序/无序列表、图片）。

排版规格：正文宋体 12pt + Times New Roman + w:hint="eastAsia"；
一级标题 14pt 加粗，二级 13pt，三级 12pt；正文首行缩进 2 字符、行距 1.25。
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

CN_FONT = "宋体"
EN_FONT = "Times New Roman"


def style_run(run, size=12, bold=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = EN_FONT
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), EN_FONT)
    rFonts.set(qn("w:hAnsi"), EN_FONT)
    rFonts.set(qn("w:eastAsia"), CN_FONT)
    rFonts.set(qn("w:hint"), "eastAsia")


def add_rich(p, text, size=12, bold=False):
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            style_run(p.add_run(part[2:-2]), size=size, bold=True)
        elif part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1])
            style_run(r, size=size - 1, bold=bold)
            r.font.name = "Consolas"
            r._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:ascii"), "Consolas")
        else:
            style_run(p.add_run(part), size=size, bold=bold)


def new_doc():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin = sec.bottom_margin = Cm(2.5)
    return doc


def para(doc, text, size=12, bold=False, indent=2, align=None, after=6, spacing=1.25, hanging=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = spacing
    if hanging:
        pf.left_indent = Pt(size * 2)
        pf.first_line_indent = Pt(-size * 2)
    elif indent:
        pf.first_line_indent = Pt(size * indent)
    if align is not None:
        p.alignment = align
    add_rich(p, text, size=size, bold=bold)
    return p


def add_table(doc, rows, size=10.5):
    if not rows:
        return
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            add_rich(p, str(cell), size=size, bold=(i == 0))
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return t


def md_to_docx(md_text: str, doc=None, img_base: Path | None = None):
    doc = doc or new_doc()
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            rows = []
            header = [c.strip() for c in s.strip("|").split("|")]
            rows.append(header)
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            add_table(doc, rows)
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
            continue
        if s.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", s)
            if m and img_base:
                cap, src = m.group(1), m.group(2)
                p = img_base / src
                if p.exists():
                    doc.add_picture(str(p), width=Cm(15.5))
                    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    para(doc, cap, size=10, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
                else:
                    para(doc, f"[缺图：{src}]", size=10, indent=0)
            i += 1
            continue
        if s.startswith("#### "):
            para(doc, s[5:], size=12, bold=True, indent=0, after=6)
        elif s.startswith("### "):
            para(doc, s[4:], size=13, bold=True, indent=0, after=6)
        elif s.startswith("## "):
            para(doc, s[3:], size=14, bold=True, indent=0, after=8)
        elif s.startswith("# "):
            para(doc, s[2:], size=16, bold=True, indent=0,
                 align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
        elif re.match(r"^[-*] ", s):
            para(doc, "· " + s[2:], indent=1, after=3)
        elif re.match(r"^\d+\. ", s):
            para(doc, s, indent=1, after=3)
        elif s.startswith("> "):
            para(doc, s[2:], size=10.5, indent=1, after=6)
        else:
            para(doc, s)
        i += 1
    return doc
