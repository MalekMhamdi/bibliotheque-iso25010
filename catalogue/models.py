"""Modèles du catalogue : auteurs et livres.

Relation Livre <-> Auteur : N-N (un livre a plusieurs auteurs,
un auteur écrit plusieurs livres).
"""

from django.core.validators import MinValueValidator
from django.db import models

from catalogue.validators import valider_isbn


class Auteur(models.Model):
    """Un auteur de livres."""

    nom = models.CharField("nom", max_length=150)
    # blank=True : champ facultatif dans les formulaires
    nationalite = models.CharField("nationalité", max_length=100, blank=True)

    class Meta:
        ordering = ["nom"]  # les auteurs sont toujours triés par nom

    def __str__(self) -> str:
        return self.nom


class Livre(models.Model):
    """Un livre du catalogue (une édition, identifiée par son ISBN)."""

    # db_index=True : un INDEX en base pour accélérer la recherche par titre
    # (EF-08 : recherche sur 10 000 livres en moins de 500 ms, EQ-02)
    titre = models.CharField("titre", max_length=255, db_index=True)

    # RM-05 : unique=True  -> la BASE refuse les doublons (IntegrityError)
    #         validators   -> notre validateur de format (13 chiffres 0-9)
    isbn = models.CharField("ISBN", max_length=13, unique=True, validators=[valider_isbn])

    # null=True + blank=True : l'année peut être inconnue
    annee = models.PositiveSmallIntegerField("année de publication", null=True, blank=True)

    categorie = models.CharField("catégorie", max_length=100, blank=True, db_index=True)

    # Au moins 1 exemplaire (valeur limite : 0 est refusé)
    nb_exemplaires = models.PositiveIntegerField(
        "nombre d'exemplaires", default=1, validators=[MinValueValidator(1)]
    )

    # Relation N-N : Django crée une table de liaison livre <-> auteur.
    # related_name="livres" : depuis un auteur, on écrit auteur.livres
    auteurs = models.ManyToManyField(Auteur, related_name="livres", verbose_name="auteurs")

    class Meta:
        ordering = ["titre"]  # les livres sont toujours triés par titre

    def __str__(self) -> str:
        return f"{self.titre} ({self.isbn})"


# Create your models here.
