"""Generates the branded VoltPro Electrodata Solutions quote PDF with ReportLab."""
from io import BytesIO
import os

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image,
)

INK = colors.HexColor("#101A2C")
AMBER = colors.HexColor("#C9822F")   # print-safe darker amber (screen amber is too light on white)
MUTED = colors.HexColor("#5B6B80")
LINE = colors.HexColor("#D8DEE8")
PANEL = colors.HexColor("#F4F6F9")

STYLES = {
    "brand": ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=17, textColor=INK, leading=20),
    "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=MUTED, leading=11),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=14),
    "body_muted": ParagraphStyle("body_muted", fontName="Helvetica", fontSize=9, textColor=MUTED, leading=13),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=11),
    "right": ParagraphStyle("right", fontName="Helvetica", fontSize=9.5, textColor=INK, alignment=TA_RIGHT),
    "total_label": ParagraphStyle("total_label", fontName="Helvetica-Bold", fontSize=11, textColor=INK, alignment=TA_RIGHT),
    "total_value": ParagraphStyle("total_value", fontName="Helvetica-Bold", fontSize=13, textColor=INK, alignment=TA_RIGHT),
}


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    y = 18 * mm
    canvas.line(20 * mm, y + 8, doc.pagesize[0] - 20 * mm, y + 8)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, y - 2, "VoltPro Electrodata Solutions  ·  Nairobi, Kenya  ·  +254 714 155 230  ·  info@voltproelectrodata.co.ke")
    canvas.drawRightString(doc.pagesize[0] - 20 * mm, y - 2, f"Page {doc.page}")
    canvas.restoreState()


def build_quote_pdf(quote):
    """Returns a BytesIO containing the rendered quote PDF for a Quote instance."""
    buf = BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=26 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="quote", frames=[frame], onPage=_footer)])

    story = []

    # Add logo to header if available
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'images', 'logo.jpg')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=40 * mm, height=10 * mm)
            header_table = Table(
                [[
                    logo,
                    Paragraph(
                        f"QUOTATION<br/><font size=9 color='#5B6B80'>{quote.quote_number}</font>",
                        ParagraphStyle("qmeta", fontName="Helvetica-Bold", fontSize=14, textColor=AMBER, alignment=TA_RIGHT, leading=17),
                    ),
                ]],
                colWidths=[100 * mm, 70 * mm],
            )
        except Exception:
            # Fallback to text if logo fails
            header_table = Table(
                [[
                    Paragraph("VOLTPRO<br/><font size=8 color='#C9822F'>ELECTRODATA SOLUTIONS</font>", STYLES["brand"]),
                    Paragraph(
                        f"QUOTATION<br/><font size=9 color='#5B6B80'>{quote.quote_number}</font>",
                        ParagraphStyle("qmeta", fontName="Helvetica-Bold", fontSize=14, textColor=AMBER, alignment=TA_RIGHT, leading=17),
                    ),
                ]],
                colWidths=[100 * mm, 70 * mm],
            )
    else:
        header_table = Table(
            [[
                Paragraph("VOLTPRO<br/><font size=8 color='#C9822F'>ELECTRODATA SOLUTIONS</font>", STYLES["brand"]),
                Paragraph(
                    f"QUOTATION<br/><font size=9 color='#5B6B80'>{quote.quote_number}</font>",
                    ParagraphStyle("qmeta", fontName="Helvetica-Bold", fontSize=14, textColor=AMBER, alignment=TA_RIGHT, leading=17),
                ),
            ]],
            colWidths=[100 * mm, 70 * mm],
        )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1.4, color=INK))
    story.append(Spacer(1, 6 * mm))

    bill_to = [
        Paragraph("QUOTE FOR", STYLES["label"]),
        Paragraph(quote.client_name, STYLES["body"]),
    ]
    if quote.client_location:
        bill_to.append(Paragraph(quote.client_location, STYLES["body_muted"]))
    if quote.client_phone:
        bill_to.append(Paragraph(quote.client_phone, STYLES["body_muted"]))
    if quote.client_email:
        bill_to.append(Paragraph(quote.client_email, STYLES["body_muted"]))

    meta_rows = [
        ["Issue date", quote.issue_date.strftime("%d %b %Y") if quote.issue_date else "—"],
        ["Valid until", quote.valid_until.strftime("%d %b %Y") if quote.valid_until else "—"],
        ["Service", quote.service.title if quote.service else "—"],
        ["Status", quote.get_status_display().upper()],
    ]
    meta_table = Table(meta_rows, colWidths=[28 * mm, 42 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))

    top_row = Table([[bill_to, meta_table]], colWidths=[100 * mm, 70 * mm])
    top_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(top_row)
    story.append(Spacer(1, 8 * mm))

    if quote.notes:
        story.append(Paragraph("SCOPE", STYLES["label"]))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(quote.notes.replace("\n", "<br/>"), STYLES["body"]))
        story.append(Spacer(1, 7 * mm))

    rows = [["#", "Description", "Qty", "Unit", "Unit price", "Line total"]]
    for i, item in enumerate(quote.line_items.all(), start=1):
        rows.append([
            str(i),
            Paragraph(item.description, STYLES["body"]),
            f"{item.quantity:g}",
            item.unit,
            f"KES {item.unit_price:,.2f}",
            f"KES {item.line_total:,.2f}",
        ])
    if len(rows) == 1:
        rows.append(["", "No line items added yet.", "", "", "", ""])

    items_table = Table(
        rows, colWidths=[8 * mm, 72 * mm, 14 * mm, 16 * mm, 28 * mm, 32 * mm], repeatRows=1
    )
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    totals_rows = [
        [Paragraph("Subtotal", STYLES["total_label"]), Paragraph(f"KES {quote.subtotal:,.2f}", STYLES["right"])],
        [Paragraph(f"VAT ({quote.tax_rate:g}%)", STYLES["total_label"]), Paragraph(f"KES {quote.tax_amount:,.2f}", STYLES["right"])],
        [Paragraph("Total due", STYLES["total_label"]), Paragraph(f"KES {quote.total:,.2f}", STYLES["total_value"])],
    ]
    totals_table = Table(totals_rows, colWidths=[40 * mm, 40 * mm], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, INK),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 10 * mm))

    if quote.terms:
        story.append(Paragraph("TERMS", STYLES["label"]))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(quote.terms.replace("\n", "<br/>"), STYLES["small"]))

    doc.build(story)
    buf.seek(0)
    return buf
