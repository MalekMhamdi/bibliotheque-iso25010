"""EF-09 : tableau de bord (chiffres exacts, top 5, période, droits)."""
from datetime import date
from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from catalogue.models import Livre
from prets.models import Pret
from prets.statistiques import calculer_statistiques

pytestmark = pytest.mark.django_db

S = Pret.Statut
_isbn = count(9783000000001)
_num = count(1)


def _livre(titre="Livre"):
    return Livre.objects.create(
        titre=titre, isbn=str(next(_isbn)), categorie="Roman", nb_exemplaires=5
    )


def _adherent():
    n = next(_num)
    return get_user_model().objects.create_user(
        username=f"adh{n}", email=f"adh{n}@exemple.com", password="MotDePasse!2026"
    )


def _pret(livre, statut=S.RESERVE, penalite="0.00", reserve_le=date(2026, 3, 10)):
    return Pret.objects.create(
        utilisateur=_adherent(),
        livre=livre,
        statut=statut,
        penalite=Decimal(penalite),
        date_reservation=reserve_le,
    )


def test_chiffres_exacts():
    """3 prêts actifs dont 1 en retard ; pénalités 0,50 + 10,00."""
    livre = _livre()
    _pret(livre, S.RESERVE)
    _pret(livre, S.EN_COURS)
    _pret(livre, S.EN_RETARD)
    _pret(livre, S.RENDU, penalite="0.50")
    _pret(livre, S.RENDU, penalite="10.00")

    stats = calculer_statistiques()

    assert stats["nb_actifs"] == 3
    assert stats["nb_retard"] == 1
    assert stats["total_penalites"] == Decimal("10.50")


def test_total_penalites_vaut_zero_sans_donnees():
    stats = calculer_statistiques()

    assert stats["total_penalites"] == Decimal("0.00")
    assert stats["nb_actifs"] == 0
    assert stats["top_livres"] == []


def test_top_5_dans_le_bon_ordre_et_limite_a_5():
    emprunts = {"L1": 1, "L2": 6, "L3": 3, "L4": 5, "L5": 2, "L6": 4, "L7": 7}
    for titre, nb in emprunts.items():
        livre = _livre(titre)
        for _ in range(nb):
            _pret(livre)

    top = calculer_statistiques()["top_livres"]

    assert [(l.titre, l.nb_prets) for l in top] == [
        ("L7", 7), ("L2", 6), ("L4", 5), ("L6", 4), ("L3", 3),
    ]


def test_filtre_de_periode():
    livre = _livre()
    _pret(livre, S.EN_COURS, reserve_le=date(2026, 1, 15))
    _pret(livre, S.EN_COURS, reserve_le=date(2026, 3, 15))
    _pret(livre, S.EN_COURS, reserve_le=date(2026, 5, 15))

    stats = calculer_statistiques(debut=date(2026, 3, 1), fin=date(2026, 3, 31))

    assert stats["nb_actifs"] == 1


def test_bornes_de_la_periode_incluses():
    livre = _livre()
    _pret(livre, S.EN_COURS, reserve_le=date(2026, 3, 1))
    _pret(livre, S.EN_COURS, reserve_le=date(2026, 3, 31))

    stats = calculer_statistiques(debut=date(2026, 3, 1), fin=date(2026, 3, 31))

    assert stats["nb_actifs"] == 2


@pytest.mark.parametrize(
    "role, attendu",
    [(None, 302), ("ADHERENT", 403), ("BIBLIOTHECAIRE", 200), ("ADMIN", 200)],
)
def test_droits_de_la_page(client, creer_utilisateur, role, attendu):
    if role:
        client.force_login(creer_utilisateur(role))

    assert client.get(reverse("tableau_de_bord")).status_code == attendu


def test_la_page_affiche_les_chiffres(client, creer_utilisateur):
    client.force_login(creer_utilisateur("ADMIN"))
    livre = _livre("Livre Phare")
    _pret(livre, S.EN_RETARD)
    _pret(livre, S.RENDU, penalite="2.50")

    contenu = client.get(reverse("tableau_de_bord")).content.decode()

    assert "Livre Phare" in contenu
    assert "2,50" in contenu


def test_filtre_de_la_page(client, creer_utilisateur):
    client.force_login(creer_utilisateur("ADMIN"))
    _pret(_livre("Livre Mars"), reserve_le=date(2026, 3, 10))
    _pret(_livre("Livre Mai"), reserve_le=date(2026, 5, 10))

    contenu = client.get(
        reverse("tableau_de_bord"), {"debut": "2026-03-01", "fin": "2026-03-31"}
    ).content.decode()

    assert "Livre Mars" in contenu
    assert "Livre Mai" not in contenu


def test_dates_invalides_ne_provoquent_pas_d_erreur_500(client, creer_utilisateur):
    client.force_login(creer_utilisateur("ADMIN"))

    reponse = client.get(reverse("tableau_de_bord"), {"debut": "pas-une-date"})

    assert reponse.status_code == 200


def test_lien_dans_le_menu_pour_le_personnel_seulement(client, creer_utilisateur):
    url = reverse("tableau_de_bord")

    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    assert f'href="{url}"' in client.get("/").content.decode()

    client.force_login(creer_utilisateur("ADHERENT"))
    assert f'href="{url}"' not in client.get("/").content.decode()