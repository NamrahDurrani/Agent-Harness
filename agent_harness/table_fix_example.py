from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors

styles = getSampleStyleSheet()
cell_style = ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontSize=8, leading=10, wordWrap="CJK",  # wordWrap='CJK' forces
    # break-anywhere wrapping so a single long word/URL can't blow
    # through the column either
)
header_style = ParagraphStyle(
    "TableHeader", parent=cell_style, fontName="Helvetica-Bold",
)

raw_rows = [
    ["Disease", "Symptoms", "Affected Part", "Control Measures", "Prevalence in Punjab"],
    ["Leaf Rust (Puccinia triticina)",
     "Yellow pustules on leaf surfaces, progressing to leaf tip necrosis.",
     "Leaves and stems",
     "Resistant cultivars, fungicide sprays (e.g., azoxystrobin) during early infection.",
     "High during spring; outbreaks recorded in 2023 across all districts"],
    # ...remaining rows...
]

# THE FIX: every cell becomes a Paragraph (wraps to colWidth), not a
# bare string (which reportlab draws on one line and lets overflow).
data = [
    [Paragraph(str(cell), header_style if r == 0 else cell_style) for cell in row]
    for r, row in enumerate(raw_rows)
]

# Column widths should sum to roughly the usable page width
# (letter width 612pt - 2*36pt margins = 540pt here).
col_widths = [80, 150, 60, 150, 100]

table = Table(data, colWidths=col_widths, repeatRows=1)
# IMPORTANT: do NOT pass rowHeights=[...] — leave it unset so
# reportlab computes each row's height from the wrapped Paragraph
# content. A fixed/guessed rowHeight is the other common cause of
# this exact overlap (row N+1 starts drawing before row N's wrapped
# text has finished).
table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
]))
