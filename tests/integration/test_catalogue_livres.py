"""Tests du CRUD des livres (EF-03) avec contrôle des droits (EF-02).

CRUD = Create (créer), Read (lire), Update (modifier), Delete (supprimer).

Droits (les mêmes que pour les auteurs) :
    voir la liste             : tous les rôles connectés
    créer / modifier / suppr. : ADMIN et BIBLIOTHECAIRE (ADHERENT -> 403)

En plus, ce qui est PROPRE aux livres :
  - on choisit les AUTEURS dans le formulaire (relation N-N) ;
  - RM-05 : un ISBN mal formé ou déjà utilisé est refusé AVEC un message
            (le formulaire est réaffiché, pas d'erreur 500) ;
  - au moins UN auteur est obligatoire ;
  - supprimer un livre ne supprime PAS ses auteurs.

RÈGLE D'OR : pour chaque refus, on vérifie ce que le site DIT (le code)
ET ce que le site a FAIT (la base de données).
"""

import pytest

# Les deux modèles du catalogue
from catalogue.models import Auteur, Livre

# --- Constantes --------------------------------------------------------
URL_LISTE = "/catalogue/livres/"               # liste des livres
URL_CREATION = "/catalogue/livres/nouveau/"    # formulaire d'ajout
ISBN_ASTERIX = "9782070612758"                 # ISBN du livre déjà en base
ISBN_NOUVEAU = "9782070612765"                 # ISBN libre, pour créer un livre


# --- Adresses qui dépendent du livre ----------------------------------
# livre.pk = numéro unique du livre en base (ex. 1)
def url_modification(livre):
    return f"/catalogue/livres/{livre.pk}/modifier/"


def url_suppression(livre):
    return f"/catalogue/livres/{livre.pk}/supprimer/"


# ======================================================================
# PRÉPARATIONS (fixtures)
# ======================================================================
@pytest.fixture
def goscinny(db):
    """Un auteur en base."""
    return Auteur.objects.create(nom="René Goscinny")


@pytest.fixture
def uderzo(db):
    """Un deuxième auteur en base."""
    return Auteur.objects.create(nom="Albert Uderzo")


@pytest.fixture
def asterix(db, goscinny, uderzo):
    """Un livre déjà en base, avec SES DEUX auteurs.

    Une fixture peut utiliser d'autres fixtures : pytest crée d'abord
    goscinny et uderzo, puis appelle celle-ci.
    """
    livre = Livre.objects.create(
        titre="Astérix le Gaulois", isbn=ISBN_ASTERIX, categorie="BD"
    )
    livre.auteurs.add(goscinny, uderzo)   # relie le livre à ses 2 auteurs (N-N)
    return livre


# ======================================================================
# FONCTION D'AIDE : les données d'un formulaire de livre
# ======================================================================
def donnees_livre(auteurs, **changements):
    """Renvoie les données d'un formulaire de livre VALIDE.

    auteurs       = la liste des auteurs à "cocher" dans le formulaire
    **changements = pour remplacer UN ou plusieurs champs
                    ex. donnees_livre([goscinny], isbn="mauvais")

    Intérêt : chaque test montre seulement CE QUI CHANGE.
    """
    donnees = {
        "titre": "Le Petit Nicolas",
        "isbn": ISBN_NOUVEAU,
        # Un formulaire n'envoie pas les auteurs eux-mêmes,
        # mais leurs NUMÉROS (pk) : ex. [1, 2]
        "auteurs": [auteur.pk for auteur in auteurs],
        "annee": "1960",
        "categorie": "Jeunesse",
        "nb_exemplaires": "2",
    }
    # update() = remplace les valeurs par celles données en **changements
    donnees.update(changements)
    return donnees


# ======================================================================
# R = READ (LIRE) : la liste affiche les livres ET leurs auteurs
# ======================================================================
# parametrize : le même test lancé 3 fois, une fois par rôle
@pytest.mark.parametrize("role", ["ADMIN", "BIBLIOTHECAIRE", "ADHERENT"])
def test_tous_les_roles_voient_les_livres_et_leurs_auteurs(client, creer_utilisateur, asterix, role):
    # Préparer : un utilisateur de ce rôle est connecté
    # (creer_utilisateur vient de tests/conftest.py)
    client.force_login(creer_utilisateur(role))

    # Agir : il ouvre la liste des livres
    reponse = client.get(URL_LISTE)
    contenu = reponse.content.decode()   # le HTML de la page, en texte

    # Vérifier : la page s'affiche...
    assert reponse.status_code == 200
    # ...avec le livre...
    assert "Astérix le Gaulois" in contenu
    # ...et ses DEUX auteurs (preuve que la relation N-N est affichée)
    assert "René Goscinny" in contenu
    assert "Albert Uderzo" in contenu


def test_visiteur_non_connecte_est_redirige(client, db):
    # Personne n'est connecté -> redirection (302) vers la connexion
    assert client.get(URL_LISTE).status_code == 302


# ======================================================================
# C = CREATE (CRÉER)
# ======================================================================
# Chaque ligne = 1 cas de la table : (rôle, code attendu, livre créé ?)
@pytest.mark.parametrize(
    "role, code_attendu, livre_cree",
    [
        ("ADMIN", 302, True),            # créé, puis redirigé vers la liste
        ("BIBLIOTHECAIRE", 302, True),   # idem
        ("ADHERENT", 403, False),        # refusé, et RIEN n'est créé
    ],
)
def test_creation_selon_le_role(client, creer_utilisateur, goscinny, role, code_attendu, livre_cree):
    client.force_login(creer_utilisateur(role))

    # Agir : il remplit le formulaire (avec Goscinny comme auteur) et valide
    reponse = client.post(URL_CREATION, donnees_livre([goscinny]))

    # Vérifier n°1 : ce que le site DIT
    assert reponse.status_code == code_attendu
    # Vérifier n°2 : ce que le site a FAIT (le livre existe-t-il en base ?)
    assert Livre.objects.filter(isbn=ISBN_NOUVEAU).exists() is livre_cree


def test_les_auteurs_choisis_sont_enregistres(client, creer_utilisateur, goscinny, uderzo):
    """N-N : un livre créé avec 2 auteurs a bien ses 2 auteurs en base."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : on "coche" les DEUX auteurs dans le formulaire
    client.post(URL_CREATION, donnees_livre([goscinny, uderzo]))

    # Vérifier : on relit le livre en base et on regarde ses auteurs
    livre = Livre.objects.get(isbn=ISBN_NOUVEAU)
    # set(...) = un ENSEMBLE : on compare sans tenir compte de l'ordre
    assert set(livre.auteurs.all()) == {goscinny, uderzo}


def test_isbn_mal_forme_refuse_avec_message(client, creer_utilisateur, goscinny):
    """RM-05 : le formulaire utilise NOTRE validateur et affiche son message."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # 13 caractères, mais une LETTRE à la fin.
    # (pas de tiret : "978-..." ferait 14 caractères, et Django le refuserait
    #  dès la longueur maximale, SANS appeler notre validateur -> on ne
    #  testerait pas ce qu'on veut)
    reponse = client.post(URL_CREATION, donnees_livre([goscinny], isbn="978207061276X"))

    assert reponse.status_code == 200                     # formulaire réaffiché
    assert Livre.objects.count() == 0                     # rien n'est créé
    assert "13 chiffres" in reponse.content.decode()      # notre message est visible


def test_isbn_deja_utilise_refuse(client, creer_utilisateur, asterix, goscinny):
    """RM-05 : un doublon est refusé PROPREMENT (message, pas de plantage)."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : on essaie de créer un livre avec l'ISBN d'Astérix (déjà pris)
    reponse = client.post(URL_CREATION, donnees_livre([goscinny], isbn=ISBN_ASTERIX))

    # 200 = formulaire réaffiché avec un message.
    # (et PAS 500 = l'IntegrityError de la base qui ferait planter la page)
    assert reponse.status_code == 200
    # Toujours UN seul livre en base : Astérix
    assert Livre.objects.count() == 1


def test_au_moins_un_auteur_obligatoire(client, creer_utilisateur):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : aucun auteur coché -> liste vide []
    reponse = client.post(URL_CREATION, donnees_livre([]))

    assert reponse.status_code == 200      # formulaire réaffiché (erreur)
    assert Livre.objects.count() == 0      # rien n'est créé


# ======================================================================
# U = UPDATE (MODIFIER)
# ======================================================================
def test_modification_par_bibliothecaire(client, creer_utilisateur, asterix, goscinny):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    # Agir : on passe Astérix à 5 exemplaires
    # (on renvoie TOUS les champs, comme le ferait le vrai formulaire,
    #  en gardant le titre et l'ISBN d'Astérix)
    reponse = client.post(
        url_modification(asterix),
        donnees_livre([goscinny], titre="Astérix le Gaulois", isbn=ISBN_ASTERIX, nb_exemplaires="5"),
    )

    assert reponse.status_code == 302                 # succès -> redirection
    asterix.refresh_from_db()                         # relire la base
    assert asterix.nb_exemplaires == 5                # le changement est réel


def test_modification_refusee_a_adherent(client, creer_utilisateur, asterix, goscinny):
    client.force_login(creer_utilisateur("ADHERENT"))

    # Agir : un adhérent essaie de renommer le livre en "Pirate"
    reponse = client.post(
        url_modification(asterix),
        donnees_livre([goscinny], titre="Pirate", isbn=ISBN_ASTERIX),
    )

    assert reponse.status_code == 403                 # ce que le site DIT
    asterix.refresh_from_db()
    assert asterix.titre == "Astérix le Gaulois"      # ce que le site a FAIT : rien


# ======================================================================
# D = DELETE (SUPPRIMER)
# ======================================================================
def test_suppression_par_bibliothecaire(client, creer_utilisateur, asterix):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    reponse = client.post(url_suppression(asterix))

    assert reponse.status_code == 302                          # succès
    assert not Livre.objects.filter(pk=asterix.pk).exists()    # le livre n'existe plus


def test_suppression_refusee_a_adherent(client, creer_utilisateur, asterix):
    client.force_login(creer_utilisateur("ADHERENT"))
    reponse = client.post(url_suppression(asterix))

    assert reponse.status_code == 403                          # interdit
    assert Livre.objects.filter(pk=asterix.pk).exists()        # le livre est toujours là


def test_supprimer_un_livre_garde_ses_auteurs(client, creer_utilisateur, asterix, goscinny):
    """Goscinny a écrit d'autres livres : il ne doit pas disparaître avec Astérix."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    client.post(url_suppression(asterix))

    # 1. La suppression a VRAIMENT eu lieu.
    #    (CORRECTION : sans cette ligne, le test passait même quand la page
    #     n'existait pas (404) -> il ne prouvait rien. Découvert en phase rouge.)
    assert not Livre.objects.filter(pk=asterix.pk).exists()

    # 2. ...et l'auteur est toujours là.
    assert Auteur.objects.filter(pk=goscinny.pk).exists()