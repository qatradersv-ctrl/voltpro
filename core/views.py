from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings

from .models import Service, Project, Testimonial, QuoteRequest, Quote, QuoteStatus, SiteConfiguration, InventoryItem
from .pdf import build_quote_pdf


def home(request):
    services = Service.objects.filter(is_featured=True)
    projects = Project.objects.all()[:6]
    testimonials = Testimonial.objects.all()
    
    # Handle database schema issues gracefully
    try:
        site_config = SiteConfiguration.objects.first()
    except Exception:
        site_config = None

    if request.method == "POST":
        return _handle_quote_post(request, services)

    context = {
        "services": services,
        "projects": projects,
        "testimonials": testimonials,
        "site_config": site_config,
    }
    return render(request, "core/home.html", context)


def _handle_quote_post(request, services):
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()

    if not name or not phone:
        messages.error(request, "Name and phone number are required.")
    else:
        service_id = request.POST.get("service") or None
        quote_request = QuoteRequest.objects.create(
            name=name,
            phone=phone,
            email=request.POST.get("email", "").strip(),
            location=request.POST.get("location", "").strip(),
            service_id=service_id,
            message=request.POST.get("message", "").strip(),
        )
        
        # Send confirmation email if email provided
        if quote_request.email:
            try:
                subject = "Quote Request Received - VoltPro Electrodata Solutions"
                message = f"""
Dear {name},

Thank you for your quote request. We have received your inquiry and our team will contact you within one business day.

Your request details:
- Phone: {phone}
- Location: {quote_request.location or 'Not specified'}
- Service: {quote_request.service.title if quote_request.service else 'Not specified'}
- Message: {quote_request.message or 'No message provided'}

If you have any questions, please contact us at 0715 117855 or 0724076047.

Best regards,
VoltPro Electrodata Solutions
"""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [quote_request.email],
                    fail_silently=True,
                )
            except Exception:
                # Email sending failed but don't block the request
                pass
        
        # Send technician notification email with client details
        try:
            site_config = SiteConfiguration.objects.first()
            technician_email = site_config.technician_email if site_config else settings.DEFAULT_FROM_EMAIL
            
            technician_subject = f"New Quote Request - {name}"
            technician_message = f"""
New quote request received from the website:

Client Details:
- Name: {name}
- Phone: {phone}
- Email: {quote_request.email or 'Not provided'}
- Location: {quote_request.location or 'Not specified'}
- Service: {quote_request.service.title if quote_request.service else 'Not specified'}
- Message: {quote_request.message or 'No message provided'}

Please follow up with the client within one business day.
"""
            # Send to technician email and dennisc@voltproelectrodata.co.ke
            recipients = [technician_email, 'dennisc@voltproelectrodata.co.ke']
            # Remove duplicates if technician_email is the same
            recipients = list(set(recipients))
            
            send_mail(
                technician_subject,
                technician_message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=True,
            )
        except Exception:
            # Email sending failed but don't block the request
            pass
        
        messages.success(
            request,
            "Request received. Our team will call you back within one business day.",
        )
    return redirect("core:home")


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    related = Service.objects.exclude(pk=service.pk).filter(
        category=service.category
    )[:3]
    context = {"service": service, "related": related}
    return render(request, "core/service_detail.html", context)


def work(request):
    projects = Project.objects.all()
    context = {"projects": projects}
    return render(request, "core/work.html", context)


def services(request):
    services = Service.objects.all()
    context = {"services": services}
    return render(request, "core/services.html", context)


def process(request):
    return render(request, "core/process.html")


def contact(request):
    return render(request, "core/contact.html")


def quote_detail(request, public_id):
    """Client-facing quote page — no login required, reachable only with the UUID link."""
    quote = get_object_or_404(Quote, public_id=public_id)

    if request.method == "POST":
        decision = request.POST.get("decision")
        if decision == "accept" and quote.status == QuoteStatus.SENT:
            quote.status = QuoteStatus.ACCEPTED
            quote.save(update_fields=["status", "updated_at"])
            messages.success(request, "Quote accepted. We'll be in touch to schedule the work.")
        elif decision == "reject" and quote.status == QuoteStatus.SENT:
            quote.status = QuoteStatus.REJECTED
            quote.save(update_fields=["status", "updated_at"])
            messages.error(request, "Quote marked as declined.")
        return redirect("core:quote_detail", public_id=quote.public_id)

    return render(request, "core/quote_detail.html", {"quote": quote})


def quote_pdf(request, public_id):
    """Public PDF download for a quote — same access rule as the detail page."""
    quote = get_object_or_404(Quote, public_id=public_id)
    buf = build_quote_pdf(quote)
    response = HttpResponse(buf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{quote.quote_number}.pdf"'
    return response


@staff_member_required
def quote_pdf_admin(request, pk):
    """Staff-only PDF fetch by primary key, linked from the Django admin change form."""
    quote = get_object_or_404(Quote, pk=pk)
    buf = build_quote_pdf(quote)
    response = HttpResponse(buf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{quote.quote_number}.pdf"'
    return response


@staff_member_required
def inventory_item_json(request, pk):
    """Return inventory item data as JSON for admin autofill."""
    item = get_object_or_404(InventoryItem, pk=pk)
    data = {
        'name': item.name,
        'description': item.description,
        'unit': item.unit,
        'unit_price': str(item.unit_price),
        'category': item.category,
    }
    return JsonResponse(data)
