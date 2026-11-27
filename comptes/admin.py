"""Interface d'administration (/admin) pour les utilisateurs."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from audit.admin_mixins import JournalAdminMixin
from comptes.models import Utilisateur


# @admin.register = "affiche ce modèle dans /admin, avec cette configuration"
@admin.register(Utilisateur)
class UtilisateurAdmin(JournalAdminMixin, UserAdmin):
    # On réutilise l'écran standard des utilisateurs de Django (UserAdmin),
    # qui gère déjà le mot de passe haché, et on y ajoute le RÔLE
    # et la pénalité impayée (l'admin peut la solder : RM-04).

    # Colonnes affichées dans la liste
    list_display = ("username", "email", "role", "is_active", "penalite_impayee")

    # Filtres à droite de la liste (ex. : voir seulement les bibliothécaires)
    list_filter = ("role", "is_active")

    # Écran de MODIFICATION : on ajoute une section "Rôle"
    fieldsets = UserAdmin.fieldsets + (
        ("Rôle dans la bibliothèque", {"fields": ("role", "penalite_impayee")}),
    )

    # Écran de CRÉATION : on demande aussi l'email et le rôle
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Rôle dans la bibliothèque", {"fields": ("email", "role")}),
    )
