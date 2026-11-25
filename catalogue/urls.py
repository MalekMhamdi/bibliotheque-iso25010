

from django.urls import path

from catalogue import views   # les vues du catalogue (pas de config !)

urlpatterns = [
    path("auteurs/", views.AuteurListe.as_view(), name="auteur_liste"),
    path("auteurs/nouveau/", views.AuteurCreation.as_view(), name="auteur_creation"),
    # <int:pk> = un NOMBRE dans l'adresse, transmis à la vue sous le nom "pk"
    path("auteurs/<int:pk>/modifier/", views.AuteurModification.as_view(), name="auteur_modification"),
    path("auteurs/<int:pk>/supprimer/", views.AuteurSuppression.as_view(), name="auteur_suppression"),
    path("livres/", views.LivreListe.as_view(), name="livre_liste"),
    path("livres/nouveau/", views.LivreCreation.as_view(), name="livre_creation"),
    path("livres/<int:pk>/modifier/", views.LivreModification.as_view(), name="livre_modification"),
    path("livres/<int:pk>/supprimer/", views.LivreSuppression.as_view(), name="livre_suppression"),
]