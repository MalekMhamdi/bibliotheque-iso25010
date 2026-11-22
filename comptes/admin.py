"""Interface d'administration (/admin) pour les utilisateurs."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from comptes.models import Utilisateur


# @admin.register = "affiche ce modèle dans /admin, avec cette configuration"
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    # On réutilise l'écran standard des utilisateurs de Django (UserAdmin),
    # qui gère déjà le mot de passe haché, et on y ajoute le RÔLE.

    # Colonnes affichées dans la liste
    list_display = ("username", "email", "role", "is_active")

    # Filtres à droite de la liste (ex. : voir seulement les bibliothécaires)
    list_filter = ("role", "is_active")

    # Écran de MODIFICATION : on ajoute une section "Rôle"
    fieldsets = UserAdmin.fieldsets + (
        ("Rôle dans la bibliothèque", {"fields": ("role",)}),
    )

    # Écran de CRÉATION : on demande aussi l'email et le rôle
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Rôle dans la bibliothèque", {"fields": ("email", "role")}),
    )