"""Génère un catalogue de test (EF-08, EQ-02).

Utilisation :
    python manage.py generer_catalogue --livres 10000
"""

import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogue.models import Auteur, Livre

TAILLE_PAQUET = 500  # nombre de livres insérés par requête

CATEGORIES = [
    "Roman", "Science-fiction", "Policier", "Histoire", "Biographie",
    "Poésie", "Théâtre", "Jeunesse", "Bande dessinée", "Science",
    "Philosophie", "Cuisine", "Voyage", "Informatique", "Art",
]
PRENOMS = [
    "Jean", "Marie", "Pierre", "Sophie", "Ahmed", "Fatma", "Karim", "Leila",
    "Victor", "Alice", "Omar", "Nadia", "Paul", "Claire", "Samir", "Hela",
]
NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Ben Salah", "Trabelsi", "Haddad", "Gharbi",
    "Mansouri", "Bouazizi",
]
MOTS_A = [
    "Le secret", "La maison", "Le voyage", "L'histoire", "Les enfants",
    "Le jardin", "La mémoire", "Le dernier", "La première", "Les ombres",
]
MOTS_B = [
    "du temps", "de la mer", "des étoiles", "oubliée", "perdu", "du désert",
    "de la nuit", "du village", "des anciens", "du futur",
]


class Command(BaseCommand):
    help = "Génère des livres et des auteurs de test (ISBN uniques de 13 chiffres)."

    def add_arguments(self, parser):
        parser.add_argument("--livres", type=int, default=10000)
        parser.add_argument("--auteurs", type=int, default=300)
        parser.add_argument("--graine", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **options):
        nb_livres = options["livres"]
        if nb_livres < 1:
            raise CommandError("--livres doit être supérieur à 0.")
        hasard = random.Random(options["graine"])

        auteurs_ids = self._preparer_auteurs(options["auteurs"], hasard)
        isbns = self._isbns_libres(nb_livres)

        Liaison = Livre.auteurs.through
        for debut in range(0, nb_livres, TAILLE_PAQUET):
            isbns_paquet = isbns[debut:debut + TAILLE_PAQUET]
            Livre.objects.bulk_create(
                [self._nouveau_livre(i, isbn, hasard)
                 for i, isbn in enumerate(isbns_paquet, start=debut)]
            )
            ids = Livre.objects.filter(isbn__in=isbns_paquet).values_list("pk", flat=True)
            Liaison.objects.bulk_create(
                [Liaison(livre_id=pk, auteur_id=hasard.choice(auteurs_ids)) for pk in ids]
            )

        self.stdout.write(self.style.SUCCESS(f"{nb_livres} livres générés."))

    def _preparer_auteurs(self, nb_voulus, hasard):
        """Complète jusqu'à nb_voulus auteurs, puis renvoie leurs identifiants."""
        manquants = max(0, nb_voulus - Auteur.objects.count())
        Auteur.objects.bulk_create(
            [Auteur(nom=f"{hasard.choice(PRENOMS)} {hasard.choice(NOMS)}",
                    nationalite="Tunisienne" if hasard.random() < 0.3 else "Française")
             for _ in range(manquants)]
        )
        return list(Auteur.objects.values_list("pk", flat=True))

    def _isbns_libres(self, nombre):
        """ISBN de 13 chiffres (978 + compteur sur 10 chiffres), jamais déjà utilisés."""
        existants = set(Livre.objects.values_list("isbn", flat=True))
        isbns, compteur = [], 1
        while len(isbns) < nombre:
            isbn = f"978{compteur:010d}"
            compteur += 1
            if isbn not in existants:
                isbns.append(isbn)
        return isbns

    def _nouveau_livre(self, numero, isbn, hasard):
        return Livre(
            titre=f"{hasard.choice(MOTS_A)} {hasard.choice(MOTS_B)} n°{numero}",
            isbn=isbn,
            annee=hasard.randint(1950, 2025),
            categorie=hasard.choice(CATEGORIES),
            nb_exemplaires=hasard.randint(1, 5),
        )