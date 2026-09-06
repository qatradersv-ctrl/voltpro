from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("process/", views.process, name="process"),
    path("work/", views.work, name="work"),
    path("contact/", views.contact, name="contact"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("quotes/<uuid:public_id>/", views.quote_detail, name="quote_detail"),
    path("quotes/<uuid:public_id>/pdf/", views.quote_pdf, name="quote_pdf"),
    path("quotes/<uuid:public_id>/toggle-item-tax/", views.quote_toggle_item_tax, name="quote_toggle_item_tax"),
    path("quotes/admin/<int:pk>/pdf/", views.quote_pdf_admin, name="quote_pdf_admin"),
    path("admin/core/inventoryitem/<int:pk>/json/", views.inventory_item_json, name="inventory_item_json"),
]
