"""Tests de navigation (facilité d'utilisation, EQ-04).

Deux choses à vérifier :
  1. les livres et les auteurs sont gérables dans l'interface /admin ;
  2. le MENU affiche les bons liens selon le rôle :

    Visiteur        | Livres | Auteurs | Utilisateurs | Se connecter
    ----------------|--------|---------|--------------|-------------
    non connecté    |   non  |   non   |     non      |     oui
    ADHERENT        |   oui  |   oui   |     non      |      -
    BIBLIOTHECAIRE  |   oui  |   oui   |     non      |      -
    ADMIN           |   oui  |   oui   |     oui      |      -

Pourquoi cacher "Utilisateurs" aux non-admins ? Ce lien les mènerait
à "Accès refusé" (403) : un mauvais parcours pour l'utilisateur.
(La VRAIE protection reste le vigile côté serveur : le menu, c'est du confort.)
"""

import pytest
from django.contrib.auth import get_user_model


# ======================================================================
# 1. LE CATALOGUE DANS /admin
# ======================================================================
# parametrize : le même test lancé 2 fois, une fois par adresse.
# Format des adresses de /admin : /admin/<application>/<modèle en minuscules>/
@pytest.mark.parametrize(
    "url_admin",
    [
        "/admin/catalogue/livre/",    # la liste des livres dans /admin
        "/admin/catalogue/auteur/",   # la liste des auteurs dans /admin
    ],
)
def test_catalogue_present_dans_admin(client, db, url_admin):
    # Préparer : un super-utilisateur (seul lui a accès à /admin)
    superadmin = get_user_model().objects.create_superuser(
        username="chef", email="chef@exemple.com", password="MotDePasse!2026"
    )
    client.force_login(superadmin)

    # Agir + Vérifier : la page de /admin existe (200).
    # Tant que le modèle n'est pas enregistré dans l'admin -> 404.
    assert client.get(url_admin).status_code == 200


# ======================================================================
# 2. LE MENU SELON LE RÔLE
# ======================================================================
# Un lien HTML s'écrit :  <a href="/catalogue/livres/">Livres</a>
# On cherche donc le morceau  href="..."  dans le HTML de la page.
# (les guillemets simples ' ' entourent un texte qui contient des " ")
LIEN_LIVRES = 'href="/catalogue/livres/"'
LIEN_AUTEURS = 'href="/catalogue/auteurs/"'
LIEN_UTILISATEURS = 'href="/comptes/utilisateurs/"'
LIEN_CONNEXION = 'href="/comptes/connexion/"'


# Chaque ligne = 1 ligne de la table du haut : (rôle, voit "Utilisateurs" ?)
@pytest.mark.parametrize(
    "role, voit_utilisateurs",
    [
        ("ADMIN", True),
        ("BIBLIOTHECAIRE", False),
        ("ADHERENT", False),
    ],
)
def test_menu_selon_le_role(client, creer_utilisateur, role, voit_utilisateurs):
    # Préparer : un utilisateur de ce rôle est connecté
    # (creer_utilisateur vient de tests/conftest.py)
    client.force_login(creer_utilisateur(role))

    # Agir : il ouvre la page d'accueil (le menu est dans base.html,
    # donc présent sur TOUTES les pages : l'accueil suffit pour le tester)
    page = client.get("/").content.decode()

    # Vérifier : tous les utilisateurs connectés voient Livres et Auteurs...
    assert LIEN_LIVRES in page
    assert LIEN_AUTEURS in page
    # ...mais seul l'ADMIN voit "Utilisateurs".
    # (LIEN in page) vaut True ou False, et doit être égal au résultat attendu
    assert (LIEN_UTILISATEURS in page) is voit_utilisateurs


def test_menu_visiteur_non_connecte(client, db):
    # Personne n'est connecté (pas de force_login)
    page = client.get("/").content.decode()

    # Pas de lien vers des pages protégées (il serait renvoyé à la connexion)
    assert LIEN_LIVRES not in page
    # Seulement le lien "Se connecter"
    assert LIEN_CONNEXION in page
    # 💡 Ce test PASSE DÉJÀ (il n'y a encore aucun menu) : ce n'est pas un
    # test trop faible, c'est un test de NON-RÉGRESSION. Il empêchera plus
    # tard d'afficher par erreur les liens protégés aux visiteurs.