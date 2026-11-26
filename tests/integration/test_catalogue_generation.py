"""Génération de données de test : commande generer_catalogue (EF-08, EQ-02)."""

import pytest
from django.core.management import call_command

from catalogue.models import Auteur, Livre
from catalogue.validators import valider_isbn

pytestmark = pytest.mark.django_db


def test_generer_50_livres():
    """La commande crée exactement le nombre de livres demandé."""
    call_command("generer_catalogue", "--livres", "50")

    assert Livre.objects.count() == 50
    assert Auteur.objects.count() > 0


def test_tous_les_isbn_generes_sont_valides_et_uniques():
    """RM-05 : 13 chiffres, tous différents."""
    call_command("generer_catalogue", "--livres", "50")

    isbns = list(Livre.objects.values_list("isbn", flat=True))
    for isbn in isbns:
        valider_isbn(isbn)  # lève ValidationError si invalide
    assert len(set(isbns)) == 50


def test_chaque_livre_genere_a_au_moins_un_auteur():
    call_command("generer_catalogue", "--livres", "30")

    assert all(livre.auteurs.exists() for livre in Livre.objects.all())


def test_relancer_la_commande_ne_provoque_pas_de_doublon_d_isbn():
    """Utile avec Docker : la base persiste entre deux lancements."""
    call_command("generer_catalogue", "--livres", "20")
    call_command("generer_catalogue", "--livres", "20")

    assert Livre.objects.count() == 40