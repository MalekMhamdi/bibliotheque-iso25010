"""EF-10 : journal d'audit (qui, quoi, quand)."""
from datetime import date, timedelta

import pytest
from django.urls import reverse

from audit.models import JournalAudit
from audit.services import journaliser
from catalogue.models import Auteur, Livre
from prets.models import Pret

pytestmark = pytest.mark.django_db
A = JournalAudit.Action
S = Pret.Statut


def _livre(isbn="9782070409228"):
    return Livre.objects.create(
        titre="Les Misérables", isbn=isbn, categorie="Roman", nb_exemplaires=2
    )


# --- Le service ---------------------------------------------------------
def test_journaliser_enregistre_qui_quoi_quand(creer_utilisateur):
    """EF-10 : une entrée contient l'utilisateur, l'action, l'objet et la date."""
    admin = creer_utilisateur("ADMIN")
    livre = _livre()

    journaliser(admin, A.CREATION, livre, detail="test")

    entree = JournalAudit.objects.get()
    assert entree.utilisateur == admin
    assert entree.action == A.CREATION
    assert entree.entite == "Livre"
    assert entree.entite_id == livre.pk
    assert entree.detail == "test"
    assert entree.date_heure is not None


def test_entree_conservee_si_l_utilisateur_est_supprime(creer_utilisateur):
    """EF-10 : SET_NULL, l'historique survit à la suppression du compte."""
    admin = creer_utilisateur("ADMIN")
    journaliser(admin, A.CREATION, _livre())

    admin.delete()

    entree = JournalAudit.objects.get()
    assert entree.utilisateur is None


# --- Catalogue : création / modification / suppression -------------------
def test_creer_un_livre_par_la_page_est_journalise(client, creer_utilisateur):
    biblio = creer_utilisateur("BIBLIOTHECAIRE")
    client.force_login(biblio)
    auteur = Auteur.objects.create(nom="Victor Hugo")  # À ADAPTER

    reponse = client.post(  # À ADAPTER : noms des champs du formulaire
        reverse("livre_creation"),
        {
            "titre": "Nouveau livre",
            "isbn": "9782070409228",
            "categorie": "Roman",
            "nb_exemplaires": 1,
            "auteurs": [auteur.pk],
        },
    )

    assert reponse.status_code == 302
    entree = JournalAudit.objects.get()
    assert entree.utilisateur == biblio
    assert entree.action == A.CREATION
    assert entree.entite == "Livre"


def test_modifier_un_livre_est_journalise(client, creer_utilisateur):
    biblio = creer_utilisateur("BIBLIOTHECAIRE")
    client.force_login(biblio)
    livre = _livre()
    livre.auteurs.add(Auteur.objects.create(nom="Victor Hugo"))

    client.post(  # À ADAPTER
        reverse("livre_modification", args=[livre.pk]),
        {
            "titre": "Titre modifié",
            "isbn": livre.isbn,
            "categorie": "Roman",
            "nb_exemplaires": 2,
            "auteurs": [livre.auteurs.first().pk],
        },
    )

    entree = JournalAudit.objects.get()
    assert entree.action == A.MODIFICATION
    assert entree.entite_id == livre.pk


def test_supprimer_un_livre_est_journalise(client, creer_utilisateur):
    biblio = creer_utilisateur("BIBLIOTHECAIRE")
    client.force_login(biblio)
    livre = _livre()
    pk = livre.pk

    client.post(reverse("livre_suppression", args=[pk]))

    assert not Livre.objects.filter(pk=pk).exists()
    entree = JournalAudit.objects.get()
    assert entree.action == A.SUPPRESSION
    assert entree.entite_id == pk


def test_suppression_refusee_n_est_pas_journalisee(client, creer_utilisateur):
    """Un livre protégé par des prêts n'est pas supprimé : rien dans le journal."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    livre = _livre()
    Pret.objects.create(utilisateur=creer_utilisateur("ADHERENT"), livre=livre)

    client.post(reverse("livre_suppression", args=[livre.pk]))

    assert Livre.objects.filter(pk=livre.pk).exists()
    assert not JournalAudit.objects.exists()


# --- Prêts ---------------------------------------------------------------
def test_reserver_est_journalise_au_nom_de_l_adherent(client, creer_utilisateur):
    adherent = creer_utilisateur("ADHERENT")
    client.force_login(adherent)
    livre = _livre()

    client.post(reverse("pret_reserver", args=[livre.pk]))

    entree = JournalAudit.objects.get()
    assert entree.utilisateur == adherent
    assert entree.action == A.RESERVATION
    assert entree.entite == "Pret"


@pytest.mark.parametrize(
    "page, statut_initial, action",
    [
        ("pret_remettre", S.RESERVE, A.REMISE),
        ("pret_rendre", S.EN_COURS, A.RETOUR),
        ("pret_annuler", S.RESERVE, A.ANNULATION),
    ],
)
def test_actions_du_bibliothecaire_sont_journalisees(
    client, creer_utilisateur, page, statut_initial, action
):
    biblio = creer_utilisateur("BIBLIOTHECAIRE")
    client.force_login(biblio)
    pret = Pret.objects.create(
        utilisateur=creer_utilisateur("ADHERENT"),
        livre=_livre(),
        statut=statut_initial,
        date_emprunt=date.today(),
        date_retour_prevue=date.today() + timedelta(days=14),
    )

    client.post(reverse(page, args=[pret.pk]))

    entree = JournalAudit.objects.get()
    assert entree.utilisateur == biblio
    assert entree.action == action
    assert entree.entite_id == pret.pk


def test_action_refusee_n_est_pas_journalisee(client, creer_utilisateur):
    """Remettre un prêt déjà EN_COURS est refusé : rien dans le journal."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    pret = Pret.objects.create(
        utilisateur=creer_utilisateur("ADHERENT"), livre=_livre(), statut=S.EN_COURS
    )

    client.post(reverse("pret_remettre", args=[pret.pk]))

    assert not JournalAudit.objects.exists()


# --- La page /audit/ -----------------------------------------------------
@pytest.mark.parametrize(
    "role, attendu",
    [(None, 302), ("ADHERENT", 403), ("BIBLIOTHECAIRE", 403), ("ADMIN", 200)],
)
def test_droits_de_la_page_audit(client, creer_utilisateur, role, attendu):
    """EF-10 / cadrage §1 : page réservée à l'ADMIN."""
    if role:
        client.force_login(creer_utilisateur(role))

    assert client.get(reverse("audit_liste")).status_code == attendu


def test_audit_trie_du_plus_recent_au_plus_ancien(client, creer_utilisateur):
    admin = creer_utilisateur("ADMIN")
    client.force_login(admin)
    journaliser(admin, A.CREATION, _livre("9782000000001"), detail="PREMIER-EVENEMENT")
    journaliser(admin, A.CREATION, _livre("9782000000002"), detail="SECOND-EVENEMENT")

    contenu = client.get(reverse("audit_liste")).content.decode()

    assert contenu.index("SECOND-EVENEMENT") < contenu.index("PREMIER-EVENEMENT")


def test_audit_est_pagine(client, creer_utilisateur):
    admin = creer_utilisateur("ADMIN")
    client.force_login(admin)
    livre = _livre()
    for _ in range(25):
        journaliser(admin, A.MODIFICATION, livre)

    reponse = client.get(reverse("audit_liste"))

    assert reponse.context["page_obj"].paginator.num_pages == 2
    assert len(reponse.context["entrees"]) == 20


def test_lien_audit_dans_le_menu_pour_l_admin_seulement(client, creer_utilisateur):
    url = reverse("audit_liste")

    client.force_login(creer_utilisateur("ADMIN"))
    assert f'href="{url}"' in client.get("/").content.decode()

    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    assert f'href="{url}"' not in client.get("/").content.decode()

def test_creer_un_auteur_est_journalise(client, creer_utilisateur):
    biblio = creer_utilisateur("BIBLIOTHECAIRE")
    client.force_login(biblio)

    reponse = client.post(
        reverse("auteur_creation"), {"nom": "Victor Hugo", "nationalite": "Française"}
    )

    assert reponse.status_code == 302
    entree = JournalAudit.objects.get()
    assert entree.utilisateur == biblio
    assert entree.action == A.CREATION
    assert entree.entite == "Auteur"


def test_supprimer_un_auteur_est_journalise(client, creer_utilisateur):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    auteur = Auteur.objects.create(nom="Victor Hugo")
    pk = auteur.pk

    client.post(reverse("auteur_suppression", args=[pk]))

    entree = JournalAudit.objects.get()
    assert entree.action == A.SUPPRESSION
    assert entree.entite == "Auteur"
    assert entree.entite_id == pk    