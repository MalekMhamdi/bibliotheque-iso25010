"""Tests unitaires RM-04 : droit de réserver (couverture MC/DC)."""

from decimal import Decimal

import pytest

from prets.regles import peut_reserver


@pytest.mark.parametrize(
    "compte_actif, a_un_retard, penalite, attendu",
    [
        (True, False, Decimal("0.00"), True),  # cas 1 : tout est bon -> autorisé
        (False, False, Decimal("0.00"), False),  # cas 2 : seul A change (compte inactif)
        (True, True, Decimal("0.00"), False),  # cas 3 : seul B change (prêt en retard)
        (True, False, Decimal("0.50"), False),  # cas 4 : seul C change (pénalité due)
        (True, False, Decimal("0.01"), False),  # valeur limite : 0,01 EUR suffit à refuser
    ],
)
def test_peut_reserver_mcdc(compte_actif, a_un_retard, penalite, attendu):
    """RM-04 : réservation autorisée seulement si compte actif ET aucun retard
    ET pénalité impayée = 0. Chaque condition change seule le résultat (MC/DC)."""
    assert peut_reserver(compte_actif, a_un_retard, penalite) is attendu
