"""Tests de sécurité des comptes (EQ-06)."""

import pytest
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()

MOT_DE_PASSE = "MotDePasse!2026"


@pytest.mark.django_db
def test_mot_de_passe_jamais_stocke_en_clair():
    """EQ-06 : le mot de passe enregistré n'est pas lisible."""
    user = Utilisateur.objects.create_user(
        username="alice", email="alice@exemple.com", password=MOT_DE_PASSE
    )
    assert MOT_DE_PASSE not in user.password


@pytest.mark.django_db
def test_mot_de_passe_hache_avec_bcrypt():
    """EQ-06 : l'algorithme de hachage est bcrypt."""
    user = Utilisateur.objects.create_user(
        username="alice", email="alice@exemple.com", password=MOT_DE_PASSE
    )
    assert user.password.startswith("bcrypt_sha256$")


@pytest.mark.django_db
def test_verification_du_mot_de_passe():
    """Le bon mot de passe est accepté, un mauvais est refusé."""
    user = Utilisateur.objects.create_user(
        username="alice", email="alice@exemple.com", password=MOT_DE_PASSE
    )
    assert user.check_password(MOT_DE_PASSE) is True
    assert user.check_password("mauvais") is False