"""Styling and formatting helpers for the PatentIQ B.Tech Project Report.
Enforces official BCSE497J formatting rules:
- Page size: A4 (21.0 x 29.7 cm)
- Margins: Left 3.81 cm (1.5 in), Right/Top/Bottom 2.54 cm (1.0 in)
- Font: Times New Roman throughout
- Normal body text: 12pt, 1.5 line spacing, Justified, 6pt after
- Chapter headings: 16pt Bold Centered
- Section headings: 14pt Bold ALL CAPS Left
- Subsection headings: 12pt Bold ALL CAPS Left
- Captions: 10pt Bold Centered
- Tables: Single spaced, light gray header shading (#EAECEE), bordered
"""

import re
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

FONT_NAME = "Times New Roman"
COLOR_BLACK = RGBColor(0, 0, 0)
COLOR_NAVY = RGBColor(16, 44, 87)
COLOR_MUTED = RGBColor(80, 80, 80)

_XML_ILLEGAL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]')

def clean_xml_string(text: str) -> str:
    """Sanitizes strings to ensure full compatibility with the XML/docx specification."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return _XML_ILLEGAL_CHARS.sub('', text)


def configure_document_setup(doc: docx.Document):
    """Sets default Normal style and document defaults."""
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(12)
    style.font.color.rgb = COLOR_BLACK
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def set_section_margins(section, left_cm=3.81, right_cm=2.54, top_cm=2.54, bottom_cm=2.54):
    """Applies official A4 page dimensions and margins to a Word section."""
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(left_cm)
    section.right_margin = Cm(right_cm)
    section.top_margin = Cm(top_cm)
    section.bottom_margin = Cm(bottom_cm)


def add_page_number(run):
    """Inserts a dynamic PAGE number field into a run."""
    fldSimple = OxmlElement("w:fldSimple")
    fldSimple.set(qn("w:instr"), "PAGE")
    run._r.append(fldSimple)


def set_section_numbering_format(section, fmt="decimal", start=1):
    """Configures section page numbering format (lowerRoman or decimal)."""
    pgNumType = OxmlElement("w:pgNumType")
    pgNumType.set(qn("w:fmt"), fmt)
    if start is not None:
        pgNumType.set(qn("w:start"), str(start))
    section._sectPr.append(pgNumType)


def add_chapter_heading(doc, chapter_num, title):
    """Adds a standardized Chapter Heading (16pt Bold, Centered)."""
    p_num = doc.add_paragraph()
    p_num.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_num.paragraph_format.space_before = Pt(18)
    p_num.paragraph_format.space_after = Pt(4)
    p_num.paragraph_format.line_spacing = 1.0
    run_num = p_num.add_run(clean_xml_string(f"CHAPTER {chapter_num}"))
    run_num.font.name = FONT_NAME
    run_num.font.size = Pt(16)
    run_num.font.bold = True
    run_num.font.color.rgb = COLOR_BLACK

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(18)
    p_title.paragraph_format.line_spacing = 1.15
    run_title = p_title.add_run(clean_xml_string(title.upper()))
    run_title.font.name = FONT_NAME
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_BLACK
    return p_title


def add_section_heading(doc, text):
    """Adds a Section Heading (14pt Bold ALL CAPS Left)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    run = p.add_run(clean_xml_string(text.upper()))
    run.font.name = FONT_NAME
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = COLOR_BLACK
    return p


def add_subsection_heading(doc, text):
    """Adds a Subsection Heading (12pt Bold ALL CAPS Left)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    run = p.add_run(clean_xml_string(text.upper()))
    run.font.name = FONT_NAME
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = COLOR_BLACK
    return p


def add_subsubsection_heading(doc, text):
    """Adds a Sub-subsection Heading (12pt Bold Title Case Left)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    run = p.add_run(clean_xml_string(text))
    run.font.name = FONT_NAME
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = COLOR_BLACK
    return p


def add_body_p(doc, text, bold_prefix=None, italic_prefix=None):
    """Adds a standard body paragraph (12pt Times New Roman, 1.5 line spacing, Justified, 6pt after)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.space_before = Pt(0)

    if bold_prefix:
        r_pre = p.add_run(clean_xml_string(bold_prefix))
        r_pre.font.name = FONT_NAME
        r_pre.font.size = Pt(12)
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_BLACK

    if italic_prefix:
        r_pre2 = p.add_run(clean_xml_string(italic_prefix))
        r_pre2.font.name = FONT_NAME
        r_pre2.font.size = Pt(12)
        r_pre2.font.italic = True
        r_pre2.font.color.rgb = COLOR_BLACK

    r = p.add_run(clean_xml_string(text))
    r.font.name = FONT_NAME
    r.font.size = Pt(12)
    r.font.color.rgb = COLOR_BLACK
    return p


def add_bullet_p(doc, bold_title, body_text):
    """Adds an indented bullet point with a bold title and body text."""
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.space_before = Pt(0)

    r_title = p.add_run(clean_xml_string(bold_title))
    r_title.font.name = FONT_NAME
    r_title.font.size = Pt(12)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_BLACK

    r_body = p.add_run(clean_xml_string(f" {body_text}"))
    r_body.font.name = FONT_NAME
    r_body.font.size = Pt(12)
    r_body.font.color.rgb = COLOR_BLACK
    return p


def add_table_data(doc, table_num, table_title, headers, rows, col_widths=None):
    """Creates a beautifully styled, publication-ready table with caption above."""
    # Caption above table
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(12)
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(clean_xml_string(f"Table {table_num}: {table_title}"))
    r_cap.font.name = FONT_NAME
    r_cap.font.size = Pt(11)
    r_cap.font.bold = True
    r_cap.font.color.rgb = COLOR_BLACK

    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = clean_xml_string(h)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.0
        for run in p.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = COLOR_BLACK
        # Shading #EAECEE
        shd = parse_xml(r'<w:shd {} w:fill="EAECEE"/>'.format(nsdecls('w')))
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)

    # Data Rows
    for r_idx, row in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = clean_xml_string(str(val))
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            for run in p.runs:
                run.font.name = FONT_NAME
                run.font.size = Pt(10)
                run.font.color.rgb = COLOR_BLACK

    # Set cell borders
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(
                r'<w:tcBorders {}><w:top w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/>'
                r'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/>'
                r'<w:left w:val="none"/><w:right w:val="none"/></w:tcBorders>'.format(nsdecls('w'))
            )
            tcPr.append(tcBorders)

    # Col widths if given
    if col_widths:
        for row in table.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Cm(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return table


def add_figure_image(doc, img_path, fig_num, fig_title, width_cm=14.5):
    """Inserts a centered image with caption below."""
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(10)
    p_img.paragraph_format.space_after = Pt(4)
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=Cm(width_cm))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(12)
    p_cap.paragraph_format.line_spacing = 1.0
    r_cap = p_cap.add_run(f"Figure {fig_num}: {fig_title}")
    r_cap.font.name = FONT_NAME
    r_cap.font.size = Pt(10)
    r_cap.font.bold = True
    r_cap.font.color.rgb = COLOR_BLACK
    return p_cap
