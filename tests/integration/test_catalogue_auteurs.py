"""Tests du CRUD des auteurs (EF-04) avec contrôle des droits (EF-02).

CRUD = Create (créer), Read (lire), Update (modifier), Delete (supprimer).

Table de décision (tirée du tableau des droits du cadrage) :

    Action      | ADMIN | BIBLIOTHECAIRE | ADHERENT | non connecté
    ------------|-------|----------------|----------|-------------
    voir liste  |  200  |      200       |   200    |    302
    créer       |  oui  |      oui       |   403    |
    modifier    |  oui  |      oui       |   403    |
    supprimer   |  oui  |      oui       |   403    |

RÈGLE D'OR de ce fichier : pour chaque REFUS, on vérifie DEUX choses :
  1. ce que le site DIT      -> le code 403 ;
  2. ce que le site a FAIT   -> la base de données n'a PAS changé.
(comme au distributeur : on lit l'écran ET on vérifie le compte)
"""

import pytest

# Le modèle qu'on teste (la table des auteurs)
from catalogue.models import Auteur

# --- Adresses fixes (constantes) -------------------------------------
URL_LISTE = "/catalogue/auteurs/"              # liste de tous les auteurs
URL_CREATION = "/catalogue/auteurs/nouveau/"   # formulaire d'ajout


# --- Adresses qui dépendent de l'auteur -------------------------------
# auteur.pk = "primary key" = numéro unique de l'auteur en base (1, 2, 3...)
# Exemple : l'auteur n°3 -> /catalogue/auteurs/3/modifier/
def url_modification(auteur):
    return f"/catalogue/auteurs/{auteur.pk}/modifier/"


def url_suppression(auteur):
    return f"/catalogue/auteurs/{auteur.pk}/supprimer/"


# --- Préparation : un auteur qui existe déjà en base ------------------
# Fixture locale à ce fichier. "db" = accès à la base temporaire.
@pytest.fixture
def goscinny(db):
    return Auteur.objects.create(nom="René Goscinny", nationalite="française")


# ======================================================================
# R = READ (LIRE) : tout utilisateur connecté voit la liste
# ======================================================================
# parametrize : le même test est lancé 3 fois, une fois par rôle.
@pytest.mark.parametrize("role", ["ADMIN", "BIBLIOTHECAIRE", "ADHERENT"])
def test_tous_les_roles_voient_la_liste(client, creer_utilisateur, goscinny, role):
    # creer_utilisateur vient de tests/conftest.py (pas besoin d'import)
    # Préparer : un utilisateur de ce rôle est connecté
    client.force_login(creer_utilisateur(role))

    # Agir : il ouvre la liste des auteurs
    reponse = client.get(URL_LISTE)

    # Vérifier : la page s'affiche (200)...
    assert reponse.status_code == 200
    # ...et l'auteur y apparaît bien (on cherche son nom dans le HTML)
    assert "René Goscinny" in reponse.content.decode()


def test_visiteur_non_connecte_est_redirige(client, db):
    # Pas de force_login : personne n'est connecté.
    # On doit être renvoyé vers la page de connexion (302).
    assert client.get(URL_LISTE).status_code == 302


# ======================================================================
# C = CREATE (CRÉER) : gestionnaires oui, adhérent non
# ======================================================================
# Chaque ligne = 1 cas de la table : (rôle, code attendu, auteur créé ?)
@pytest.mark.parametrize(
    "role, code_attendu, auteur_cree",
    [
        ("ADMIN", 302, True),            # créé, puis redirigé vers la liste
        ("BIBLIOTHECAIRE", 302, True),   # idem
        ("ADHERENT", 403, False),        # refusé ET rien ne doit être créé
    ],
)
def test_creation_selon_le_role(client, creer_utilisateur, role, code_attendu, auteur_cree):
    # Préparer : connecté avec ce rôle
    client.force_login(creer_utilisateur(role))

    # Agir : il remplit le formulaire d'ajout et clique "Enregistrer"
    reponse = client.post(URL_CREATION, {"nom": "Albert Uderzo", "nationalite": "française"})

    # Vérifier n°1 : ce que le site DIT (le code HTTP)
    assert reponse.status_code == code_attendu

    # Vérifier n°2 : ce que le site a FAIT (l'auteur existe-t-il en base ?)
    # .filter(...).exists() -> True s'il existe, False sinon
    assert Auteur.objects.filter(nom="Albert Uderzo").exists() is auteur_cree


def test_nom_obligatoire(client, creer_utilisateur):
    # Préparer : un bibliothécaire (il a le droit de créer)
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : il envoie le formulaire avec un nom VIDE
    reponse = client.post(URL_CREATION, {"nom": "", "nationalite": ""})

    # Vérifier : formulaire invalide -> Django RÉAFFICHE la page (200)
    # avec le message d'erreur (il ne redirige, 302, que si c'est réussi)
    assert reponse.status_code == 200
    # Et rien n'a été enregistré
    assert Auteur.objects.count() == 0


# ======================================================================
# U = UPDATE (MODIFIER)
# ======================================================================
def test_modification_par_bibliothecaire(client, creer_utilisateur, goscinny):
    # Préparer : un bibliothécaire est connecté
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : il change la nationalité de Goscinny
    reponse = client.post(
        url_modification(goscinny),
        {"nom": "René Goscinny", "nationalite": "franco-argentine"},
    )

    # Vérifier n°1 : succès -> redirection (302)
    assert reponse.status_code == 302

    # Vérifier n°2 : la base a VRAIMENT changé.
    # refresh_from_db() = relire l'auteur depuis la base,
    # car l'objet "goscinny" en mémoire ne se met pas à jour tout seul.
    goscinny.refresh_from_db()
    assert goscinny.nationalite == "franco-argentine"


def test_modification_refusee_a_adherent(client, creer_utilisateur, goscinny):
    # Préparer : un ADHÉRENT (il n'a PAS le droit de modifier)
    client.force_login(creer_utilisateur("ADHERENT"))

    # Agir : il essaie quand même de renommer l'auteur en "Pirate"
    reponse = client.post(url_modification(goscinny), {"nom": "Pirate", "nationalite": ""})

    # Vérifier n°1 : ce que le site DIT -> interdit
    assert reponse.status_code == 403

    # Vérifier n°2 : ce que le site a FAIT -> le nom n'a PAS changé
    goscinny.refresh_from_db()
    assert goscinny.nom == "René Goscinny"


# ======================================================================
# D = DELETE (SUPPRIMER)
# ======================================================================
def test_suppression_par_bibliothecaire(client, creer_utilisateur, goscinny):
    # Préparer : un bibliothécaire est connecté
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : il confirme la suppression (formulaire POST)
    reponse = client.post(url_suppression(goscinny))

    # Vérifier n°1 : succès -> redirection
    assert reponse.status_code == 302
    # Vérifier n°2 : l'auteur n'existe PLUS en base
    assert not Auteur.objects.filter(pk=goscinny.pk).exists()


def test_suppression_refusee_a_adherent(client, creer_utilisateur, goscinny):
    # Préparer : un ADHÉRENT
    client.force_login(creer_utilisateur("ADHERENT"))

    # Agir : il essaie de supprimer l'auteur
    reponse = client.post(url_suppression(goscinny))

    # Vérifier n°1 : ce que le site DIT -> interdit
    assert reponse.status_code == 403
    # Vérifier n°2 : ce que le site a FAIT -> l'auteur est TOUJOURS là
    # (c'est ce assert qui attraperait un code qui supprime PUIS répond 403)
    assert Auteur.objects.filter(pk=goscinny.pk).exists()