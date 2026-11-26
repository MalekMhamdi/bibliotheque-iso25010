from django.urls import path

from api import views

urlpatterns = [
    path("livres/", views.LivreListe.as_view(), name="api_livre_liste"),
    path("livres/<int:pk>/", views.LivreDetail.as_view(), name="api_livre_detail"),
]
