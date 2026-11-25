"""Modèle utilisateur : l'utilisateur standard de Django, plus un rôle."""

from decimal import Decimal

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UtilisateurManager(UserManager):
    """Gestionnaire des utilisateurs : il fabrique les comptes.

    On hérite du gestionnaire standard de Django et on change UNE chose :
    un super-utilisateur reçoit automatiquement le rôle ADMIN.
    """

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # setdefault = "mets ADMIN, sauf si un autre rôle a été donné"
        extra_fields.setdefault("role", "ADMIN")
        # puis on laisse Django faire tout le reste (hachage, is_superuser...)
        return super().create_superuser(username, email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """Utilisateur de la bibliothèque, avec un rôle (EF-02)."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrateur"
        BIBLIOTHECAIRE = "BIBLIOTHECAIRE", "Bibliothécaire"
        ADHERENT = "ADHERENT", "Adhérent"

    # RM-07 : un email ne peut appartenir qu'à un seul utilisateur
    email = models.EmailField("adresse email", unique=True)

    role = models.CharField(
        "rôle",
        max_length=20,
        choices=Role.choices,
        default=Role.ADHERENT,
    )

    # On branche NOTRE gestionnaire à la place du gestionnaire standard
    objects = UtilisateurManager()

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    penalite_impayee = models.DecimalField(
        "pénalité impayée", max_digits=6, decimal_places=2, default=Decimal("0.00")
    )
