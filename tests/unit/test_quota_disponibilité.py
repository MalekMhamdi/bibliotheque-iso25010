"""Tests unitaires RM-01 (quota de 3 prêts actifs) et RM-06 (disponibilité)."""
import pytest

from prets.regles import nb_disponibles, quota_atteint


@pytest.mark.parametrize(
    "nb_prets_actifs, attendu",
    [
        (0, False),   # aucun prêt
        (2, False),   # limite - 1 : encore autorisé
        (3, True),    # limite : quota atteint, refusé
        (4, True),    # limite + 1
    ],
)
def test_quota_atteint(nb_prets_actifs, attendu):
    """RM-01 : maximum 3 prêts actifs par adhérent."""
    assert quota_atteint(nb_prets_actifs) is attendu


@pytest.mark.parametrize(
    "nb_exemplaires, nb_prets_actifs_du_livre, attendu",
    [
        (2, 1, 1),   # un exemplaire reste
        (1, 1, 0),   # plus aucun disponible
        (3, 0, 3),   # aucun prêt actif
    ],
)
def test_nb_disponibles(nb_exemplaires, nb_prets_actifs_du_livre, attendu):
    """RM-06 : disponibles = exemplaires - prêts actifs du livre."""
    assert nb_disponibles(nb_exemplaires, nb_prets_actifs_du_livre) == attendu