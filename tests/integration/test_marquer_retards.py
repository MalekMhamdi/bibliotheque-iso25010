"""EF-07 : passage automatique des prêts EN_COURS en EN_RETARD."""

from datetime import date, timedelta
from io import StringIO
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from catalogue.models import Livre
from prets.models import Pret

pytestmark = pytest.mark.django_db

S = Pret.Statut
_isbn = count(9784000000001)
_num = count(1)


def _pret(statut, retour_prevu):
    n = next(_num)
    utilisateur = get_user_model().objects.create_user(
        username=f"u{n}", email=f"u{n}@exemple.com", password="MotDePasse!2026"
    )
    livre = Livre.objects.create(
        titre=f"Livre {n}", isbn=str(next(_isbn)), categorie="Roman", nb_exemplaires=1
    )
    return Pret.objects.create(
        utilisateur=utilisateur,
        livre=livre,
        statut=statut,
        date_emprunt=retour_prevu - timedelta(days=14),
        date_retour_prevue=retour_prevu,
    )


def test_la_commande_marque_les_prets_en_retard():
    hier = date.today() - timedelta(days=1)
    en_retard = _pret(S.EN_COURS, hier)
    dans_les_temps = _pret(S.EN_COURS, date.today())  # limite : pas encore en retard
    reserve = _pret(S.RESERVE, hier)

    sortie = StringIO()
    call_command("marquer_retards", stdout=sortie)

    for p in (en_retard, dans_les_temps, reserve):
        p.refresh_from_db()
    assert en_retard.statut == S.EN_RETARD
    assert dans_les_temps.statut == S.EN_COURS
    assert reserve.statut == S.RESERVE
    assert "1" in sortie.getvalue()


def test_la_commande_est_idempotente():
    _pret(S.EN_COURS, date.today() - timedelta(days=3))

    call_command("marquer_retards", stdout=StringIO())
    sortie = StringIO()
    call_command("marquer_retards", stdout=sortie)

    assert "0" in sortie.getvalue()


def test_le_tableau_de_bord_marque_les_retards(client, creer_utilisateur):
    """Les chiffres affichés sont à jour même sans lancer la commande."""
    client.force_login(creer_utilisateur("ADMIN"))
    pret = _pret(S.EN_COURS, date.today() - timedelta(days=2))

    client.get(reverse("tableau_de_bord"))

    pret.refresh_from_db()
    assert pret.statut == S.EN_RETARD


def test_la_liste_des_prets_marque_les_retards(client, creer_utilisateur):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    pret = _pret(S.EN_COURS, date.today() - timedelta(days=2))

    client.get(reverse("pret_liste"))

    pret.refresh_from_db()
    assert pret.statut == S.EN_RETARD
