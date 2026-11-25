from django.urls import path

from prets import views

urlpatterns = [
    path("", views.pret_liste, name="pret_liste"),
    path("mes-prets/", views.mes_prets, name="mes_prets"),
    path("reserver/<int:livre_pk>/", views.pret_reserver, name="pret_reserver"),
    path("<int:pk>/remettre/", views.pret_remettre, name="pret_remettre"),
    path("<int:pk>/rendre/", views.pret_rendre, name="pret_rendre"),
    path("<int:pk>/annuler/", views.pret_annuler, name="pret_annuler"),
]
