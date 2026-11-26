"""EQ-05 : fiabilité (rollback, pas d'erreur 500, récupération)."""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from audit.models import JournalAudit
from catalogue.models import Auteur, Livre
from prets import services
from prets.models import Pret

pytestmark = pytest.mark.django_db

_isbn = count(9785000000001)


def _livre(**champs):
    return Livre.objects.create(
        titre="Livre fiabilité",
        isbn=str(next(_isbn)),
        categorie="Roman",
        nb_exemplaires=1,
        **champs,
    )


# --- 1. Rien de partiel en cas d'erreur (rollback) ----------------------
def test_panne_du_journal_annule_la_reservation(creer_utilisateur, monkeypatch):
    """Si journaliser() échoue au milieu de reserver(), aucun prêt n'est créé."""
    adherent = creer_utilisateur("ADHERENT")
    livre = _livre()

    def panne(*args, **kwargs):
        raise RuntimeError("panne simulée")

    monkeypatch.setattr(services, "journaliser", panne)

    with pytest.raises(RuntimeError):
        services.reserver(adherent, livre)

    assert not Pret.objects.exists()
    assert not JournalAudit.objects.exists()


def test_panne_du_journal_annule_le_retour_et_la_penalite(creer_utilisateur, monkeypatch):
    """rendre() : statut, pénalité du prêt et pénalité de l'adhérent restent inchangés."""
    from datetime import date, timedelta
    from decimal import Decimal

    adherent = creer_utilisateur("ADHERENT")
    pret = Pret.objects.create(
        utilisateur=adherent,
        livre=_livre(),
        statut=Pret.Statut.EN_COURS,
        date_emprunt=date.today() - timedelta(days=20),
        date_retour_prevue=date.today() - timedelta(days=6),
    )

    def panne(*args, **kwargs):
        raise RuntimeError("panne simulée")

    monkeypatch.setattr(services, "journaliser", panne)

    with pytest.raises(RuntimeError):
        services.rendre(pret, aujourd_hui=date.today())

    pret.refresh_from_db()
    adherent.refresh_from_db()
    assert pret.statut == Pret.Statut.EN_COURS
    assert adherent.penalite_impayee == Decimal("0.00")


# --- 2. Une erreur ne fait pas planter le serveur -----------------------
@pytest.mark.parametrize(
    "url",
    ["/page-inexistante/", "/catalogue/livres/99999/modifier/", "/prets/99999/rendre/"],
)
def test_adresse_inexistante_donne_404_pas_500(client, creer_utilisateur, url):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))

    reponse = client.get(url)

    assert reponse.status_code in (404, 405)  # 405 : POST seulement, jamais 500


def test_livre_protege_donne_un_message_pas_une_erreur_500(client, creer_utilisateur):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    livre = _livre()
    Pret.objects.create(utilisateur=creer_utilisateur("ADHERENT"), livre=livre)

    reponse = client.post(reverse("livre_suppression", args=[livre.pk]))

    assert reponse.status_code == 200
    assert Livre.objects.filter(pk=livre.pk).exists()


def test_regle_metier_refusee_ne_plante_pas_la_page(client, creer_utilisateur):
    """Remettre un prêt déjà rendu : message + redirection, jamais 500."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    adherent = get_user_model().objects.create_user(
        username="x", email="x@exemple.com", password="MotDePasse!2026"
    )
    pret = Pret.objects.create(utilisateur=adherent, livre=_livre(), statut=Pret.Statut.RENDU)

    reponse = client.post(reverse("pret_remettre", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == Pret.Statut.RENDU


def test_formulaire_invalide_reaffiche_la_page(client, creer_utilisateur):
    """ISBN invalide : page réaffichée (200), rien en base, pas de 500."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    auteur = Auteur.objects.create(nom="Auteur")

    reponse = client.post(
        reverse("livre_creation"),
        {
            "titre": "X",
            "isbn": "123",
            "categorie": "Roman",
            "nb_exemplaires": 1,
            "auteurs": [auteur.pk],
        },
    )

    assert reponse.status_code == 200
    assert not Livre.objects.exists()
