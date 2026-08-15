from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("work/", views.work, name="work"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("quotes/<uuid:public_id>/", views.quote_detail, name="quote_detail"),
    path("quotes/<uuid:public_id>/pdf/", views.quote_pdf, name="quote_pdf"),
    path("quotes/admin/<int:pk>/pdf/", views.quote_pdf_admin, name="quote_pdf_admin"),
]
