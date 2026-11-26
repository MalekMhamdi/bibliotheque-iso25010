"""Passe en EN_RETARD les prêts EN_COURS dont la date de retour est dépassée.

Utilisation : python manage.py marquer_retards
(à planifier une fois par jour en production)
"""
from datetime import date

from django.core.management.base import BaseCommand

from prets import services


class Command(BaseCommand):
    help = "Marque les prêts en retard."

    def handle(self, *args, **options):
        nombre = services.marquer_retards(date.today())
        self.stdout.write(self.style.SUCCESS(f"{nombre} prêt(s) marqué(s) en retard."))