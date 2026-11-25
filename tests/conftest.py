"""Fixtures partagées par TOUS les tests.

pytest lit ce fichier automatiquement : une fixture définie ici
est utilisable dans n'importe quel test du dossier tests/,
simplement en écrivant son nom dans les paramètres du test.
"""

import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def creer_utilisateur(db):  #db la fixture demande l'accès à la base temporaire
    """Fabrique d'utilisateurs : renvoie une FONCTION qui crée un utilisateur.

    Utilisation dans un test :
        def test_exemple(creer_utilisateur):
            biblio = creer_utilisateur("BIBLIOTHECAIRE")
            adherent = creer_utilisateur("ADHERENT")
    """

    def _creer(role):
        nom = role.lower()                       # "ADMIN" -> "admin"
        return get_user_model().objects.create_user(
            username=nom,
            email=f"{nom}@exemple.com",          # un email différent par rôle (RM-07)
            password="MotDePasse!2026",
            role=role,
        )

    return _creer   # on renvoie la FONCTION, pas un utilisateur



#Pourquoi renvoyer une fonction ? Une fixture « normale », comme alice à l'étape 4.4, donne un objet fixe. Ici, chaque test veut un rôle différent, voire plusieurs utilisateurs. On renvoie donc une fabrique : le test l'appelle avec le rôle qu'il veut. On appelle ce modèle une factory fixture (fixture-fabrique).