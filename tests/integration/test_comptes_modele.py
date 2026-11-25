"""Tests du modèle Utilisateur (EF-02, RM-07)."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

# get_user_model() renvoie le modèle utilisateur ACTIF du projet.
# On ne l'importe pas directement : c'est la bonne pratique Django.
Utilisateur = get_user_model()


@pytest.mark.django_db
def test_role_par_defaut_est_adherent():
    """Un nouvel utilisateur est un adhérent si on ne précise rien."""
    user = Utilisateur.objects.create_user(
        username="alice", email="alice@exemple.com", password="MotDePasse!2026"
    )
    assert user.role == "ADHERENT"


@pytest.mark.django_db  # donne au test une base de données temporaire
def test_les_trois_roles_existent():
    """EF-02 : les 3 rôles du cadrage sont disponibles."""
    roles = [choix[0] for choix in Utilisateur.Role.choices]
    assert roles == ["ADMIN", "BIBLIOTHECAIRE", "ADHERENT"]


@pytest.mark.django_db
def test_email_unique_rm07():
    """RM-07 : un email ne peut appartenir qu'à un seul utilisateur."""
    Utilisateur.objects.create_user(
        username="alice", email="meme@exemple.com", password="MotDePasse!2026"
    )
    with pytest.raises(IntegrityError):
        Utilisateur.objects.create_user(
            username="bob", email="meme@exemple.com", password="MotDePasse!2026"
        )
