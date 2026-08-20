"""
Renders a Quote as a PDF matching the reference template:
logo + company block / QUOTE title, date/quote#/customer id/valid-until
box, customer block, line-items table, totals block, terms &
conditions + signature, footer.
"""
import io
import os

from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

NAVY = colors.HexColor("#33517A")
LIGHT_BLUE = colors.HexColor("#8FAADC")
ROW_SHADE = colors.HexColor("#EFEFEF")
LINE_GREY = colors.HexColor("#B7B7B7")
TOTAL_SHADE = colors.HexColor("#C9D5EA")
HEADER_GREY = colors.HexColor("#E9E9E9")

PAGE_W, PAGE_H = letter
MARGIN = 0.5 * inch


def _wrapped_text(c, text, x, y, max_width, font="Helvetica", size=8, leading=10):
    """Very small word-wrap helper for the terms & conditions block."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split(" ")
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, font, size) > max_width and line:
            c.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = candidate
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def build_quote_pdf(quote):
    """Returns a BytesIO containing the rendered quote PDF for a Quote instance."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    # Outer border
    c.setStrokeColor(colors.HexColor("#999999"))
    c.setLineWidth(1)
    c.rect(MARGIN * 0.6, MARGIN * 0.6, PAGE_W - MARGIN * 1.2, PAGE_H - MARGIN * 1.2)

    x_left = MARGIN
    x_right = PAGE_W - MARGIN
    y = PAGE_H - MARGIN - 10

    # ---------------- Header: logo + company name / QUOTE -----------------
    logo_box_size = 0.55 * inch

    # Figure out contact lines and meta rows up front so we can size the
    # grey header band correctly before drawing anything on top of it.
    contact_lines = []
    contact_lines.append("Nairobi, Kenya")
    contact_lines.append("Website: voltproelectrodata.co.ke")
    contact_lines.append("Phone: 0715 117855 / 0724 076 047")
    contact_lines.append("Prepared by: Sales Team")

    meta_rows = [
        ("DATE", quote.issue_date.strftime("%m/%d/%Y") if quote.issue_date else "-"),
        ("QUOTE #", quote.quote_number or "-"),
        ("CUSTOMER ID", quote.client_name[:10] if quote.client_name else "-"),
        ("VALID UNTIL", quote.valid_until.strftime("%m/%d/%Y") if quote.valid_until else "-"),
    ]

    header_body_h = max(len(contact_lines) * 11, len(meta_rows) * 15)
    header_top = PAGE_H - MARGIN * 0.6 - 2
    header_bottom = y - logo_box_size - header_body_h - 12
    c.setFillColor(HEADER_GREY)
    c.rect(
        MARGIN * 0.6 + 1, header_bottom,
        PAGE_W - MARGIN * 1.2 - 2, header_top - header_bottom,
        fill=1, stroke=0,
    )

    logo_drawn = False
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'images', 'logo.png')
    if os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            iw, ih = img.getSize()
            draw_h = logo_box_size
            draw_w = draw_h * (iw / ih)
            c.drawImage(
                img, x_left, y - logo_box_size, width=draw_w,
                height=draw_h, preserveAspectRatio=True, mask="auto",
            )
            logo_drawn = True
        except Exception:
            logo_drawn = False
    if not logo_drawn:
        c.setFillColor(colors.HexColor("#D9E1F2"))
        c.rect(x_left, y - logo_box_size, logo_box_size, logo_box_size, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x_left + logo_box_size / 2, y - logo_box_size / 2 - 3, "LOGO")

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(x_left + logo_box_size + 10, y - 20, "VoltPro Electrodata Solutions")

    c.setFillColor(LIGHT_BLUE)
    c.setFont("Helvetica-Bold", 26)
    c.drawRightString(x_right, y - 14, "QUOTE")

    y -= logo_box_size + 8

    # Company contact block (left)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    cy = y
    for line in contact_lines:
        c.drawString(x_left, cy, line)
        cy -= 11

    # Date / Quote# / Customer ID / Valid until box (right)
    box_w = 2.3 * inch
    box_x = x_right - box_w
    row_h = 15
    ry = y
    c.setFont("Helvetica-Bold", 8)
    label_w = box_w * 0.5
    for label, value in meta_rows:
        c.setFillColor(colors.black)
        c.drawRightString(box_x + label_w - 4, ry - 10, label)
        c.setStrokeColor(LINE_GREY)
        c.setFillColor(colors.white)
        c.rect(box_x + label_w, ry - row_h + 2, box_w - label_w, row_h, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(box_x + label_w + 4, ry - 10, str(value))
        c.setFont("Helvetica-Bold", 8)
        ry -= row_h

    y = min(cy, ry) - 14

    # ---------------- Customer block ----------------
    c.setFillColor(NAVY)
    c.rect(x_left, y - 14, x_right - x_left, 14, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_left + 4, y - 10.5, "CUSTOMER")
    y -= 14 + 4

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_left, y - 2, quote.client_name or "")
    y -= 13
    c.setFont("Helvetica", 8.5)
    for val in [quote.client_location, quote.client_phone, quote.client_email]:
        if val:
            c.drawString(x_left, y, val)
            y -= 11

    y -= 8

    # ---------------- Scope notes ----------------
    if quote.notes:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawString(x_left, y - 2, "SCOPE")
        y -= 12
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        for line in quote.notes.split('\n'):
            y = _wrapped_text(c, line, x_left, y, x_right - x_left - 8, size=8.5, leading=11)
        y -= 8

    # ---------------- Line items table ----------------
    col_num_x = x_left
    col_desc_x = x_left + 0.3 * inch
    col_unit_x = x_left + 3.4 * inch
    col_qty_x = x_left + 4.5 * inch
    col_tax_x = x_left + 5.15 * inch
    col_amt_x = x_right

    header_h = 14
    c.setFillColor(NAVY)
    c.rect(x_left, y - header_h, x_right - x_left, header_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(col_num_x + 0.15 * inch, y - 10.5, "#")
    c.drawString(col_desc_x + 4, y - 10.5, "DESCRIPTION")
    c.drawRightString(col_unit_x, y - 10.5, "UNIT PRICE")
    c.drawCentredString(col_qty_x, y - 10.5, "QTY")
    c.drawCentredString(col_tax_x, y - 10.5, "TAXED")
    c.drawRightString(col_amt_x, y - 10.5, "AMOUNT")
    y -= header_h

    items = list(quote.line_items.all())
    row_h = 14
    min_rows = max(len(items), 8)
    c.setFont("Helvetica", 8.5)
    for i in range(min_rows):
        shade = ROW_SHADE if i % 2 == 0 else colors.white
        c.setFillColor(shade)
        c.rect(x_left, y - row_h, x_right - x_left, row_h, fill=1, stroke=0)
        if i < len(items):
            item = items[i]
            c.setFillColor(colors.black)
            c.drawCentredString(col_num_x + 0.15 * inch, y - 10, str(i + 1))
            c.drawString(col_desc_x + 4, y - 10, item.description[:100])
            c.drawRightString(col_unit_x, y - 10, f"KES {item.unit_price:,.2f}")
            c.drawCentredString(col_qty_x, y - 10, f"{item.quantity:g}")
            c.drawCentredString(col_tax_x, y - 10, "No")
            c.drawRightString(col_amt_x, y - 10, f"KES {item.line_total:,.2f}")
        else:
            c.setFillColor(colors.black)
            c.drawRightString(col_amt_x, y - 10, "-")
        y -= row_h

    c.setStrokeColor(LINE_GREY)
    c.line(x_left, y, x_right, y)

    y -= 10

    # ---------------- Totals block ----------------
    totals_box_x = x_left + 4.2 * inch
    totals = [
        ("Subtotal", f"KES {quote.subtotal:,.2f}", False),
    ]
    
    # Only show tax-related lines if tax_rate > 0
    if quote.tax_rate > 0:
        totals.extend([
            ("Taxable", f"KES {quote.subtotal:,.2f}", False),
            (f"Tax rate ({quote.tax_rate:g}%)", f"{quote.tax_rate:g}%", False),
            ("Tax due", f"KES {quote.tax_amount:,.2f}", False),
        ])
    
    totals.extend([
        ("Other", "KES 0.00", False),
        ("TOTAL", f"KES {quote.total:,.2f}", True),
    ])
    c.setFont("Helvetica", 9)
    for label, value, is_total in totals:
        if is_total:
            c.setFillColor(TOTAL_SHADE)
            c.rect(totals_box_x, y - 13, x_right - totals_box_x, 15, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(totals_box_x + 4, y - 9, "TOTAL")
            c.drawRightString(x_right - 2, y - 9, f"KES {value}")
        else:
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(totals_box_x + 4, y - 9, label)
            c.drawRightString(x_right - 2, y - 9, value)
        y -= 16

    y -= 10

    # ---------------- Terms & conditions + signature ----------------
    terms_top = y
    terms_box_h = 1.35 * inch
    terms_w = 4.6 * inch

    c.setFillColor(NAVY)
    c.rect(x_left, terms_top - 14, terms_w, 14, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_left + 4, terms_top - 10.5, "TERMS AND CONDITIONS")

    ty = terms_top - 14 - 12
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    terms_text = quote.terms if quote.terms else "50% deposit on acceptance, balance on completion. Quote valid for 30 days from issue date unless stated otherwise. Materials sourced to spec unless an alternative is agreed in writing."
    for line in terms_text.splitlines():
        if not line.strip():
            continue
        ty = _wrapped_text(c, line.strip(), x_left, ty, terms_w - 8, size=8, leading=10)

    ty -= 6
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(x_left, ty, "Customer Acceptance (sign below):")
    ty -= 26
    c.setStrokeColor(colors.black)
    c.line(x_left + 8, ty, x_left + terms_w - 20, ty)
    ty -= 11
    c.setFont("Helvetica", 8)
    c.drawString(x_left, ty, "Print Name: ____________________________")

    y = ty - 28

    # ---------------- Footer ----------------
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_W / 2, y, "If you have any questions about this price quote, please contact")
    y -= 11
    c.drawCentredString(PAGE_W / 2, y, "VoltPro Electrodata Solutions, 0715 117855 / 0724 076 047, info@voltproelectrodata.co.ke")
    y -= 16
    c.setFont("Helvetica-BoldOblique", 10)
    c.drawCentredString(PAGE_W / 2, y, "Thank You For Your Business!")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
