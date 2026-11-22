"""Tests du compte administrateur et de la gestion des rôles (EF-05).

Problème constaté : un compte créé avec "createsuperuser" avait le rôle
ADHERENT (rôle par défaut) -> l'administrateur se faisait refuser (403)
l'accès à ses propres pages, et aucun écran ne permettait de changer un rôle.

Règles vérifiées :
  1. un super-utilisateur a le rôle ADMIN ;
  2. l'admin peut gérer les utilisateurs et leur rôle dans /admin.
"""

import pytest
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()

# Page de l'interface /admin de Django qui liste les utilisateurs
URL_ADMIN_UTILISATEURS = "/admin/comptes/utilisateur/"


# ----------------------------------------------------------------------
# Préparation : un super-utilisateur (comme avec "createsuperuser")
# ----------------------------------------------------------------------
@pytest.fixture
def superadmin(db):
    # create_superuser = la méthode qu'appelle la commande "createsuperuser"
    return Utilisateur.objects.create_superuser(
        username="chef", email="chef@exemple.com", password="MotDePasse!2026"
    )


# Règle 1 : un super-utilisateur doit avoir le rôle ADMIN.
def test_superutilisateur_a_le_role_admin(superadmin):
    assert superadmin.role == "ADMIN"


# Règle 2 : l'admin peut gérer les utilisateurs dans /admin,
# et le rôle y apparaît (pour pouvoir le modifier).
def test_admin_peut_gerer_les_utilisateurs_et_leur_role(client, superadmin):
    client.force_login(superadmin)                      # Préparer : l'admin est connecté
    reponse = client.get(URL_ADMIN_UTILISATEURS)        # Agir : il ouvre la page
    assert reponse.status_code == 200                   # Vérifier : elle s'affiche...
    assert "rôle" in reponse.content.decode().lower()   # ...avec la colonne "rôle"
    # content.decode() = le HTML de la page en texte
    # .lower()         = tout en minuscules ("Rôle" ou "rôle" sont trouvés)