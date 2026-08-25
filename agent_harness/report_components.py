"""
Reusable visual-component helpers for reportlab PDF generation.
Import these into document_author.py's generated scripts instead of
having the LLM freehand rounded boxes/colored cells each time — same
"give it a helper, don't hope it remembers the rules" pattern as
table_fix_example.py's make_table().

Only use what a given report actually needs — see document_author_prompt.md
§6a before reaching for stat_cards() / any chart function.
"""
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

styles = getSampleStyleSheet()

STATUS_COLORS = {
    "deficit": ("#FDECEC", "#C0392B"),   # bg, text — red
    "balanced": ("#EAF7EE", "#1E8449"),  # green
    "warning": ("#FEF6E7", "#B9770E"),   # amber
    "ok": ("#EAF7EE", "#1E8449"),
    "high": ("#FDECEC", "#C0392B"),
    "medium": ("#FEF6E7", "#B9770E"),
    "low": ("#EAF7EE", "#1E8449"),
}


def header_band(title: str, subtitle: str = "", meta_line: str = "", width: float = 468,
                 bg="#1C2B3A", fg="#FFFFFF", accent="#2ECC71"):
    """Dark title band: bold title, subtitle, then a metadata row
    (location/date/scope). Returns a flowable Table to insert first.

    FIX: subtitle/meta_line/width used to have no defaults at all — a
    call like header_band("My Title") crashed with a TypeError instead
    of degrading gracefully. width now defaults to 468pt (Letter's
    612pt minus 2x72pt/1in margins — a common content width for the
    page setups these reports typically use); pass the real
    CONTENT_WIDTH you computed if your margins differ."""
    title_style = ParagraphStyle("HBTitle", fontSize=18, leading=22,
                                  textColor=colors.HexColor(fg), fontName="Helvetica-Bold")
    sub_style = ParagraphStyle("HBSub", fontSize=11, leading=14,
                                textColor=colors.HexColor(accent), fontName="Helvetica-Bold")
    meta_style = ParagraphStyle("HBMeta", fontSize=8.5, leading=11,
                                 textColor=colors.HexColor("#CBD5E0"))
    t = Table([[Paragraph(title, title_style)],
               [Paragraph(subtitle, sub_style)],
               [Paragraph(meta_line, meta_style)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("TOPPADDING", (0, 0), (-1, 0), 14), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12), ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("LINEBELOW", (0, -1), (-1, -1), 2, colors.HexColor(accent)),
    ]))
    return t


def stat_cards(items: list[tuple[str, str]], width: float = 468,
                value_color="#1C2B3A", label_color="#7A8699"):
    """items: list of (big_value_str, short_label_str), 3-5 recommended.
    Renders as a single row of bordered cards.

    FIX: width used to have no default — see header_band's note above,
    same reasoning, same default value."""
    n = len(items)
    col_w = width / n
    value_style = ParagraphStyle("SCVal", fontSize=16, alignment=TA_CENTER,
                                  textColor=colors.HexColor(value_color), fontName="Helvetica-Bold")
    label_style = ParagraphStyle("SCLabel", fontSize=7.5, alignment=TA_CENTER,
                                  textColor=colors.HexColor(label_color), fontName="Helvetica-Bold")
    row = [[Paragraph(v, value_style) for v, _ in items],
           [Paragraph(l.upper(), label_style) for _, l in items]]
    t = Table(row, colWidths=[col_w] * n)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def alert_box(text: str, width: float = 468, level="warning"):
    """Callout box for time-sensitive / action-required content.
    level: 'warning' (amber/red) or 'info' (blue)."""
    bg, border, fg = {
        "warning": ("#FDECEC", "#C0392B", "#7B241C"),
        "info": ("#EAF3FB", "#2E86C1", "#1B4F72"),
    }[level]
    p_style = ParagraphStyle("Alert", fontSize=9.5, leading=13, textColor=colors.HexColor(fg))
    t = Table([[Paragraph(text, p_style)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor(border)),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def badge(text: str, kind: str) -> Paragraph:
    """Colored status chip for use INSIDE a table cell. kind must be a
    key in STATUS_COLORS (deficit/balanced/warning/ok/high/medium/low)."""
    bg, fg = STATUS_COLORS.get(kind.lower(), ("#EEEEEE", "#333333"))
    style = ParagraphStyle("Badge", fontSize=7.5, leading=9, alignment=TA_CENTER,
                            textColor=colors.HexColor(fg), fontName="Helvetica-Bold",
                            backColor=colors.HexColor(bg), borderPadding=3)
    return Paragraph(text.upper(), style)


def section_header(number: int, title: str, width: float = 468, accent="#2ECC71"):
    """Numbered heading with a short colored underline rule beneath it."""
    h_style = ParagraphStyle("SecHead", fontSize=12.5, leading=16,
                              fontName="Helvetica-Bold", textColor=colors.HexColor("#1C2B3A"))
    t = Table([[Paragraph(f"{number}. {title.upper()}", h_style)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.HexColor(accent)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t