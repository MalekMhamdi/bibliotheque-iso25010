"""Tests de connexion et déconnexion (EF-01).

On vérifie 4 comportements :
  1. la page de connexion s'affiche ;
  2. bon mot de passe   -> connecté + redirigé vers l'accueil ;
  3. mauvais mot de passe -> PAS connecté, on reste sur la page ;
  4. déconnexion        -> plus connecté.
"""

import pytest
from django.contrib.auth import get_user_model

# Le modèle utilisateur ACTIF du projet (notre Utilisateur avec rôle).
Utilisateur = get_user_model()

# --- Constantes : définies UNE fois, réutilisées dans tous les tests ---
MOT_DE_PASSE = "MotDePasse!2026"
URL_CONNEXION = "/comptes/connexion/"
URL_DECONNEXION = "/comptes/deconnexion/"


# ======================================================================
# PRÉPARATION (fixture)
# ======================================================================
# @pytest.fixture = ce n'est PAS un test, c'est une PRÉPARATION.
# Un test qui écrit "alice" dans ses paramètres reçoit automatiquement
# cet utilisateur, créé juste avant lui dans une base temporaire.
# "db" = autorise l'accès à la base de données temporaire.
@pytest.fixture
def alice(db):
    """Un adhérent qui existe en base, prêt à se connecter."""
    return Utilisateur.objects.create_user(
        username="alice", email="alice@exemple.com", password=MOT_DE_PASSE
    )


# ======================================================================
# FONCTION D'AIDE
# ======================================================================
def est_connecte(client):
    """Répond à la question : quelqu'un est-il connecté ?

    Quand un utilisateur se connecte, Django écrit son identifiant
    dans la session sous la clé "_auth_user_id".
    """
    return "_auth_user_id" in client.session


# ======================================================================
# LES 4 TESTS
# ======================================================================


# Test 1 : la page de connexion s'ouvre.
# Pas besoin d'alice ici, mais la page utilise la base -> django_db.
@pytest.mark.django_db
def test_page_connexion_s_affiche(client):
    # client = navigateur simulé fourni par pytest-django
    reponse = client.get(URL_CONNEXION)  # Agir : j'ouvre la page
    assert reponse.status_code == 200  # Vérifier : 200 = OK, elle s'affiche


# Test 2 : bon mot de passe -> connecté et redirigé vers l'accueil.
def test_connexion_reussie_avec_bon_mot_de_passe(client, alice):
    # client.post = je remplis le formulaire et je clique "Se connecter"
    reponse = client.post(URL_CONNEXION, {"username": "alice", "password": MOT_DE_PASSE})
    assert reponse.status_code == 302  # 302 = redirection...
    assert reponse.url == "/"  # ...vers l'accueil
    assert est_connecte(client)  # et alice est bien connectée


# Test 3 : mauvais mot de passe -> refusé (cas d'échec, très important
# pour la sécurité : un site qui accepterait n'importe quoi = faille).
def test_connexion_refusee_avec_mauvais_mot_de_passe(client, alice):
    reponse = client.post(URL_CONNEXION, {"username": "alice", "password": "mauvais"})
    assert reponse.status_code == 200  # on RESTE sur la page de connexion
    assert not est_connecte(client)  # et on n'est PAS connecté


# Test 4 : déconnexion -> plus connecté.
def test_deconnexion(client, alice):
    client.force_login(alice)  # Préparer : alice déjà connectée
    # (sans formulaire : on ne teste
    #  QUE la déconnexion ici)
    reponse = client.post(URL_DECONNEXION)  # Agir : "Se déconnecter"
    assert reponse.status_code == 302  # redirection après déconnexion
    assert not est_connecte(client)  # Vérifier : plus connectée
