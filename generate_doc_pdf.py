"""
Converts Virtual_Daycare_Project_Documentation.md to a PDF
using ReportLab — no system libraries required on Windows.
"""

import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

MD_FILE = "Virtual_Daycare_Project_Documentation.md"
PDF_FILE = "Virtual_Daycare_Project_Documentation.pdf"

# ── Colour palette (monochrome / grayscale — professional look) ──
BLACK      = colors.HexColor("#000000")
DARK_GRAY  = colors.HexColor("#222222")
MID_GRAY   = colors.HexColor("#555555")
LIGHT_GRAY = colors.HexColor("#888888")
RULE_GRAY  = colors.HexColor("#cccccc")
TABLE_HEADER_BG = colors.HexColor("#2c2c2c")
TABLE_ALT_BG    = colors.HexColor("#f5f5f5")
TABLE_BORDER    = colors.HexColor("#999999")

def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "DocTitle",
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=34,
            textColor=BLACK,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "DocMeta",
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=3,
        ),
        "h1": ParagraphStyle(
            "H1",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=22,
            textColor=BLACK,
            spaceBefore=18,
            spaceAfter=8,
            borderPad=0,
        ),
        "h2": ParagraphStyle(
            "H2",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=DARK_GRAY,
            spaceBefore=14,
            spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "H3",
            fontName="Helvetica-BoldOblique",
            fontSize=11,
            leading=16,
            textColor=DARK_GRAY,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=DARK_GRAY,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=DARK_GRAY,
            leftIndent=18,
            spaceAfter=3,
            bulletIndent=6,
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=8.5,
            leading=12,
            textColor=DARK_GRAY,
            backColor=colors.HexColor("#f0f0f0"),
            leftIndent=12,
            rightIndent=12,
            spaceAfter=8,
            spaceBefore=4,
            borderPad=6,
        ),
        "toc_h1": ParagraphStyle(
            "TocH1",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=BLACK,
            leftIndent=0,
            spaceAfter=2,
        ),
        "toc_h2": ParagraphStyle(
            "TocH2",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=DARK_GRAY,
            leftIndent=14,
            spaceAfter=1,
        ),
        "toc_h3": ParagraphStyle(
            "TocH3",
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=13,
            textColor=MID_GRAY,
            leftIndent=26,
            spaceAfter=1,
        ),
    }
    return styles


def escape_xml(text):
    """Escape characters that break ReportLab Paragraph XML."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def inline_format(text, styles):
    """Convert inline markdown (bold, italic, code) to ReportLab XML."""
    # Bold + italic: ***text*** or ___text___
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Inline code: `text`
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" size="9">\1</font>', text)
    return text


def parse_table(lines):
    """Parse markdown table lines into a list of row lists."""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith("|"):
            line = line.strip("|")
        # Skip separator rows like |---|---|
        if re.match(r'^[\s\|\-:]+$', line):
            continue
        cells = [c.strip() for c in line.split("|")]
        rows.append(cells)
    return rows


def build_rl_table(rows, styles):
    """Build a ReportLab Table from a list of row lists."""
    if not rows:
        return None

    header = rows[0]
    data_rows = rows[1:]

    # Determine column widths based on page width
    page_width = A4[0] - 3.6 * cm   # left + right margins
    n_cols = len(header)
    col_w = page_width / n_cols

    table_data = []

    # Header row
    header_cells = [
        Paragraph(f"<b><font color='white'>{escape_xml(h)}</font></b>",
                  ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=9,
                                 leading=12, textColor=colors.white))
        for h in header
    ]
    table_data.append(header_cells)

    # Data rows
    for i, row in enumerate(data_rows):
        # Pad or trim to match header count
        while len(row) < n_cols:
            row.append("")
        row = row[:n_cols]
        cells = [
            Paragraph(escape_xml(cell),
                      ParagraphStyle("TD", fontName="Helvetica", fontSize=9,
                                     leading=12, textColor=DARK_GRAY))
            for cell in row
        ]
        table_data.append(cells)

    t = Table(table_data, colWidths=[col_w] * n_cols, repeatRows=1)

    # Style
    ts = TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING",    (0, 0), (-1, 0), 5),
        # Data rows
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ALT_BG]),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Borders
        ("GRID",       (0, 0), (-1, -1), 0.4, TABLE_BORDER),
        ("LINEBELOW",  (0, 0), (-1, 0),  1.0, BLACK),
    ])
    t.setStyle(ts)
    return t


def md_to_flowables(md_text, styles):
    """Convert markdown text to a list of ReportLab flowables."""
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    # Title page flag
    title_done = False

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # ── Code fence ──────────────────────────────────────────
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                # Split into chunks to avoid very tall cells
                for chunk in [code_text[j:j+2000] for j in range(0, len(code_text), 2000)]:
                    escaped = escape_xml(chunk).replace("\n", "<br/>")
                    flowables.append(
                        Paragraph(escaped, styles["code"])
                    )
                flowables.append(Spacer(1, 4))
            i += 1
            continue

        if in_code_block:
            code_lines.append(raw.rstrip())
            i += 1
            continue

        # ── Table detection ─────────────────────────────────────
        if stripped.startswith("|"):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            i += 1
            continue
        else:
            if in_table:
                in_table = False
                rows = parse_table(table_lines)
                t = build_rl_table(rows, styles)
                if t:
                    flowables.append(Spacer(1, 6))
                    flowables.append(t)
                    flowables.append(Spacer(1, 10))
                table_lines = []

        # ── Headings ─────────────────────────────────────────────
        if stripped.startswith("#### "):
            text = escape_xml(stripped[5:].strip())
            text = inline_format(text, styles)
            flowables.append(Paragraph(f"<b>{text}</b>", styles["h3"]))

        elif stripped.startswith("### "):
            text = escape_xml(stripped[4:].strip())
            text = inline_format(text, styles)
            flowables.append(Paragraph(text, styles["h3"]))

        elif stripped.startswith("## "):
            text = escape_xml(stripped[3:].strip())
            text = inline_format(text, styles)
            flowables.append(Paragraph(text, styles["h2"]))
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                        color=RULE_GRAY, spaceAfter=4))

        elif stripped.startswith("# "):
            text = escape_xml(stripped[2:].strip())
            # First H1 = document title page
            if not title_done:
                flowables.append(Spacer(1, 2.5 * cm))
                flowables.append(Paragraph(text, styles["title"]))
                title_done = True
            else:
                flowables.append(PageBreak())
                flowables.append(Paragraph(text, styles["h1"]))
                flowables.append(HRFlowable(width="100%", thickness=1.2,
                                            color=BLACK, spaceAfter=8))

        # ── Horizontal rule ──────────────────────────────────────
        elif stripped in ("---", "***", "___"):
            flowables.append(Spacer(1, 4))
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                        color=RULE_GRAY))
            flowables.append(Spacer(1, 4))

        # ── Bullet / numbered list ───────────────────────────────
        elif re.match(r'^[-*+] ', stripped):
            text = escape_xml(stripped[2:].strip())
            text = inline_format(text, styles)
            flowables.append(Paragraph(f"\u2022&nbsp;&nbsp;{text}", styles["bullet"]))

        elif re.match(r'^\d+\. ', stripped):
            text = re.sub(r'^\d+\. ', '', stripped)
            text = escape_xml(text)
            text = inline_format(text, styles)
            num = re.match(r'^(\d+)\.', stripped).group(1)
            flowables.append(Paragraph(f"<b>{num}.</b>&nbsp;&nbsp;{text}", styles["bullet"]))

        # ── Bold-prefixed label lines (e.g. **Label:** text) ─────
        elif stripped.startswith("**") and ":**" in stripped:
            text = escape_xml(stripped)
            text = inline_format(text, styles)
            flowables.append(Paragraph(text, styles["body"]))

        # ── Empty line ───────────────────────────────────────────
        elif stripped == "" or stripped == "&nbsp;":
            flowables.append(Spacer(1, 5))

        # ── Regular paragraph ────────────────────────────────────
        else:
            text = escape_xml(stripped)
            if not text:
                i += 1
                continue
            text = inline_format(text, styles)
            # Detect meta lines (key: value pattern at top of doc)
            if re.match(r'^\*\*[^*]+\*\*:', text) or re.match(r'^_.*_$', text):
                flowables.append(Paragraph(text, styles["meta"]))
            else:
                flowables.append(Paragraph(text, styles["body"]))

        i += 1

    # Flush any remaining table
    if in_table and table_lines:
        rows = parse_table(table_lines)
        t = build_rl_table(rows, styles)
        if t:
            flowables.append(t)
            flowables.append(Spacer(1, 10))

    return flowables


def add_page_number(canvas, doc):
    """Footer with page number on every page after the title."""
    canvas.saveState()
    page_num = canvas.getPageNumber()
    if page_num > 1:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(LIGHT_GRAY)
        canvas.drawCentredString(
            A4[0] / 2, 1.2 * cm,
            f"Virtual Daycare Platform  |  Project Documentation  |  Page {page_num}"
        )
        canvas.setStrokeColor(RULE_GRAY)
        canvas.setLineWidth(0.4)
        canvas.line(1.8 * cm, 1.6 * cm, A4[0] - 1.8 * cm, 1.6 * cm)
    canvas.restoreState()


def generate_pdf():
    if not os.path.exists(MD_FILE):
        print(f"ERROR: {MD_FILE} not found.")
        return

    print(f"Reading {MD_FILE} ...")
    with open(MD_FILE, "r", encoding="utf-8") as f:
        md_text = f.read()

    styles = build_styles()

    doc = SimpleDocTemplate(
        PDF_FILE,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.2 * cm,
        title="Virtual Daycare Platform — Project Documentation",
        author="Little Learners Virtual Daycare",
        subject="Full Project Documentation",
    )

    print("Building flowables ...")
    flowables = md_to_flowables(md_text, styles)

    print(f"Writing PDF to {PDF_FILE} ...")
    doc.build(flowables, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"\nDone! PDF saved: {os.path.abspath(PDF_FILE)}")
    size_kb = os.path.getsize(PDF_FILE) // 1024
    print(f"File size: {size_kb} KB")


if __name__ == "__main__":
    generate_pdf()
