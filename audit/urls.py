from django.urls import path

from audit import views

urlpatterns = [
    path("", views.AuditListe.as_view(), name="audit_liste"),
]