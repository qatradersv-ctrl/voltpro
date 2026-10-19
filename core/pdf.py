"""
Renders a Quote as a PDF.

Two documents share this module but no longer share a layout: a quotation is
the boxed, form-like sheet a client's accounts desk expects (letterhead,
parties, ruled line table, notes beside the totals, bank details, terms and a
signature rule), while an invoice keeps the flatter layout it was given when it
was split off from the quote.
"""
import io
import os

from django.conf import settings
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
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

# The site's own palette, so the printed quotation and the web one agree.
BRAND_NAVY = colors.HexColor("#032B7A")
BRAND_AMBER = colors.HexColor("#FFCC00")
BRAND_AMBER_INK = colors.HexColor("#8A6A00")
BRAND_PANEL = colors.HexColor("#F3F4F0")
BRAND_TINT = colors.HexColor("#FFF3C4")
BRAND_LINE = colors.HexColor("#CDD1CC")
BRAND_MUTED = colors.HexColor("#4A4A4A")

A4_W, A4_H = A4
FRAME = 26          # outer hairline inset
PAD = 13            # gap between the frame and the content


def _tracked(text):
    """Letter-spacing, which ReportLab has no native support for."""
    return " ".join(text.upper())


def _box_title(c, x, y, text, size=5.8):
    c.setFillColor(BRAND_AMBER_INK)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, _tracked(text))


def _box(c, x, y, w, h):
    c.setStrokeColor(BRAND_LINE)
    c.setLineWidth(0.7)
    c.rect(x, y - h, w, h, fill=0, stroke=1)


def _grid(c, x0, x1, y0, y1, colour=BRAND_LINE, width=0.5):
    c.setStrokeColor(colour)
    c.setLineWidth(width)
    c.line(x0, y0, x1, y0)
    c.line(x0, y1, x1, y1)
    c.line(x0, y0, x0, y1)
    c.line(x1, y0, x1, y1)


def _logo(c, x, y_top, height):
    """Draw the VoltPro mark with its top edge at y_top; True if it drew."""
    path = os.path.join(settings.BASE_DIR, "static", "core", "images", "logo-mark.png")
    if not os.path.exists(path):
        return False
    try:
        img = ImageReader(path)
        iw, ih = img.getSize()
        c.drawImage(
            img, x, y_top - height, width=height * (iw / ih), height=height,
            preserveAspectRatio=True, mask="auto",
        )
        return True
    except Exception:
        return False


def _quotation_frame(c):
    c.setStrokeColor(BRAND_LINE)
    c.setLineWidth(0.8)
    c.rect(FRAME, FRAME, A4_W - 2 * FRAME, A4_H - 2 * FRAME)


def _contact_lines(site_config):
    lines = [
        "Jamii Plaza, 2nd Floor, off Police Road",
        "Mlolongo, Machakos County, Kenya",
        "P.O. Box 37, 00519 - Mlolongo",
        "Tel: 0715 117855 / 0724 076 047",
        f"Email: {getattr(site_config, 'contact_email', '') or 'info@voltpro.co.ke'}",
    ]
    pin = (getattr(site_config, "kra_pin", "") or "").strip()
    if pin:
        lines.append(f"KRA PIN: {pin}")
    return lines


def build_quote_pdf(quote):
    """Returns a BytesIO containing the rendered PDF for a Quote instance."""
    if quote.is_invoice:
        return _build_invoice_pdf(quote)
    return _build_quotation_pdf(quote)


def _build_quotation_pdf(quote):
    """The boxed quotation form. Everything is measured before anything is
    drawn, so the line table absorbs whatever the fixed blocks leave over."""
    from .models import SiteConfiguration

    site_config = SiteConfiguration.objects.first()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _quotation_frame(c)

    x_left = FRAME + PAD
    x_right = A4_W - FRAME - PAD
    table_w = x_right - x_left
    y = A4_H - FRAME - PAD

    # ---------------- letterhead ----------------
    supplier = _contact_lines(site_config)
    logo_h = 44
    head_body_h = max(16 + len(supplier) * 9.6, logo_h)

    _logo(c, x_left, y, logo_h)
    text_x = x_left + logo_h * (186 / 238) + 11
    c.setFillColor(BRAND_NAVY)
    c.setFont("Helvetica-Bold", 13.5)
    c.drawString(text_x, y - 12, "VoltPro Electrodata Solutions")
    c.setFillColor(BRAND_MUTED)
    c.setFont("Helvetica", 7.4)
    cy = y - 24
    for line in supplier:
        c.drawString(text_x, cy, line)
        cy -= 9.6

    c.setFillColor(BRAND_NAVY)
    c.setFont("Helvetica-Bold", 19)
    label = "QUOTATION"
    band_w = stringWidth(label, "Helvetica-Bold", 19) + 30
    band_x = x_right - band_w
    c.rect(band_x, y - 26, band_w, 26, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawCentredString(x_right - band_w / 2, y - 19, label)
    c.setFillColor(BRAND_AMBER)
    c.rect(band_x, y - 30, band_w, 3, fill=1, stroke=0)
    c.setFillColor(BRAND_MUTED)
    c.setFont("Helvetica", 7.4)
    c.drawRightString(x_right, y - 42, quote.quote_number or "Draft")

    y -= head_body_h + 14
    c.setStrokeColor(BRAND_LINE)
    c.setLineWidth(0.7)
    c.line(x_left, y, x_right, y)
    y -= 14

    # ---------------- parties and document meta ----------------
    bill_lines = []
    if quote.client_company and quote.client_name:
        bill_lines.append(f"Attn: {quote.client_name}")
    if quote.client_phone:
        bill_lines.append(f"Tel: {quote.client_phone}")
    if quote.client_email:
        bill_lines.append(f"Email: {quote.client_email}")
    if quote.client_kra_pin:
        bill_lines.append(f"KRA PIN: {quote.client_kra_pin}")

    site_text = quote.client_location or "To be confirmed at survey"
    party_w = table_w * 0.52
    meta_w = table_w - party_w - 16
    meta_x = x_right - meta_w
    site_rows = len(_wrap_lines(site_text, party_w - 18, size=8))

    billed_h = 30 + 11 + len(bill_lines) * 10
    site_h = 30 + site_rows * 10
    meta_rows = [
        ("Quote number", quote.quote_number or "Draft"),
        ("Date", quote.issue_date.strftime("%d/%m/%Y") if quote.issue_date else "-"),
        ("Valid until", quote.valid_until.strftime("%d/%m/%Y") if quote.valid_until else "-"),
        ("Status", quote.get_status_display()),
        ("Currency", "KES"),
    ]
    row_h = 14
    meta_h = len(meta_rows) * row_h
    parties_h = max(billed_h + 8 + site_h, meta_h)

    by = y
    _box(c, x_left, by, party_w, billed_h)
    _box_title(c, x_left + 9, by - 14, "Billed to")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x_left + 9, by - 27, quote.billing_name or "-")
    c.setFont("Helvetica", 8)
    iy = by - 27 - 11
    for line in bill_lines:
        c.drawString(x_left + 9, iy, line)
        iy -= 10

    sy = by - billed_h - 8
    _box(c, x_left, sy, party_w, site_h)
    _box_title(c, x_left + 9, sy - 14, "Site / work location")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    iy = sy - 27
    for line in _wrap_lines(site_text, party_w - 18, size=8):
        c.drawString(x_left + 9, iy, line)
        iy -= 10

    _box(c, meta_x, by, meta_w, meta_h)
    c.setFillColor(BRAND_PANEL)
    label_w = meta_w * 0.46
    c.rect(meta_x, by - meta_h, label_w, meta_h, fill=1, stroke=0)
    ry = by
    for i, (label, value) in enumerate(meta_rows):
        if i:
            c.setStrokeColor(BRAND_LINE)
            c.setLineWidth(0.4)
            c.line(meta_x, ry, meta_x + meta_w, ry)
            c.line(meta_x + label_w, ry, meta_x + label_w, ry)
        c.setFillColor(BRAND_MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(meta_x + 9, ry - 9.5, label)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawRightString(meta_x + meta_w - 9, ry - 9.5, str(value))
        ry -= row_h
    c.setStrokeColor(BRAND_LINE)
    c.setLineWidth(0.7)
    c.rect(meta_x, by - meta_h, label_w, meta_h, fill=0, stroke=1)

    y -= parties_h + 6
    c.setStrokeColor(BRAND_LINE)
    c.setLineWidth(0.7)
    c.line(x_left, y, x_right, y)
    y -= 16

    # ---------------- how much room the table has ----------------
    items = list(quote.line_items.all())
    col_w = {"line": 26, "qty": 44, "unit": 38, "price": 60, "vat": 40, "total": 64}
    desc_w = table_w - sum(col_w.values()) - 18
    row_min = 17
    row_lead = 9.4
    item_heights = []
    for item in items:
        n = max(1, len(_wrap_lines(item.description, desc_w, size=8.2)))
        item_heights.append(max(row_min, 7 + n * row_lead))

    pay_lines = quote.payment_details_list
    pay_h = 15 + 11 + len(pay_lines) * 10 + 9
    numbered_terms = [f"{i}. {line}" for i, line in enumerate(quote.terms_list, 1)]
    terms_col_w = table_w * 0.72
    terms_rows = sum(len(_wrap_lines(t, terms_col_w, size=7.6)) for t in numbered_terms)
    terms_h = 15 + 11 + terms_rows * 9.4 + 12 + 34 + 9
    notes_rows = len(_wrap_lines(quote.notes or "", desc_w + 60, size=8)) if quote.notes else 1
    close_h = max(30 + notes_rows * 10 + 9, 3 * 19 + 8)
    footer_h = 34
    bottom = FRAME + PAD + 4

    fixed = pay_h + 10 + terms_h + 8 + close_h + footer_h + 15 + 14

    head_h = 15
    cols = [
        ("LINE", col_w["line"], "c"),
        ("DESCRIPTION", desc_w + 18, "l"),
        ("QUANTITY", col_w["qty"], "r"),
        ("UNIT", col_w["unit"], "l"),
        ("UNIT PRICE", col_w["price"], "r"),
        ("VAT", col_w["vat"], "c"),
        ("TOTAL", col_w["total"], "r"),
    ]
    header_xs = []
    cx = x_left
    for name, w, _align in cols:
        header_xs.append((name, cx, w))
        cx += w

    def draw_head(y):
        """The navy column bar. Returns the y just below it."""
        c.setFillColor(BRAND_NAVY)
        c.rect(x_left, y - head_h, table_w, head_h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 6.6)
        for name, bx, bw in header_xs:
            if name in ("LINE", "VAT"):
                c.drawCentredString(bx + bw / 2, y - 10, name)
            elif name == "DESCRIPTION":
                c.drawString(bx + 6, y - 10, name)
            elif name == "UNIT":
                c.drawString(bx + 4, y - 10, name)
            else:
                c.drawRightString(bx + bw - 5, y - 10, name)
        return y - head_h

    def draw_row(y, i, h, item=None):
        """One ruled line of the table, or a blank one when item is None."""
        if i % 2 == 0:
            c.setFillColor(BRAND_PANEL)
            c.rect(x_left, y - h, table_w, h, fill=1, stroke=0)
        if item is not None:
            base = y - 11
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 8.2)
            c.drawCentredString(x_left + col_w["line"] / 2, base, str(i + 1))
            ty = base
            for line in _wrap_lines(item.description, desc_w, size=8.2) or [""]:
                c.drawString(header_xs[1][1] + 6, ty, line)
                ty -= row_lead
            c.drawRightString(header_xs[2][1] + header_xs[2][2] - 5, base, f"{item.quantity:g}")
            c.drawString(header_xs[3][1] + 4, base, (item.unit or "")[:6])
            c.drawRightString(header_xs[4][1] + header_xs[4][2] - 5, base, f"{item.unit_price:,.2f}")
            c.drawCentredString(
                header_xs[5][1] + header_xs[5][2] / 2, base, "VAT" if item.taxable else "Exempt"
            )
            c.setFillColor(BRAND_NAVY)
            c.setFont("Helvetica-Bold", 8.2)
            c.drawRightString(header_xs[6][1] + header_xs[6][2] - 5, base, f"{item.line_total:,.2f}")
        return y - h

    def rule_table(table_top, table_bottom, heights):
        _grid(c, x_left, x_right, table_bottom, table_top)
        c.setStrokeColor(BRAND_LINE)
        c.setLineWidth(0.4)
        for name, bx, bw in header_xs[1:]:
            c.line(bx, table_bottom, bx, table_top - head_h)
        yy = table_top
        for h in heights:
            yy -= h
            c.line(x_left, yy, x_right, yy)

    # A materials list can be longer than the page, and the bank details, terms
    # and signature must never be pushed off the bottom of it, so the table
    # splits and the closing blocks always sit under the last chunk of rows.
    idx = 0
    page = 1
    while True:
        if page > 1:
            c.showPage()
            _quotation_frame(c)
            y = A4_H - FRAME - PAD
            c.setFillColor(BRAND_NAVY)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_left, y - 10, "VoltPro Electrodata Solutions")
            c.setFillColor(BRAND_MUTED)
            c.setFont("Helvetica", 7.6)
            c.drawRightString(
                x_right, y - 10,
                f"Quotation {quote.quote_number or ''} continued — {quote.billing_name}".strip(),
            )
            y -= 22
            c.setStrokeColor(BRAND_LINE)
            c.setLineWidth(0.7)
            c.line(x_left, y, x_right, y)
            y -= 14
        y = draw_head(y)
        table_top = y
        limit = y - fixed - bottom - 14
        heights = []
        while idx < len(items) and (not heights or y - item_heights[idx] > limit):
            heights.append(item_heights[idx])
            y = draw_row(y, idx, item_heights[idx], items[idx])
            idx += 1
        if idx >= len(items):
            blanks = max(0, min(6, int((y - limit) // row_min))) if page == 1 else 0
            for n in range(blanks):
                heights.append(row_min)
                y = draw_row(y, len(items) + n, row_min)
        rule_table(table_top, y, heights)
        if idx >= len(items):
            break
        page += 1
    y -= 14

    # ---------------- notes and totals ----------------
    totals = [
        ("Subtotal", f"Ksh {quote.subtotal:,.2f}"),
        (f"VAT ({float(quote.tax_rate):g}%)", f"Ksh {quote.tax_amount:,.2f}"),
        ("Total", f"Ksh {quote.total:,.2f}"),
    ]
    totals_w = 190
    totals_x = x_right - totals_w
    _box(c, x_left, y, table_w, close_h)
    c.setStrokeColor(BRAND_LINE)
    c.setLineWidth(0.7)
    c.line(totals_x, y, totals_x, y - close_h)
    _box_title(c, x_left + 9, y - 14, "Notes / scope of work")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    ny = y - 28
    body = quote.notes or "Nothing beyond the line items above."
    for line in _wrap_lines(body, totals_x - x_left - 18, size=8):
        if line and not quote.notes:
            c.setFont("Helvetica-Oblique", 8)
        c.drawString(x_left + 9, ny, line)
        ny -= 10
    ty = y
    trow = (close_h - 4) / 3
    for i, (label, value) in enumerate(totals):
        if i < 2:
            c.setFillColor(BRAND_PANEL)
            c.rect(totals_x, ty - trow, totals_w * 0.45, trow, fill=1, stroke=0)
            c.setFillColor(BRAND_MUTED)
            c.setFont("Helvetica", 8)
            c.drawString(totals_x + 9, ty - trow + 9, label)
            c.setFillColor(colors.black)
            c.drawRightString(x_right - 9, ty - trow + 9, value)
        else:
            c.setFillColor(BRAND_TINT)
            c.rect(totals_x, ty - trow, totals_w, trow, fill=1, stroke=0)
            c.setStrokeColor(BRAND_NAVY)
            c.setLineWidth(1.1)
            c.line(totals_x, ty, x_right, ty)
            c.setFillColor(BRAND_NAVY)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(totals_x + 9, ty - trow + 9.5, label)
            c.drawRightString(x_right - 9, ty - trow + 9.5, value)
        ty -= trow
    y -= close_h + 10

    # ---------------- payment and bank details ----------------
    _box(c, x_left, y, table_w, pay_h)
    c.setFillColor(BRAND_NAVY)
    c.rect(x_left, y - 15, table_w, 15, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7.4)
    c.drawString(x_left + 9, y - 10.5, "PAYMENT & BANK DETAILS")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    py = y - 15 - 11
    for line in pay_lines:
        c.drawString(x_left + 9, py, line)
        py -= 10
    y -= pay_h + 10

    # ---------------- terms and signature ----------------
    _box(c, x_left, y, table_w, terms_h)
    c.setFillColor(BRAND_NAVY)
    c.rect(x_left, y - 15, table_w, 15, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7.4)
    c.drawString(x_left + 9, y - 10.5, "TERMS AND CONDITIONS")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7.6)
    ty = y - 15 - 11
    for line in numbered_terms:
        ty = _wrapped_text(c, line, x_left + 9, ty, terms_col_w, size=7.6, leading=9.4)
    ty -= 10
    c.setStrokeColor(BRAND_MUTED)
    c.setLineWidth(0.6)
    c.line(x_left + 9, ty - 22, x_left + 9 + 190, ty - 22)
    c.setFillColor(BRAND_MUTED)
    c.setFont("Helvetica", 6)
    c.drawString(x_left + 9, ty - 33, _tracked("Customer acceptance - sign, print name and date"))
    y = y - terms_h - 16

    # ---------------- footer ----------------
    c.setFillColor(BRAND_MUTED)
    c.setFont("Helvetica", 7.6)
    c.drawCentredString(
        A4_W / 2, y,
        "Questions about any line above? Call 0715 117855 or write to "
        f"{getattr(site_config, 'contact_email', '') or 'info@voltpro.co.ke'}",
    )
    y -= 12
    c.setFillColor(BRAND_NAVY)
    c.setFont("Helvetica-Bold", 8.6)
    c.drawCentredString(A4_W / 2, y, "Thank you for your business.")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def _wrapped_text(c, text, x, y, max_width, font="Helvetica", size=8, leading=10):
    """Very small word-wrap helper for the terms & conditions block."""
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


def _wrap_lines(text, max_width, font="Helvetica", size=8):
    """The lines _wrapped_text would draw, without drawing them."""
    lines = []
    line = ""
    for word in text.split(" "):
        candidate = f"{line} {word}".strip() if line else word
        if stringWidth(candidate, font, size) > max_width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def _build_invoice_pdf(quote):
    """Build an invoice with wrapped text and a table that can span pages."""
    from html import escape
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from .models import SiteConfiguration

    buf = io.BytesIO()
    site_config = SiteConfiguration.objects.first()
    business_pin = (getattr(site_config, "kra_pin", "") or "").strip()
    document_number = quote.invoice_number or quote.quote_number or "Draft"
    usable_width = PAGE_W - 2 * MARGIN
    body = ParagraphStyle("InvoiceBody", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.black)
    small = ParagraphStyle("InvoiceSmall", parent=body, fontSize=7.5, leading=9)
    heading = ParagraphStyle("InvoiceHeading", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=NAVY, spaceBefore=7, spaceAfter=4)
    customer_name = ParagraphStyle("InvoiceCustomerName", parent=body, fontName="Helvetica-Bold", fontSize=9.5, leading=12, spaceAfter=2)
    table_body = ParagraphStyle("InvoiceTableBody", parent=small, fontSize=8, leading=10)
    table_right = ParagraphStyle("InvoiceTableRight", parent=table_body, alignment=TA_RIGHT)
    table_header = ParagraphStyle(
        "InvoiceTableHeader", parent=table_body, fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    def draw_page(c, doc):
        c.saveState()
        c.setStrokeColor(colors.HexColor("#999999"))
        c.setLineWidth(0.8)
        c.rect(MARGIN * 0.6, MARGIN * 0.6, PAGE_W - MARGIN * 1.2, PAGE_H - MARGIN * 1.2)
        c.setFillColor(colors.HexColor("#F2F4F7"))
        c.rect(MARGIN * 0.6 + 1, PAGE_H - 104, PAGE_W - MARGIN * 1.2 - 2, 72, fill=1, stroke=0)
        logo_size = 0.48 * inch
        _logo(c, MARGIN, PAGE_H - 42, logo_size)
        text_x = MARGIN + logo_size + 10
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(text_x, PAGE_H - 46, "VoltPro Electrodata Solutions")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7.5)
        contact_lines = [
            "Jamii Plaza, 2nd Floor, off Police Road, Mlolongo, Machakos County",
            "Website: voltproelectrodata.co.ke",
            "Phone: 0715 117855 / 0724 076 047",
            f"Email: {getattr(site_config, 'contact_email', '') or 'info@voltpro.co.ke'}",
        ]
        if business_pin:
            contact_lines.append(f"KRA PIN: {business_pin}")
        cy = PAGE_H - 59
        for line in contact_lines:
            c.drawString(text_x, cy, line)
            cy -= 9
        c.setFillColor(LIGHT_BLUE)
        c.setFont("Helvetica-Bold", 22)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 45, "INVOICE")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 61, document_number)
        if doc.page > 1:
            c.setFillColor(BRAND_MUTED)
            c.setFont("Helvetica-Oblique", 7.5)
            c.drawRightString(PAGE_W - MARGIN, PAGE_H - 74, "Continued")
        footer_y = MARGIN * 0.6 + 17
        c.setStrokeColor(LINE_GREY)
        c.setLineWidth(0.5)
        c.line(MARGIN, footer_y + 9, PAGE_W - MARGIN, footer_y + 9)
        c.setFillColor(BRAND_MUTED)
        c.setFont("Helvetica", 7.2)
        c.drawCentredString(PAGE_W / 2, footer_y, f"VoltPro Electrodata Solutions  |  0715 117855 / 0724 076 047  |  Page {doc.page}")
        c.restoreState()

    def para(value, style=body):
        text = escape(str(value or "")).replace("\r\n", "\n").replace("\r", "\n")
        return Paragraph(text.replace("\n", "<br/>"), style)

    story = []
    band_style = ParagraphStyle("InvoiceCustomerBand", fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=colors.white)
    band = Table([[Paragraph("CUSTOMER", band_style)]], colWidths=[usable_width])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    customer_details = []
    if quote.client_company and quote.client_name:
        customer_details.append(f"Attn: {quote.client_name}")
    for label, value in (("Location", quote.client_location), ("Phone", quote.client_phone), ("Email", quote.client_email), ("KRA PIN", quote.client_kra_pin)):
        if value:
            customer_details.append(f"{label}: {value}")
    story.extend([band, Spacer(1, 5), para(quote.billing_name or "-", customer_name)])
    story.extend(para(value, body) for value in customer_details)
    story.append(Spacer(1, 5))
    if quote.notes:
        story.extend([Paragraph("SCOPE", heading), para(quote.notes), Spacer(1, 5)])

    col_widths = [24, 254, 76, 36, 48, usable_width - 438]
    table_data = [[
        para("#", table_header), para("DESCRIPTION", table_header),
        para("UNIT PRICE", table_header), para("QTY", table_header),
        para("TAXED", table_header), para("AMOUNT", table_header),
    ]]
    for index, item in enumerate(quote.line_items.all(), 1):
        table_data.append([
            para(index, table_right), para(item.description, table_body),
            para(f"KES {item.unit_price:,.2f}", table_right), para(f"{item.quantity:g}", table_right),
            para("Yes" if item.taxable else "No", table_right), para(f"KES {item.line_total:,.2f}", table_right),
        ])
    item_table = LongTable(table_data, colWidths=col_widths, repeatRows=1, splitByRow=1, hAlign="LEFT")
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_SHADE]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([Paragraph("LINE ITEMS", heading), item_table, Spacer(1, 8)])

    totals = [("Subtotal", f"KES {quote.subtotal:,.2f}")]
    if quote.tax_rate > 0:
        totals.extend([("Taxable", f"KES {quote.taxable_subtotal:,.2f}"), (f"Tax rate ({quote.tax_rate:g}%)", f"{quote.tax_rate:g}%"), ("Tax due", f"KES {quote.tax_amount:,.2f}")])
    totals.extend([("Other", "KES 0.00"), ("AMOUNT DUE", f"KES {quote.total:,.2f}")])
    totals_table = Table([[para(label, body), para(value, table_right)] for label, value in totals], colWidths=[usable_width - 170, 170], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("LINEABOVE", (0, 0), (-1, 0), 0.6, LINE_GREY),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, NAVY), ("BACKGROUND", (0, -1), (-1, -1), TOTAL_SHADE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([
        totals_table, Spacer(1, 10),
        Paragraph("If you have any questions about this invoice, please contact VoltPro Electrodata Solutions at 0715 117855 / 0724 076 047 or info@voltproelectrodata.co.ke.", small),
        Spacer(1, 5), Paragraph("Thank You For Your Business!", ParagraphStyle("InvoiceThanks", parent=body, fontName="Helvetica-BoldOblique", fontSize=10, leading=13)),
    ])
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=118, bottomMargin=48, title=f"Invoice {document_number}", author="VoltPro Electrodata Solutions", allowSplitting=1)
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    buf.seek(0)
    return buf

def build_sales_report(queryset):
    """Generate a sales report PDF for selected quotes."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from datetime import datetime
    from decimal import Decimal
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    PAGE_W, PAGE_H = A4
    
    # Colors
    NAVY = colors.HexColor("#16233A")
    ACCENT = colors.HexColor("#F5A623")
    
    # Header
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 80, PAGE_W, 80, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, PAGE_H - 50, "SALES REPORT")
    c.setFont("Helvetica", 12)
    c.drawString(50, PAGE_H - 70, f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}")
    
    # Summary stats
    total_quotes = queryset.count()
    total_amount = sum(q.total for q in queryset)
    total_vat = sum(q.tax_amount for q in queryset)
    total_subtotal = sum(q.subtotal for q in queryset)
    
    y = PAGE_H - 120
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Total Quotes: {total_quotes}")
    y -= 25
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Total Revenue: KES {total_amount:,.2f}")
    y -= 20
    c.drawString(50, y, f"Total VAT: KES {total_vat:,.2f}")
    y -= 20
    c.drawString(50, y, f"Total Subtotal: KES {total_subtotal:,.2f}")
    
    # Table header
    y -= 40
    c.setFillColor(NAVY)
    c.rect(50, y - 30, PAGE_W - 100, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y - 20, "Quote #")
    c.drawString(150, y - 20, "Client")
    c.drawString(350, y - 20, "Status")
    c.drawString(450, y - 20, "Date")
    c.drawString(520, y - 20, "Total")
    
    # Table rows
    y -= 30
    c.setFont("Helvetica", 9)
    for quote in queryset:
        if y < 50:
            c.showPage()
            y = PAGE_H - 50
            
        c.setFillColor(colors.black)
        c.drawString(55, y - 20, quote.quote_number or "DRAFT")
        c.drawString(150, y - 20, quote.client_name[:30])
        c.drawString(350, y - 20, quote.get_status_display())
        c.drawString(450, y - 20, quote.issue_date.strftime('%d/%m/%Y'))
        c.drawString(520, y - 20, f"KES {quote.total:,.2f}")
        y -= 25
    
    c.save()
    return buffer
