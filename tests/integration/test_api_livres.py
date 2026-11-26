"""Tests de l'API livres : EQ-03 (interopérabilité), EF-03."""

import pytest

from catalogue.models import Auteur, Livre

pytestmark = pytest.mark.django_db

URL_LISTE = "/api/livres/"


@pytest.fixture
def livre():
    auteur = Auteur.objects.create(nom="Goscinny")
    livre = Livre.objects.create(titre="Astérix le Gaulois", isbn="9782070612758", categorie="BD")
    livre.auteurs.add(auteur)
    return livre


def test_non_connecte_refuse(client, livre):
    """Non connecté -> 403 et aucune donnée dans la réponse."""
    reponse = client.get(URL_LISTE)
    assert reponse.status_code == 403
    assert "Astérix" not in reponse.content.decode()


@pytest.mark.parametrize("role", ["ADMIN", "BIBLIOTHECAIRE", "ADHERENT"])
def test_liste_accessible_a_tous_les_roles(client, creer_utilisateur, livre, role):
    client.force_login(creer_utilisateur(role))
    reponse = client.get(URL_LISTE)
    assert reponse.status_code == 200
    assert reponse["Content-Type"].startswith("application/json")


def test_format_de_la_liste(client, creer_utilisateur, livre):
    client.force_login(creer_utilisateur("ADHERENT"))
    donnees = client.get(URL_LISTE).json()
    assert {"count", "next", "previous", "results"} <= donnees.keys()
    assert donnees["count"] == 1
    item = donnees["results"][0]
    assert item["titre"] == "Astérix le Gaulois"
    assert item["isbn"] == "9782070612758"
    assert isinstance(item["id"], int)
    assert isinstance(item["auteurs"], list)


def test_detail_existant(client, creer_utilisateur, livre):
    client.force_login(creer_utilisateur("ADHERENT"))
    reponse = client.get(f"{URL_LISTE}{livre.pk}/")
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == "Astérix le Gaulois"


def test_detail_introuvable(client, creer_utilisateur):
    client.force_login(creer_utilisateur("ADHERENT"))
    assert client.get(f"{URL_LISTE}99999/").status_code == 404


def test_pagination_20_par_page(client, creer_utilisateur):
    Livre.objects.bulk_create(
        [Livre(titre=f"Livre {i}", isbn=f"978000000{i:04d}") for i in range(25)]
    )
    client.force_login(creer_utilisateur("ADHERENT"))
    page1 = client.get(URL_LISTE).json()
    assert page1["count"] == 25
    assert len(page1["results"]) == 20
    assert len(client.get(URL_LISTE + "?page=2").json()["results"]) == 5