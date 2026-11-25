from datetime import date

from django.conf import settings
from django.db import models


class Pret(models.Model):
    class Statut(models.TextChoices):
        RESERVE = "RESERVE", "Réservé"
        EN_COURS = "EN_COURS", "En cours"
        EN_RETARD = "EN_RETARD", "En retard"
        RENDU = "RENDU", "Rendu"
        ANNULE = "ANNULE", "Annulé"

    STATUTS_ACTIFS = (Statut.RESERVE, Statut.EN_COURS, Statut.EN_RETARD)

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prets"
    )
    livre = models.ForeignKey("catalogue.Livre", on_delete=models.PROTECT, related_name="prets")
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.RESERVE)
    date_reservation = models.DateField(default=date.today)
    date_emprunt = models.DateField(null=True, blank=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    date_retour_effective = models.DateField(null=True, blank=True)
    penalite = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.livre} - {self.utilisateur} ({self.statut})"


# Create your models here.
