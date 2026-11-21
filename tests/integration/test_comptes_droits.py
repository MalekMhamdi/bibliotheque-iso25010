"""Tests du contrôle des droits par rôle (EF-02).

Table de décision pour la page /comptes/utilisateurs/ (réservée à l'admin) :

    Visiteur             | Résultat attendu
    ---------------------|-------------------------------
    non connecté         | 302 -> page de connexion
    ADHERENT             | 403 interdit
    BIBLIOTHECAIRE       | 403 interdit
    ADMIN                | 200 autorisé
"""

import pytest
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()

URL_UTILISATEURS = "/comptes/utilisateurs/"


def creer_utilisateur(role):
    """Crée un utilisateur avec le rôle demandé (fonction d'aide)."""
    nom = role.lower()
    return Utilisateur.objects.create_user(
        username=nom,
        email=f"{nom}@exemple.com",
        password="MotDePasse!2026",
        role=role,
    )


# Ligne 1 de la table : visiteur non connecté -> on lui demande de se connecter.
@pytest.mark.django_db
def test_visiteur_non_connecte_est_redirige_vers_connexion(client):
    reponse = client.get(URL_UTILISATEURS)
    assert reponse.status_code == 302
    assert reponse.url.startswith("/comptes/connexion/")


# Lignes 2, 3 et 4 de la table : UN SEUL test, lancé 3 fois avec des données différentes.
@pytest.mark.django_db
@pytest.mark.parametrize(  #lancer LE MÊME test plusieurs fois,avec des données différentes
    "role, code_attendu",
    [
        ("ADHERENT", 403),        # interdit
        ("BIBLIOTHECAIRE", 403),  # interdit
        ("ADMIN", 200),           # autorisé
    ],
)
def test_acces_liste_utilisateurs_selon_le_role(client, role, code_attendu):
    client.force_login(creer_utilisateur(role))   # Préparer : connecté avec ce rôle
    reponse = client.get(URL_UTILISATEURS)        # Agir : il visite la page admin
    assert reponse.status_code == code_attendu    # Vérifier : le bon code