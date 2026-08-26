import uuid
from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils import timezone


class ServiceCategory(models.TextChoices):
    POWER = "power", "Power & Backup"
    SOLAR = "solar", "Solar & Clean Energy"
    ACCESS = "access", "Access & Security"
    INFRA = "infra", "Wiring & Infrastructure"
    GATES = "gates", "Gates & Perimeter"


class Service(models.Model):
    """One module on the switchboard — a single service line."""
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=20, choices=ServiceCategory.choices)
    short_description = models.CharField(
        max_length=160, help_text="One line shown on the service card."
    )
    description = models.TextField(
        help_text="Full detail shown on the service page."
    )
    icon = models.CharField(
        max_length=40,
        default="bolt",
        help_text="Icon key used by the SVG icon set in the template.",
    )
    image = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True,
        help_text="Photo shown on the service card and detail page. Falls back to a "
                   "branded category cover graphic when left blank.",
    )
    rating_note = models.CharField(
        max_length=60,
        blank=True,
        help_text="Optional spec-style label, e.g. '3-Phase & Single-Phase'.",
    )
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:service_detail", kwargs={"slug": self.slug})

    @property
    def fallback_cover_image_url(self):
        """Bundled cover used when a hosted media file is unavailable."""
        return f"/static/core/images/covers/{self.category}.svg"

    @property
    def cover_image_url(self):
        """Use the uploaded photo where it is available, with a bundled
        category illustration as a reliable visual fallback."""
        if self.image:
            return self.image.url
        return self.fallback_cover_image_url


class Project(models.Model):
    """Completed installation shown in the works/gallery section."""
    title = models.CharField(max_length=150)
    location = models.CharField(max_length=120, blank=True)
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="projects",
    )
    summary = models.CharField(max_length=200)
    image = models.ImageField(upload_to="projects/", blank=True, null=True)
    video = models.FileField(upload_to="project_videos/", blank=True, null=True, help_text="Video file for this project.")
    completed_on = models.DateField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-completed_on"]

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    client_name = models.CharField(max_length=120)
    client_role = models.CharField(max_length=150, blank=True)
    quote = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.client_name} — {self.quote[:40]}"


class QuoteRequest(models.Model):
    """Lead captured from the 'Request a Quote' form."""
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.created_at:%d %b %Y})"


class QuoteStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class Quote(models.Model):
    """A formal, numbered quotation — the document a client can accept, download as PDF, or reject."""

    VAT_RATE_DEFAULT = Decimal("16.00")

    quote_number = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    request = models.ForeignKey(
        QuoteRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="quotes",
        help_text="Optional — the lead this quote was raised from.",
    )
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)

    client_name = models.CharField(
        max_length=120, 
        help_text="Full name of the client or organization contact person"
    )
    client_phone = models.CharField(
        max_length=30, 
        blank=True,
        help_text="Client phone number for communication"
    )
    client_email = models.EmailField(
        blank=True,
        help_text="Client email address for sending quote and updates"
    )
    client_location = models.CharField(
        max_length=150, 
        blank=True,
        help_text="Physical address or location where work will be performed"
    )

    status = models.CharField(max_length=10, choices=QuoteStatus.choices, default=QuoteStatus.DRAFT)
    issue_date = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(blank=True, null=True)

    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=VAT_RATE_DEFAULT,
        help_text="VAT percentage applied to the subtotal. Set to 0 for a tax-exempt quote.",
    )
    notes = models.TextField(
        blank=True, 
        help_text="Scope notes shown on the quote, above the line items. Describe the work scope, inclusions, and exclusions."
    )
    terms = models.TextField(
        blank=True,
        default=(
            "50% deposit on acceptance, balance on completion. Quote valid for 30 days "
            "from issue date unless stated otherwise. Materials sourced to spec unless "
            "an alternative is agreed in writing."
        ),
        help_text="Payment terms, validity period, and other conditions shown on the quote"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quote_number or 'DRAFT'} — {self.client_name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.valid_until and self.issue_date:
            self.valid_until = self.issue_date + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
        if is_new and not self.quote_number:
            year = self.issue_date.year if self.issue_date else timezone.localdate().year
            self.quote_number = f"VP-{year}-{self.pk:04d}"
            super().save(update_fields=["quote_number"])

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.line_items.all()), Decimal("0.00"))

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_rate / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def total(self):
        return self.subtotal + self.tax_amount

    def get_absolute_url(self):
        return reverse("core:quote_detail", kwargs={"public_id": self.public_id})


class InventoryItem(models.Model):
    """Inventory items that can be selected in quote line items."""
    name = models.CharField(max_length=200, help_text="Item name for dropdown")
    description = models.CharField(max_length=200, help_text="Default description")
    unit = models.CharField(max_length=20, default="unit", help_text="e.g. unit, hrs, m, lot")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    category = models.CharField(max_length=100, blank=True, help_text="Category for grouping")
    is_active = models.BooleanField(default=True, help_text="Show in dropdown")
    order = models.PositiveIntegerField(default=0, help_text="Sort order in dropdown")

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"

    def __str__(self):
        return f"{self.name} - KES {self.unit_price:,.2f}/{self.unit}"


class QuoteLineItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="line_items")
    description = models.CharField(
        max_length=200, 
        help_text="Detailed description of the item, material, or service"
    )
    unit = models.CharField(
        max_length=20, 
        default="unit", 
        help_text="Unit of measurement (e.g. unit, hrs, m, lot, kg)"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("1.00"),
        help_text="Quantity required"
    )
    unit_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00"),
        help_text="Price per unit in KES"
    )
    order = models.PositiveIntegerField(default=0, help_text="Sort order for line items")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Quote Line Item"
        verbose_name_plural = "Quote Line Items"

    def __str__(self):
        return f"{self.description} ({self.quantity} {self.unit})"

    @property
    def line_total(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @property
    def line_number(self):
        """Calculate line number based on position in quote's line items."""
        items = list(self.quote.line_items.all())
        return items.index(self) + 1 if self in items else 0


class SiteConfiguration(models.Model):
    """Singleton model for managing site-wide images and videos."""
    hero_image = models.ImageField(
        upload_to="hero/",
        blank=True,
        null=True,
        help_text="Hero section image displayed on the home page."
    )
    services_video = models.FileField(
        upload_to="videos/",
        blank=True,
        null=True,
        help_text="Video shown in the services section."
    )
    
    # Email configuration
    email_host = models.CharField(
        max_length=100,
        default='smtp.gmail.com',
        help_text="SMTP server host (e.g., smtp.gmail.com)"
    )
    email_port = models.PositiveIntegerField(
        default=587,
        help_text="SMTP server port (e.g., 587 for TLS)"
    )
    email_use_tls = models.BooleanField(
        default=True,
        help_text="Use TLS for email sending"
    )
    email_host_user = models.CharField(
        max_length=100,
        blank=True,
        help_text="SMTP username (usually email address)"
    )
    email_host_password = models.CharField(
        max_length=100,
        blank=True,
        help_text="SMTP password or app-specific password"
    )
    contact_email = models.EmailField(
        default='info@voltproelectrodata.co.ke',
        help_text="Contact email address displayed on the site"
    )
    technician_email = models.EmailField(
        default='warrenm@voltpro.co.ke',
        help_text="Technician email address for receiving quote notifications"
    )

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Configuration"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValueError("Only one SiteConfiguration instance can exist. Edit the existing one instead.")
        super().save(*args, **kwargs)
