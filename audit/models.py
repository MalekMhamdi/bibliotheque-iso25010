from django.conf import settings
from django.db import models


class JournalAudit(models.Model):
    class Action(models.TextChoices):
        CREATION = "CREATION", "Création"
        MODIFICATION = "MODIFICATION", "Modification"
        SUPPRESSION = "SUPPRESSION", "Suppression"
        RESERVATION = "RESERVATION", "Réservation"
        REMISE = "REMISE", "Remise"
        RETOUR = "RETOUR", "Retour"
        ANNULATION = "ANNULATION", "Annulation"

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entrees_audit",
    )
    action = models.CharField(max_length=15, choices=Action.choices)
    entite = models.CharField(max_length=50)
    entite_id = models.PositiveIntegerField(null=True, blank=True)
    date_heure = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_heure", "-pk"]

    def __str__(self):
        return f"{self.date_heure:%d/%m/%Y %H:%M} {self.action} {self.entite}#{self.entite_id}"
