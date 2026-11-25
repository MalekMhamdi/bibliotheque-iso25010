"""Tests unitaires des règles de prêt : RM-02 (durée) et RM-03 (pénalité)."""
from datetime import date
from decimal import Decimal

import pytest

from prets.regles import calculer_penalite, date_retour_prevue, jours_de_retard


@pytest.mark.parametrize(
    "emprunt, attendu",
    [
        (date(2026, 3, 1), date(2026, 3, 15)),     # cas simple
        (date(2027, 2, 25), date(2027, 3, 11)),    # février, 28 jours
        (date(2028, 2, 25), date(2028, 3, 10)),    # année bissextile
        (date(2026, 12, 25), date(2027, 1, 8)),    # changement d'année
    ],
)
def test_date_retour_prevue(emprunt, attendu):
    """RM-02 : retour prévu = date d'emprunt + 14 jours."""
    assert date_retour_prevue(emprunt) == attendu


@pytest.mark.parametrize(
    "rendu, attendu",
    [
        (date(2026, 3, 14), 0),   # en avance : jamais négatif
        (date(2026, 3, 15), 0),   # valeur limite
        (date(2026, 3, 16), 1),   # limite + 1
        (date(2026, 4, 4), 20),
    ],
)
def test_jours_de_retard(rendu, attendu):
    """RM-03 : nombre de jours de retard (prévu = 15/03/2026)."""
    assert jours_de_retard(date(2026, 3, 15), rendu) == attendu


@pytest.mark.parametrize(
    "jours, attendu",
    [
        (0, Decimal("0.00")),
        (1, Decimal("0.50")),
        (19, Decimal("9.50")),     # plafond - 1
        (20, Decimal("10.00")),    # le plafond
        (21, Decimal("10.00")),    # plafond + 1 (bug si 10,50)
        (100, Decimal("10.00")),   # grande valeur
    ],
)
def test_calculer_penalite(jours, attendu):
    """RM-03 : 0,50 EUR par jour, plafonnée à 10 EUR."""
    assert calculer_penalite(jours) == attendu


def test_penalite_est_un_decimal():
    """RM-03 : les montants sont des Decimal, jamais des float."""
    assert isinstance(calculer_penalite(3), Decimal)