"""Recherche dans le catalogue : ?q= (EF-08)."""

from itertools import count

import pytest
from django.urls import reverse

from catalogue.models import Auteur, Livre

pytestmark = pytest.mark.django_db

_isbn = count(9782000000001)


def _livre(titre, categorie="Roman", auteurs=("Auteur Test",), isbn=None):
    livre = Livre.objects.create(
        titre=titre,
        isbn=isbn or str(next(_isbn)),
        categorie=categorie,
        nb_exemplaires=1,
    )
    for nom in auteurs:
        auteur, _ = Auteur.objects.get_or_create(nom=nom)
        livre.auteurs.add(auteur)
    return livre


def _chercher(client, creer_utilisateur, **params):
    if "_auth_user_id" not in client.session:
        client.force_login(creer_utilisateur("ADHERENT"))
    return client.get(reverse("livre_liste"), params).content.decode()


def test_champ_de_recherche_present(client, creer_utilisateur):
    contenu = _chercher(client, creer_utilisateur)

    assert 'name="q"' in contenu


def test_recherche_vide_affiche_tous_les_livres(client, creer_utilisateur):
    _livre("Livre Un")
    _livre("Livre Deux")

    contenu = _chercher(client, creer_utilisateur, q="")

    assert "Livre Un" in contenu and "Livre Deux" in contenu


def test_recherche_par_titre_sans_tenir_compte_de_la_casse(client, creer_utilisateur):
    _livre("Le Petit Prince")
    _livre("Dune")

    contenu = _chercher(client, creer_utilisateur, q="petit")

    assert "Le Petit Prince" in contenu
    assert "Dune" not in contenu


def test_recherche_par_nom_d_auteur(client, creer_utilisateur):
    _livre("Titre Alpha", auteurs=("Herbert",))
    _livre("Titre Beta", auteurs=("Zola",))

    contenu = _chercher(client, creer_utilisateur, q="herbert")

    assert "Titre Alpha" in contenu
    assert "Titre Beta" not in contenu


def test_recherche_par_isbn_exact(client, creer_utilisateur):
    _livre("Livre Cible", isbn="9782999999991")
    _livre("Livre Autre", isbn="9782999999992")

    contenu = _chercher(client, creer_utilisateur, q="9782999999991")

    assert "Livre Cible" in contenu
    assert "Livre Autre" not in contenu


def test_un_isbn_partiel_ne_donne_pas_de_resultat(client, creer_utilisateur):
    """ISBN : correspondance exacte, pas partielle."""
    _livre("Livre Cible", isbn="9782999999991")

    contenu = _chercher(client, creer_utilisateur, q="97829999999")

    assert "Livre Cible" not in contenu


def test_recherche_par_categorie(client, creer_utilisateur):
    _livre("Livre SF", categorie="Science-fiction")
    _livre("Livre Policier", categorie="Policier")

    contenu = _chercher(client, creer_utilisateur, q="science")

    assert "Livre SF" in contenu
    assert "Livre Policier" not in contenu


def test_aucun_resultat_affiche_un_message(client, creer_utilisateur):
    _livre("Livre Existant")

    contenu = _chercher(client, creer_utilisateur, q="introuvable")

    assert "Aucun livre" in contenu
    assert "Livre Existant" not in contenu


def test_livre_a_deux_auteurs_affiche_une_seule_fois(client, creer_utilisateur):
    """.distinct() : les 2 auteurs correspondent, mais le livre n'apparaît qu'une fois."""
    _livre("Titre Duo Unique", auteurs=("Martin Alpha", "Martin Beta"))
    _livre("Livre Hors Sujet", auteurs=("Durand",))

    contenu = _chercher(client, creer_utilisateur, q="martin")

    assert contenu.count("Titre Duo Unique") == 1
    assert "Livre Hors Sujet" not in contenu


def test_pagination_conserve_la_recherche(client, creer_utilisateur):
    """25 résultats (pagination à 20) : la page 2 garde le filtre q."""
    Livre.objects.bulk_create(
        [Livre(titre=f"Cible {i:02d}", isbn=str(next(_isbn)), nb_exemplaires=1) for i in range(25)]
        + [
            Livre(titre=f"Hors-sujet {i:02d}", isbn=str(next(_isbn)), nb_exemplaires=1)
            for i in range(5)
        ]
    )

    page1 = _chercher(client, creer_utilisateur, q="cible")
    page2 = _chercher(client, creer_utilisateur, q="cible", page=2)

    assert "q=cible" in page1  # le lien « Suivante » garde la recherche
    assert page1.count("Cible ") == 20
    assert page2.count("Cible ") == 5
    assert "Hors-sujet" not in page1 and "Hors-sujet" not in page2
