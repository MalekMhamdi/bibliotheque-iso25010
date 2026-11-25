"""Fixtures partagÃ©es par TOUS les tests.

pytest lit ce fichier automatiquement : une fixture dÃ©finie ici
est utilisable dans n'importe quel test du dossier tests/,
simplement en Ã©crivant son nom dans les paramÃ¨tres du test.
"""

import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def creer_utilisateur(db):  # db la fixture demande l'accÃ¨s Ã  la base temporaire
    """Fabrique d'utilisateurs : renvoie une FONCTION qui crÃ©e un utilisateur.

    Utilisation dans un test :
        def test_exemple(creer_utilisateur):
            biblio = creer_utilisateur("BIBLIOTHECAIRE")
            adherent = creer_utilisateur("ADHERENT")
    """

    def _creer(role):
        nom = role.lower()  # "ADMIN" -> "admin"
        return get_user_model().objects.create_user(
            username=nom,
            email=f"{nom}@exemple.com",  # un email diffÃ©rent par rÃ´le (RM-07)
            password="MotDePasse!2026",
            role=role,
        )

    return _creer  # on renvoie la FONCTION, pas un utilisateur


# Pourquoi renvoyer une fonction ? Une fixture normale donne un objet fixe.
# Ici, chaque test veut un rôle différent, voire plusieurs utilisateurs.
# On renvoie donc une fabrique appelée avec le rôle voulu (factory fixture).
