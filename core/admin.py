import csv

from django.contrib import admin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings

from .models import (
    Service, Project, Testimonial, QuoteRequest, Quote, QuoteLineItem, QuoteStatus,
    SiteConfiguration, InventoryItem,
)

admin.site.site_header = "VoltPro Electrodata Solutions"
admin.site.site_title = "VoltPro Admin"
admin.site.index_title = "Operations"


def render_badge(text, variant):
    return format_html('<span class="vp-badge vp-badge-{}">{}</span>', variant, text)


def csv_response(filename, header, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    writer.writerows(rows)
    return response


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "category", "order", "is_featured")
    list_editable = ("order", "is_featured")
    list_filter = ("category", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "short_description")
    ordering = ("order", "title")
    list_per_page = 50
    readonly_fields = ("image_preview",)
    fields = (
        "title", "slug", "category", "icon", "image", "image_preview",
        "rating_note", "short_description", "description", "order", "is_featured",
    )

    @admin.display(description="")
    def thumb(self, obj):
        return format_html(
            '<img src="{}" style="width:44px;height:44px;object-fit:cover;'
            'border-radius:6px;">', obj.cover_image_url,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj.pk:
            return "Save the service to see the live preview."
        return format_html(
            '<img src="{}" style="width:280px;height:180px;object-fit:cover;'
            'border-radius:8px;border:1px solid #ddd;"><p style="color:#888;'
            'font-size:12px;margin-top:6px;">{}</p>',
            obj.cover_image_url,
            "Your uploaded photo." if obj.image else
            "No photo uploaded yet — showing the default category cover.",
        )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "service", "location", "completed_on", "order")
    list_editable = ("order",)
    list_filter = ("service", "completed_on")
    search_fields = ("title", "location", "summary")
    autocomplete_fields = ("service",)
    date_hierarchy = "completed_on"
    readonly_fields = ("image_preview", "video_preview")
    fields = (
        "title", "service", "location", "image", "image_preview",
        "video", "video_preview", "summary", "completed_on", "order",
    )

    @admin.display(description="")
    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:44px;height:44px;object-fit:cover;'
                'border-radius:6px;">', obj.image.url,
            )
        return format_html(
            '<span style="color:#888;font-size:12px;">No image</span>'
        )

    @admin.display(description="Image Preview")
    def image_preview(self, obj):
        if not obj.pk:
            return "Save the project to see the live preview."
        if obj.image:
            return format_html(
                '<img src="{}" style="width:280px;height:180px;object-fit:cover;'
                'border-radius:8px;border:1px solid #ddd;">',
                obj.image.url,
            )
        return format_html(
            '<span style="color:#888;font-size:13px;">No image uploaded yet.</span>'
        )

    @admin.display(description="Video Preview")
    def video_preview(self, obj):
        if not obj.pk:
            return "Save the project to see the video preview."
        if obj.video:
            return format_html(
                '<video controls style="width:280px;height:180px;border-radius:8px;border:1px solid #ddd;">'
                '<source src="{}" type="video/mp4">Your browser does not support the video tag.</video>',
                obj.video.url,
            )
        return format_html(
            '<span style="color:#888;font-size:13px;">No video uploaded yet.</span>'
        )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("client_name", "client_role", "quote_preview", "order")
    list_editable = ("order",)
    search_fields = ("client_name", "client_role", "quote")

    @admin.display(description="Quote")
    def quote_preview(self, obj):
        return obj.quote[:80] + "..." if len(obj.quote) > 80 else obj.quote


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "unit_price", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description", "category")
    ordering = ("order", "name")
    fields = ("name", "description", "unit", "unit_price", "category", "is_active", "order")


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Prevent adding multiple instances
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False

    readonly_fields = ("hero_image_preview", "services_video_preview")
    fieldsets = (
        ("Hero Section", {
            "fields": ("hero_image", "hero_image_preview")
        }),
        ("Services Section", {
            "fields": ("services_video", "services_video_preview")
        }),
        ("Email Configuration", {
            "fields": ("email_host", "email_port", "email_use_tls", "email_host_user", "email_host_password", "contact_email", "technician_email")
        }),
    )

    @admin.display(description="Hero Image Preview")
    def hero_image_preview(self, obj):
        if obj.hero_image:
            return format_html(
                '<img src="{}" style="width:400px;height:250px;object-fit:cover;'
                'border-radius:8px;border:1px solid #ddd;">',
                obj.hero_image.url,
            )
        return format_html(
            '<span style="color:#888;font-size:13px;">No hero image uploaded yet.</span>'
        )

    @admin.display(description="Services Video Preview")
    def services_video_preview(self, obj):
        if obj.services_video:
            return format_html(
                '<video controls style="width:400px;height:250px;border-radius:8px;border:1px solid #ddd;">'
                '<source src="{}" type="video/mp4">Your browser does not support the video tag.</video>',
                obj.services_video.url,
            )
        return format_html(
            '<span style="color:#888;font-size:13px;">No video uploaded yet.</span>'
        )


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "service", "created_at", "handled_badge", "quote_link")
    list_filter = ("handled", "service", "created_at")
    search_fields = ("name", "phone", "email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("service",)
    date_hierarchy = "created_at"
    actions = ["create_quote_from_request", "mark_handled", "mark_unhandled", "export_csv"]

    @admin.display(description="Handled", ordering="handled")
    def handled_badge(self, obj):
        return render_badge("Yes", "yes") if obj.handled else render_badge("No", "no")

    @admin.display(description="Quote")
    def quote_link(self, obj):
        quote = obj.quotes.first()
        if not quote:
            return "—"
        url = reverse("admin:core_quote_change", args=[quote.pk])
        return format_html('<a href="{}">{}</a>', url, quote.quote_number)

    @admin.action(description="Export selected leads as CSV")
    def export_csv(self, request, queryset):
        rows = [
            [lead.name, lead.phone, lead.email, lead.location,
             lead.service.title if lead.service else "", lead.message,
             lead.created_at.strftime("%Y-%m-%d %H:%M"), "Yes" if lead.handled else "No"]
            for lead in queryset
        ]
        return csv_response(
            "voltpro_leads.csv",
            ["Name", "Phone", "Email", "Location", "Service", "Message", "Received", "Handled"],
            rows,
        )

    @admin.action(description="Mark selected leads as handled")
    def mark_handled(self, request, queryset):
        updated = queryset.update(handled=True)
        self.message_user(request, f"{updated} lead(s) marked as handled.")

    @admin.action(description="Mark selected leads as unhandled")
    def mark_unhandled(self, request, queryset):
        updated = queryset.update(handled=False)
        self.message_user(request, f"{updated} lead(s) marked as unhandled.")

    @admin.action(description="Create a draft quote from selected request(s)")
    def create_quote_from_request(self, request, queryset):
        created_pks = []
        for lead in queryset:
            if lead.quotes.exists():
                continue
            quote = Quote.objects.create(
                request=lead,
                service=lead.service,
                client_name=lead.name,
                client_phone=lead.phone,
                client_email=lead.email,
                client_location=lead.location,
                notes=lead.message,
            )
            created_pks.append(quote.pk)

        if len(created_pks) == 1:
            self.message_user(
                request,
                format_html(
                    'Draft quote created. <a href="{}">Add line items &rarr;</a>',
                    reverse("admin:core_quote_change", args=[created_pks[0]]),
                ),
            )
        elif created_pks:
            self.message_user(request, f"{len(created_pks)} draft quote(s) created (requests that already had one were skipped).")
        else:
            self.message_user(request, "No new quotes created — selected request(s) already have one.")


class QuoteLineItemInline(admin.TabularInline):
    model = QuoteLineItem
    extra = 1
    fields = ("description", "quantity", "unit", "unit_price", "line_total_display")
    readonly_fields = ("line_total_display",)
    min_num = 1
    verbose_name = "Line Item"
    verbose_name_plural = "Line Items"
    
    class Media:
        js = ('core/js/line_numbering.js',)
    
    @admin.display(description="Line Total")
    def line_total_display(self, obj):
        if obj.pk:
            return f"KES {obj.line_total:,.2f}"
        return "—"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "quote_number", "client_name", "service", "status_badge",
        "issue_date", "total_display", "pdf_link",
    )
    list_filter = ("status", "service", "issue_date")
    search_fields = ("quote_number", "client_name", "client_phone", "client_email")
    readonly_fields = ("quote_number", "totals_display", "client_link_display")
    autocomplete_fields = ("request", "service")
    date_hierarchy = "issue_date"
    inlines = [QuoteLineItemInline]
    actions = ["export_csv", "send_quote", "generate_sales_report"]
    
    fieldsets = (
        ("Client Information", {
            "fields": ("client_name", "client_phone", "client_email", "client_location"),
            "description": "Enter the client's contact information for this quote. All fields are required unless otherwise noted.",
            "classes": ("client-section",),
        }),
        ("Service & Status", {
            "fields": ("service", "request", "status", "issue_date", "valid_until"),
            "description": "Select the service, quote status, and validity period for this quote.",
            "classes": ("collapse", "service-section",),
        }),
        ("Quote Details", {
            "fields": ("tax_rate", "notes", "terms"),
            "description": "Configure tax rate, scope notes, and payment terms. Line items can be added in the section below.",
            "classes": ("collapse", "details-section",),
        }),
        ("Totals & Sharing", {
            "fields": ("totals_display", "client_link_display"),
            "description": "View calculated totals and client sharing links.",
            "classes": ("collapse", "totals-section",),
        }),
        ("System Info", {
            "fields": ("quote_number",),
            "description": "System-generated quote number and reference information.",
            "classes": ("collapse", "system-section",),
        }),
    )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return render_badge(obj.get_status_display(), obj.status)

    @admin.display(description="Total (incl. VAT)")
    def total_display(self, obj):
        return f"KES {obj.total:,.2f}"

    @admin.display(description="Totals")
    def totals_display(self, obj):
        if not obj.pk:
            return "Save the quote and add line items to see totals."
        return format_html(
            "Subtotal: <b>KES {:,.2f}</b> &nbsp;|&nbsp; VAT ({}%): <b>KES {:,.2f}</b> "
            "&nbsp;|&nbsp; Total: <b>KES {:,.2f}</b>",
            obj.subtotal, obj.tax_rate, obj.tax_amount, obj.total,
        )

    @admin.display(description="Client link")
    def client_link_display(self, obj):
        if not obj.pk:
            return "Save the quote first."
        detail_url = reverse("core:quote_detail", args=[obj.public_id])
        pdf_url = reverse("core:quote_pdf", args=[obj.public_id])
        return format_html(
            'Page: <a href="{0}" target="_blank">{0}</a><br>PDF: <a href="{1}" target="_blank">{1}</a>',
            detail_url, pdf_url,
        )

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        url = reverse("core:quote_pdf_admin", args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Download</a>', url)

    @admin.action(description="Export selected quotes as CSV")
    def export_csv(self, request, queryset):
        rows = [
            [q.quote_number, q.client_name, q.client_phone, q.client_email,
             q.service.title if q.service else "", q.get_status_display(),
             q.issue_date, q.valid_until, q.subtotal, q.tax_amount, q.total]
            for q in queryset
        ]
        return csv_response(
            "voltpro_quotes.csv",
            ["Quote #", "Client", "Phone", "Email", "Service", "Status",
             "Issued", "Valid until", "Subtotal", "VAT", "Total"],
            rows,
        )

    @admin.action(description="Send selected quotes to clients")
    def send_quote(self, request, queryset):
        sent_count = 0
        failed_count = 0
        
        for quote in queryset:
            if quote.status != QuoteStatus.DRAFT:
                continue
            
            if not quote.client_email:
                failed_count += 1
                continue
            
            try:
                detail_url = request.build_absolute_uri(
                    reverse("core:quote_detail", args=[quote.public_id])
                )
                
                # Send to client
                subject = f"Quote {quote.quote_number} from VoltPro Electrodata Solutions"
                message = f"""
Dear {quote.client_name},

Please find your quote #{quote.quote_number} below.

Total Amount: KES {quote.total:,.2f}
Valid until: {quote.valid_until.strftime('%d %B %Y') if quote.valid_until else 'N/A'}

You can view your quote online at: {detail_url}

If you have any questions, please don't hesitate to contact us.

Best regards,
VoltPro Electrodata Solutions
"""
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [quote.client_email],
                    fail_silently=False,
                )
                
                # Send to technician with client details
                site_config = SiteConfiguration.objects.first()
                technician_email = site_config.technician_email if site_config else settings.DEFAULT_FROM_EMAIL
                
                technician_subject = f"Quote Sent - {quote.quote_number} - {quote.client_name}"
                technician_message = f"""
Quote #{quote.quote_number} has been sent to the client.

Client Details:
- Name: {quote.client_name}
- Phone: {quote.client_phone or 'Not provided'}
- Email: {quote.client_email}
- Location: {quote.client_location or 'Not specified'}
- Service: {quote.service.title if quote.service else 'Not specified'}

Quote Details:
- Total Amount: KES {quote.total:,.2f}
- Valid until: {quote.valid_until.strftime('%d %B %Y') if quote.valid_until else 'N/A'}
- Quote Link: {detail_url}

You can view and manage this quote in the admin panel.
"""
                
                send_mail(
                    technician_subject,
                    technician_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [technician_email],
                    fail_silently=True,
                )
                
                quote.status = QuoteStatus.SENT
                quote.save(update_fields=["status", "updated_at"])
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
        
        if sent_count > 0:
            self.message_user(request, f"{sent_count} quote(s) sent successfully.")
        if failed_count > 0:
            self.message_user(request, f"{failed_count} quote(s) failed to send.", level="ERROR")

    @admin.action(description="Generate sales report (PDF)")
    def generate_sales_report(self, request, queryset):
        from core.pdf import build_sales_report
        from django.http import HttpResponse
        from datetime import datetime
        
        # Generate sales report PDF
        buffer = build_sales_report(queryset)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
