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

NAVY_BLUE = colors.HexColor("#2C4173")  # Professional navy blue
SLATE_BLUE = colors.HexColor("#6B7BA8")  # Soft slate blue accent
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#F5F5F5")  # Light gray for alternating rows
GRAY = colors.HexColor("#E0E0E0")  # Medium gray for lines

STYLES = {
    "brand": ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY_BLUE, leading=22),
    "company_name": ParagraphStyle("company_name", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY_BLUE, leading=18),
    "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=8, textColor=colors.black, leading=12),
    "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=SLATE_BLUE, leading=11),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, textColor=colors.black, leading=14),
    "body_muted": ParagraphStyle("body_muted", fontName="Helvetica", fontSize=9, textColor=colors.black, leading=13),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, textColor=colors.black, leading=11),
    "right": ParagraphStyle("right", fontName="Helvetica", fontSize=9.5, textColor=colors.black, alignment=TA_RIGHT),
    "total_label": ParagraphStyle("total_label", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY_BLUE, alignment=TA_RIGHT),
    "total_value": ParagraphStyle("total_value", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY_BLUE, alignment=TA_RIGHT),
    "quote_title": ParagraphStyle("quote_title", fontName="Helvetica-Bold", fontSize=24, textColor=SLATE_BLUE, leading=30),
    "meta_label": ParagraphStyle("meta_label", fontName="Helvetica-Bold", fontSize=8, textColor=NAVY_BLUE, leading=10),
    "meta_value": ParagraphStyle("meta_value", fontName="Helvetica", fontSize=8, textColor=colors.black, leading=10),
}


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(NAVY_BLUE)
    canvas.setLineWidth(1.0)
    y = 18 * mm
    canvas.line(20 * mm, y + 8, doc.pagesize[0] - 20 * mm, y + 8)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.black)
    canvas.drawString(20 * mm, y - 2, "If you have any questions about this price quote, please contact VoltPro Electrodata Solutions, +254 714 155 230, info@voltproelectrodata.co.ke")
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.setFillColor(NAVY_BLUE)
    canvas.drawCentredString(doc.pagesize[0] / 2, y - 10, "Thank You For Your Business!")
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

    # Header section - Left: Logo and company info, Right: Quote metadata
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'images', 'logo.png')
    
    # Left side: Logo and company details
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=25 * mm, height=25 * mm, hAlign='LEFT', valign='MIDDLE')
            company_left = [
                [logo, Paragraph("VoltPro Electrodata Solutions", STYLES["company_name"])],
                [Spacer(1, 2 * mm), Spacer(1, 2 * mm)],
                ["", Paragraph("Nairobi, Kenya", STYLES["contact"])],
                ["", Paragraph("Website: voltproelectrodata.co.ke", STYLES["contact"])],
                ["", Paragraph("Phone: +254 714 155 230", STYLES["contact"])],
                ["", Paragraph("Prepared by: Sales Team", STYLES["contact"])],
            ]
            company_table = Table(company_left, colWidths=[28 * mm, 60 * mm])
            company_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
        except Exception:
            company_table = Paragraph("VoltPro Electrodata Solutions", STYLES["company_name"])
    else:
        company_table = Paragraph("VoltPro Electrodata Solutions", STYLES["company_name"])
    
    # Right side: Quote metadata in boxed grid
    meta_data = [
        ["DATE", quote.issue_date.strftime("%d %b %Y") if quote.issue_date else ""],
        ["QUOTE #", quote.quote_number],
        ["CUSTOMER ID", quote.client_name[:10] if quote.client_name else ""],
        ["VALID UNTIL", quote.valid_until.strftime("%d %b %Y") if quote.valid_until else ""],
    ]
    meta_box = Table(meta_data, colWidths=[25 * mm, 25 * mm])
    meta_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY_BLUE),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    
    # Quote title
    quote_title = Paragraph("QUOTE", STYLES["quote_title"])
    
    # Combine right side
    right_header = Table([[quote_title], [Spacer(1, 3 * mm)], [meta_box]])
    right_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
    ]))
    
    # Full header
    header = Table([[company_table, right_header]], colWidths=[88 * mm, 82 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(header)
    story.append(Spacer(1, 8 * mm))

    # Customer details section with navy blue bar
    customer_bar = Table([[Paragraph("CUSTOMER", ParagraphStyle("customer_bar", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE, leading=12))]], colWidths=[170 * mm])
    customer_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(customer_bar)
    
    # Customer details
    customer_details = []
    if quote.client_name:
        customer_details.append(Paragraph(quote.client_name, STYLES["body"]))
    if quote.client_location:
        customer_details.append(Paragraph(quote.client_location, STYLES["body"]))
    if quote.client_phone:
        customer_details.append(Paragraph(quote.client_phone, STYLES["body"]))
    if quote.client_email:
        customer_details.append(Paragraph(quote.client_email, STYLES["body"]))
    
    if customer_details:
        customer_table = Table([[Paragraph("", STYLES["body"])]], colWidths=[170 * mm])
        for detail in customer_details:
            customer_table._argW[0] = 170 * mm
            customer_table._cellvalues.append([[detail]])
        customer_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(customer_table)
    
    story.append(Spacer(1, 8 * mm))

    if quote.notes:
        story.append(Paragraph("SCOPE", STYLES["label"]))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(quote.notes.replace("\n", "<br/>"), STYLES["body"]))
        story.append(Spacer(1, 7 * mm))

    # Itemized table with navy blue header and alternating rows
    rows = [["DESCRIPTION", "UNIT PRICE", "QTY", "TAXED", "AMOUNT"]]
    for i, item in enumerate(quote.line_items.all(), start=1):
        rows.append([
            Paragraph(item.description, STYLES["body"]),
            f"KES {item.unit_price:,.2f}",
            f"{item.quantity:g}",
            "No",
            f"KES {item.line_total:,.2f}",
        ])
    if len(rows) == 1:
        rows.append(["No line items added yet.", "", "", "", ""])

    items_table = Table(
        rows, colWidths=[80 * mm, 30 * mm, 20 * mm, 20 * mm, 20 * mm], repeatRows=1
    )
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, GRAY),  # Vertical divider lines
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10 * mm))

    # Bottom section: Terms and conditions (left), Totals (right)
    # Terms and conditions section
    terms_content = []
    if quote.terms:
        terms_text = quote.terms.replace("\n", "<br/>")
        # Split into numbered terms if possible
        terms_lines = terms_text.split("<br/>")
        for i, line in enumerate(terms_lines, start=1):
            terms_content.append(Paragraph(f"{i}. {line}", STYLES["small"]))
    else:
        terms_content.append(Paragraph("1. Payment is due within 30 days of invoice date.", STYLES["small"]))
        terms_content.append(Paragraph("2. Prices are valid for 30 days from quote date.", STYLES["small"]))
        terms_content.append(Paragraph("3. Goods remain the property of VoltPro until paid in full.", STYLES["small"]))
    
    terms_section = [
        [Paragraph("TERMS AND CONDITIONS", ParagraphStyle("terms_header", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY_BLUE, leading=12))],
        [Spacer(1, 2 * mm)],
    ]
    for term in terms_content:
        terms_section.append([term])
    terms_section.append([Spacer(1, 4 * mm)])
    terms_section.append([Paragraph("Customer Acceptance (sign below):", STYLES["small"])])
    terms_section.append([Spacer(1, 2 * mm)])
    terms_section.append([Paragraph("x __________________________", STYLES["small"])])
    terms_section.append([Spacer(1, 1 * mm)])
    terms_section.append([Paragraph("Print Name: __________________________", STYLES["small"])])
    
    terms_table = Table(terms_section, colWidths=[95 * mm])
    terms_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    
    # Totals calculation section
    totals_rows = [
        ["Subtotal", f"KES {quote.subtotal:,.2f}"],
        ["Taxable", f"KES {quote.subtotal:,.2f}"],
        [f"Tax rate ({quote.tax_rate:g}%)", f"{quote.tax_rate:g}%"],
        ["Tax due", f"KES {quote.tax_amount:,.2f}"],
        ["Other", "KES 0.00"],
        ["TOTAL", f"KES {quote.total:,.2f}"],
    ]
    totals_table = Table(totals_rows, colWidths=[35 * mm, 35 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -2), "Helvetica"),
        ("FONTNAME", (1, -1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -2), 9),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), NAVY_BLUE),
        ("TEXTCOLOR", (0, -1), (-1, -1), WHITE),
        ("LINEABOVE", (0, -1), (-1, -1), 1.0, GRAY),
    ]))
    
    # Combine bottom section
    bottom_section = Table([[terms_table, totals_table]], colWidths=[95 * mm, 75 * mm])
    bottom_section.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(bottom_section)

    doc.build(story)
    buf.seek(0)
    return buf
