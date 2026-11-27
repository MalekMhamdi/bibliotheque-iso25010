"""Commande donnees_demo : prêts dans tous les états, sans doublons."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from prets.models import Pret

pytestmark = pytest.mark.django_db
S = Pret.Statut


def test_cree_des_prets_dans_tous_les_etats():
    call_command("donnees_demo", livres=30)

    statuts = set(Pret.objects.values_list("statut", flat=True))
    assert statuts == {S.RESERVE, S.EN_COURS, S.EN_RETARD, S.RENDU, S.ANNULE}


def test_chloe_a_la_penalite_plafonnee():
    """RM-03 : 21 jours de retard -> 10,00 €."""
    call_command("donnees_demo", livres=30)

    chloe = get_user_model().objects.get(username="chloe")
    assert chloe.penalite_impayee == Decimal("10.00")


def test_relancer_ne_cree_pas_de_doublons():
    call_command("donnees_demo", livres=30)
    nb = Pret.objects.count()

    call_command("donnees_demo", livres=30)

    assert Pret.objects.count() == nb
