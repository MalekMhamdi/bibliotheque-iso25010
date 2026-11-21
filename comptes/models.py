from django.db import models
"""Modèle utilisateur : l'utilisateur standard de Django, plus un rôle."""

from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"


