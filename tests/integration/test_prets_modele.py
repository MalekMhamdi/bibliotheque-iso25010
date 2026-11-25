"""Tests d'intégration du modèle Pret : RM-01, RM-06, suppression protégée."""
import pytest
from django.urls import reverse

from catalogue.models import Auteur, Livre
from prets.models import Pret


@pytest.fixture
def livre(db):
    """Un livre avec un auteur (préparation commune aux tests)."""
    auteur = Auteur.objects.create(nom="Victor Hugo")  # À ADAPTER : champs d'Auteur
    livre = Livre.objects.create(  # À ADAPTER : champs de Livre
        titre="Les Misérables",
        isbn="9782070409228",
        categorie="Roman",
        nb_exemplaires=2,
    )
    livre.auteurs.add(auteur)
    return livre


def test_pret_cree_en_reserve_par_defaut(creer_utilisateur, livre):
    """EF-06 : un prêt nouvellement créé a le statut RESERVE."""
    adherent = creer_utilisateur("ADHERENT")  # À ADAPTER si la signature diffère
    pret = Pret.objects.create(utilisateur=adherent, livre=livre)
    assert pret.statut == Pret.Statut.RESERVE


@pytest.mark.parametrize(
    "statut, est_actif",
    [
        ("RESERVE", True),
        ("EN_COURS", True),
        ("EN_RETARD", True),
        ("RENDU", False),
        ("ANNULE", False),
    ],
)
def test_seuls_les_statuts_actifs_comptent(creer_utilisateur, livre, statut, est_actif):
    """RM-01 / RM-06 : seuls RESERVE, EN_COURS, EN_RETARD sont des prêts actifs."""
    adherent = creer_utilisateur("ADHERENT")
    Pret.objects.create(utilisateur=adherent, livre=livre, statut=statut)
    nb_actifs = Pret.objects.filter(
        utilisateur=adherent, statut__in=Pret.STATUTS_ACTIFS
    ).count()
    assert nb_actifs == (1 if est_actif else 0)


def test_suppression_livre_avec_prets_refusee(client, creer_utilisateur, livre):
    """Cadrage : supprimer un livre qui a des prêts est refusé (pas d'erreur 500)."""
    adherent = creer_utilisateur("ADHERENT")
    bibliothecaire = creer_utilisateur("BIBLIOTHECAIRE")
    Pret.objects.create(utilisateur=adherent, livre=livre)

    client.force_login(bibliothecaire)
    url = reverse("livre_suppression", args=[livre.pk])  # À ADAPTER
    reponse = client.post(url)

    assert reponse.status_code == 200                  # page réaffichée, pas de 500
    assert Livre.objects.filter(pk=livre.pk).exists()  # le livre est toujours en base