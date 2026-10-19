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
        "Molongo, Machakos County, Kenya",
        "P.O. Box 37, 00519 - Molongo",
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
    """The invoice layout, unchanged since invoices split off from quotes."""
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
    from .models import SiteConfiguration
    site_config = SiteConfiguration.objects.first()
    business_pin = (getattr(site_config, "kra_pin", "") or "").strip()
    if business_pin:
        contact_lines.append(f"KRA PIN: {business_pin}")

    meta_rows = [
        ("DATE", quote.issue_date.strftime("%m/%d/%Y") if quote.issue_date else "-"),
        ("INVOICE #", (quote.invoice_number or quote.quote_number) or "-"),
        ("CUSTOMER ID", quote.billing_name[:10] if quote.billing_name else "-"),
        ("INVOICED ON", quote.converted_at.strftime("%m/%d/%Y") if quote.converted_at else "-"),
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
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'images', 'logo-mark.png')
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
    c.drawRightString(x_right, y - 14, "INVOICE")

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
    c.drawString(x_left, y - 2, quote.billing_name or "")
    y -= 13
    c.setFont("Helvetica", 8.5)
    customer_lines = []
    if quote.client_company and quote.client_name:
        customer_lines.append(f"Attn: {quote.client_name}")
    customer_lines += [quote.client_location, quote.client_phone, quote.client_email]
    if quote.client_kra_pin:
        customer_lines.append(f"KRA PIN: {quote.client_kra_pin}")
    for val in customer_lines:
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

    # ---------------- How much room the table has ----------------
    # The totals and the footer need real vertical room, so measure them
    # before the table and let that decide how many empty rows to pad it with.
    items = list(quote.line_items.all())
    header_h = 14
    row_h = 20
    totals_h = (3 if quote.tax_rate <= 0 else 6) * 16
    bottom_limit = MARGIN * 0.6 + 10
    room = y - header_h - 10 - totals_h - 10 - bottom_limit
    min_rows = max(len(items), min(8, int(room // row_h)))

    # ---------------- Line items table ----------------
    col_num_x = x_left
    col_desc_x = x_left + 0.3 * inch
    col_unit_x = x_left + 4.0 * inch
    col_qty_x = x_left + 5.0 * inch
    col_tax_x = x_left + 5.5 * inch
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

    c.setFont("Helvetica", 8.5)
    for i in range(min_rows):
        shade = ROW_SHADE if i % 2 == 0 else colors.white
        c.setFillColor(shade)
        c.rect(x_left, y - row_h, x_right - x_left, row_h, fill=1, stroke=0)
        if i < len(items):
            item = items[i]
            c.setFillColor(colors.black)
            c.drawCentredString(col_num_x + 0.15 * inch, y - 12, str(i + 1))
            
            # Wrap description text if too long
            from reportlab.pdfbase.pdfmetrics import stringWidth
            desc_max_width = col_unit_x - col_desc_x - 30
            words = item.description.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip() if current_line else word
                if stringWidth(test_line, "Helvetica", 8.5) <= desc_max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Draw description lines (max 2 lines to fit in row)
            desc_y = y - 12
            for line_idx, line in enumerate(lines[:2]):
                c.drawString(col_desc_x + 4, desc_y, line)
                if line_idx == 0 and len(lines) > 1:
                    desc_y -= 10
                else:
                    desc_y -= 9
            
            c.drawRightString(col_unit_x, y - 12, f"KES {item.unit_price:,.2f}")
            c.drawCentredString(col_qty_x, y - 12, f"{item.quantity:g}")
            c.drawCentredString(col_tax_x, y - 12, "No")
            c.drawRightString(col_amt_x, y - 12, f"KES {item.line_total:,.2f}")
        else:
            c.setFillColor(colors.black)
            c.drawRightString(col_amt_x, y - 12, "-")
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
        ("AMOUNT DUE", f"KES {quote.total:,.2f}", True),
    ])
    c.setFont("Helvetica", 9)
    for label, value, is_total in totals:
        if is_total:
            c.setFillColor(TOTAL_SHADE)
            c.rect(totals_box_x, y - 13, x_right - totals_box_x, 15, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(totals_box_x + 4, y - 9, label)
            c.drawRightString(x_right - 2, y - 9, value)
        else:
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(totals_box_x + 4, y - 9, label)
            c.drawRightString(x_right - 2, y - 9, value)
        y -= 16

    y -= 10

    # An invoice is a demand for payment, so it stops after the totals and
    # leaves the rest of the page to the footer.

    # ---------------- Footer ----------------
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_W / 2, y, "If you have any questions about this invoice, please contact")
    y -= 11
    c.drawCentredString(PAGE_W / 2, y, "VoltPro Electrodata Solutions, 0715 117855 / 0724 076 047, info@voltproelectrodata.co.ke")
    y -= 16
    c.setFont("Helvetica-BoldOblique", 10)
    c.drawCentredString(PAGE_W / 2, y, "Thank You For Your Business!")

    c.showPage()
    c.save()
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
