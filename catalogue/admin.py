"""Interface d'administration (/admin) pour le catalogue."""

from django.contrib import admin

from catalogue.models import Auteur, Livre


# @admin.register = "affiche ce modèle dans /admin, avec ces réglages"
@admin.register(Auteur)
class AuteurAdmin(admin.ModelAdmin):
    list_display = ("nom", "nationalite")  # colonnes de la liste
    search_fields = ("nom",)  # barre de recherche par nom


@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display = ("titre", "isbn", "categorie", "nb_exemplaires")
    list_filter = ("categorie",)  # filtre par catégorie (à droite)
    search_fields = ("titre", "isbn")  # recherche par titre ou ISBN
    # Choix des auteurs avec deux listes côte à côte
    # (plus pratique qu'une liste à Ctrl+clic quand il y a beaucoup d'auteurs)
    filter_horizontal = ("auteurs",)
