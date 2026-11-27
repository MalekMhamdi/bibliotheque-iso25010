"""Données de démonstration : comptes, livres et prêts dans tous les états.

    python manage.py donnees_demo

Passe par les SERVICES (reserver, remettre, rendre...) : les règles métier
s'appliquent et le journal d'audit se remplit comme en utilisation réelle.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogue.models import Livre
from prets import services
from prets.models import Pret

MOT_DE_PASSE = "Demo!2026"

COMPTES = [
    ("biblio", "BIBLIOTHECAIRE"),
    ("alice", "ADHERENT"),
    ("bob", "ADHERENT"),
    ("chloe", "ADHERENT"),
    ("david", "ADHERENT"),
]


class Command(BaseCommand):
    help = "Crée des comptes, des livres et des prêts de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--livres", type=int, default=200)

    @transaction.atomic
    def handle(self, *args, **options):
        Utilisateur = get_user_model()

        if Utilisateur.objects.filter(username="alice", prets__isnull=False).exists():
            self.stdout.write("Les données de démonstration existent déjà : rien à faire.")
            return

        # 1. Comptes
        u = {}
        for nom, role in COMPTES:
            compte, _ = Utilisateur.objects.get_or_create(
                username=nom, defaults={"email": f"{nom}@demo.fr", "role": role}
            )
            compte.set_password(MOT_DE_PASSE)
            compte.save()
            u[nom] = compte

        # 2. Livres (seulement si le catalogue est presque vide)
        if Livre.objects.count() < 20:
            call_command("generer_catalogue", livres=options["livres"], stdout=self.stdout)
        livres = list(Livre.objects.order_by("pk")[:8])

        aujourd_hui = date.today()
        biblio = u["biblio"]

        def il_y_a(jours):
            return aujourd_hui - timedelta(days=jours)

        # 3. Prêts dans tous les états du workflow
        # alice : 2 réservations en attente
        services.reserver(u["alice"], livres[0])
        services.reserver(u["alice"], livres[1])

        # bob : 1 prêt en cours, 1 prêt en retard
        services.remettre(services.reserver(u["bob"], livres[2]), il_y_a(3), biblio)
        services.remettre(services.reserver(u["bob"], livres[3]), il_y_a(20), biblio)
        services.marquer_retards(aujourd_hui)

        # chloe : 1 prêt rendu avec 21 jours de retard -> pénalité 10 € (RM-03)
        # (elle ne peut donc plus réserver : RM-04)
        pret = services.remettre(services.reserver(u["chloe"], livres[4]), il_y_a(40), biblio)
        services.rendre(pret, il_y_a(5), biblio)

        # david : 1 prêt rendu à temps, 1 réservation annulée
        pret = services.remettre(services.reserver(u["david"], livres[5]), il_y_a(10), biblio)
        services.rendre(pret, il_y_a(2), biblio)
        services.annuler(services.reserver(u["david"], livres[6]), u["david"])

        self.stdout.write(
            self.style.SUCCESS(
                f"{Pret.objects.count()} prêts créés. Comptes : "
                + ", ".join(nom for nom, _ in COMPTES)
                + f" (mot de passe : {MOT_DE_PASSE})"
            )
        )
