"""Pages des prêts : EF-06 (droits, effets réels, messages d'erreur, menu)."""

from datetime import date, timedelta
from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from catalogue.models import Livre
from prets.models import Pret

pytestmark = pytest.mark.django_db

S = Pret.Statut
_isbn = count(9781000000001)


# --------------------------------------------------------------------------
# Aides
# --------------------------------------------------------------------------
def _livre(titre="Livre de test", nb_exemplaires=1):
    return Livre.objects.create(
        titre=titre,
        isbn=str(next(_isbn)),
        categorie="Roman",
        nb_exemplaires=nb_exemplaires,
    )


def _autre_adherent():
    """2e adhérent (creer_utilisateur ne peut servir qu'une fois par rôle et par test)."""
    return get_user_model().objects.create_user(
        username="autre", email="autre@exemple.com", password="MotDePasse!2026"
    )


def _pret(utilisateur, livre=None, statut=S.RESERVE, **champs):
    return Pret.objects.create(
        utilisateur=utilisateur, livre=livre or _livre(), statut=statut, **champs
    )


def _messages(reponse):
    return [str(m) for m in get_messages(reponse.wsgi_request)]


# --------------------------------------------------------------------------
# Table des droits (cadrage §1) : page, méthode, rôle, code attendu
# --------------------------------------------------------------------------
DROITS = [
    ("pret_liste", "get", None, 302),
    ("pret_liste", "get", "ADHERENT", 403),
    ("pret_liste", "get", "BIBLIOTHECAIRE", 200),
    ("pret_liste", "get", "ADMIN", 200),
    ("mes_prets", "get", None, 302),
    ("mes_prets", "get", "ADHERENT", 200),
    ("mes_prets", "get", "BIBLIOTHECAIRE", 200),
    ("mes_prets", "get", "ADMIN", 200),
    ("pret_reserver", "post", None, 302),
    ("pret_reserver", "post", "ADHERENT", 302),
    ("pret_reserver", "post", "BIBLIOTHECAIRE", 403),
    ("pret_reserver", "post", "ADMIN", 403),
    ("pret_remettre", "post", None, 302),
    ("pret_remettre", "post", "ADHERENT", 403),
    ("pret_remettre", "post", "BIBLIOTHECAIRE", 302),
    ("pret_remettre", "post", "ADMIN", 403),
    ("pret_rendre", "post", None, 302),
    ("pret_rendre", "post", "ADHERENT", 403),
    ("pret_rendre", "post", "BIBLIOTHECAIRE", 302),
    ("pret_rendre", "post", "ADMIN", 403),
    ("pret_annuler", "post", None, 302),
    ("pret_annuler", "post", "BIBLIOTHECAIRE", 302),
    ("pret_annuler", "post", "ADMIN", 403),
]


def _cible(page):
    """Construit l'adresse de la page (avec un prêt ou un livre au bon statut)."""
    if page in ("pret_liste", "mes_prets"):
        return reverse(page)
    if page == "pret_reserver":
        return reverse(page, args=[_livre().pk])
    statut = S.EN_COURS if page == "pret_rendre" else S.RESERVE
    pret = _pret(
        _autre_adherent(),
        statut=statut,
        date_emprunt=date.today(),
        date_retour_prevue=date.today() + timedelta(days=14),
    )
    return reverse(page, args=[pret.pk])


@pytest.mark.parametrize(
    "page, methode, role, attendu",
    DROITS,
    ids=[f"{p}-{m}-{r}" for p, m, r, _ in DROITS],
)
def test_droits_des_pages_de_prets(client, creer_utilisateur, page, methode, role, attendu):
    """EF-06 : non connecté 302, mauvais rôle 403, bon rôle OK."""
    if role:
        client.force_login(creer_utilisateur(role))
    url = _cible(page)

    reponse = getattr(client, methode)(url)

    assert reponse.status_code == attendu


# --------------------------------------------------------------------------
# Réserver
# --------------------------------------------------------------------------
def test_reserver_cree_le_pret_en_base(client, creer_utilisateur):
    """EF-06 : l'adhérent réserve -> un prêt RESERVE existe en base."""
    adherent = creer_utilisateur("ADHERENT")
    client.force_login(adherent)
    livre = _livre()

    reponse = client.post(reverse("pret_reserver", args=[livre.pk]))

    assert reponse.status_code == 302
    assert Pret.objects.get(utilisateur=adherent, livre=livre).statut == S.RESERVE


def test_reserver_refuse_affiche_un_message_sans_creer_de_pret(client, creer_utilisateur):
    """EF-06 / RM-01 : quota atteint -> message, redirection, aucun prêt créé."""
    adherent = creer_utilisateur("ADHERENT")
    client.force_login(adherent)
    for _ in range(3):
        _pret(adherent, statut=S.EN_COURS)
    livre = _livre()

    reponse = client.post(reverse("pret_reserver", args=[livre.pk]))

    assert reponse.status_code == 302
    assert not Pret.objects.filter(utilisateur=adherent, livre=livre).exists()
    assert any("Réservation impossible" in m for m in _messages(reponse))


def test_reserver_en_get_est_refuse(client, creer_utilisateur):
    """Réserver modifie des données : GET interdit (405)."""
    client.force_login(creer_utilisateur("ADHERENT"))

    reponse = client.get(reverse("pret_reserver", args=[_livre().pk]))

    assert reponse.status_code == 405


def test_reserver_livre_inexistant_donne_404(client, creer_utilisateur):
    client.force_login(creer_utilisateur("ADHERENT"))

    reponse = client.post(reverse("pret_reserver", args=[99999]))

    assert reponse.status_code == 404


# --------------------------------------------------------------------------
# Remettre / rendre (bibliothécaire)
# --------------------------------------------------------------------------
def test_remettre_met_le_pret_en_cours_avec_les_dates(client, creer_utilisateur):
    """EF-07 / RM-02 : RESERVE -> EN_COURS, retour prévu = aujourd'hui + 14 jours."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    pret = _pret(_autre_adherent())

    reponse = client.post(reverse("pret_remettre", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == S.EN_COURS
    assert pret.date_emprunt == date.today()
    assert pret.date_retour_prevue == date.today() + timedelta(days=14)


def test_remettre_interdit_affiche_un_message_et_ne_change_rien(client, creer_utilisateur):
    """EF-07 : remettre un prêt déjà EN_COURS -> message, statut inchangé, pas de 500."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    pret = _pret(_autre_adherent(), statut=S.EN_COURS)

    reponse = client.post(reverse("pret_remettre", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == S.EN_COURS
    assert _messages(reponse)


def test_rendre_en_retard_calcule_la_penalite(client, creer_utilisateur):
    """EF-07 / RM-03 : 2 jours de retard -> 1,00 € ajouté à la pénalité de l'adhérent."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    adherent = _autre_adherent()
    pret = _pret(
        adherent,
        statut=S.EN_COURS,
        date_emprunt=date.today() - timedelta(days=16),
        date_retour_prevue=date.today() - timedelta(days=2),
    )

    reponse = client.post(reverse("pret_rendre", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    adherent.refresh_from_db()
    assert pret.statut == S.RENDU
    assert pret.penalite == Decimal("1.00")
    assert adherent.penalite_impayee == Decimal("1.00")


def test_rendre_interdit_affiche_un_message_et_ne_change_rien(client, creer_utilisateur):
    """EF-07 : rendre un prêt RESERVE -> message, statut inchangé."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    pret = _pret(_autre_adherent(), statut=S.RESERVE)

    reponse = client.post(reverse("pret_rendre", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == S.RESERVE
    assert _messages(reponse)


# --------------------------------------------------------------------------
# Annuler (adhérent : le sien ; bibliothécaire : tous)
# --------------------------------------------------------------------------
def test_adherent_annule_son_pret(client, creer_utilisateur):
    adherent = creer_utilisateur("ADHERENT")
    client.force_login(adherent)
    pret = _pret(adherent)

    reponse = client.post(reverse("pret_annuler", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == S.ANNULE


def test_adherent_ne_peut_pas_annuler_le_pret_d_un_autre(client, creer_utilisateur):
    """EF-06 : prêt d'un autre -> 403 et statut inchangé."""
    client.force_login(creer_utilisateur("ADHERENT"))
    pret = _pret(_autre_adherent())

    reponse = client.post(reverse("pret_annuler", args=[pret.pk]))

    assert reponse.status_code == 403
    pret.refresh_from_db()
    assert pret.statut == S.RESERVE


def test_bibliothecaire_annule_n_importe_quel_pret(client, creer_utilisateur):
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    pret = _pret(_autre_adherent())

    reponse = client.post(reverse("pret_annuler", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == S.ANNULE


def test_annuler_un_pret_en_cours_affiche_un_message(client, creer_utilisateur):
    """EF-06 : annuler un prêt EN_COURS est interdit -> message, statut inchangé."""
    adherent = creer_utilisateur("ADHERENT")
    client.force_login(adherent)
    pret = _pret(adherent, statut=S.EN_COURS)

    reponse = client.post(reverse("pret_annuler", args=[pret.pk]))

    assert reponse.status_code == 302
    pret.refresh_from_db()
    assert pret.statut == S.EN_COURS
    assert _messages(reponse)


# --------------------------------------------------------------------------
# Listes
# --------------------------------------------------------------------------
def test_mes_prets_montre_seulement_les_siens(client, creer_utilisateur):
    """EF-06 : un adhérent ne voit pas les prêts des autres."""
    adherent = creer_utilisateur("ADHERENT")
    client.force_login(adherent)
    _pret(adherent, livre=_livre("Mon livre"))
    _pret(_autre_adherent(), livre=_livre("Livre secret"))

    contenu = client.get(reverse("mes_prets")).content.decode()

    assert "Mon livre" in contenu
    assert "Livre secret" not in contenu


def test_mes_prets_affiche_la_penalite_impayee(client, creer_utilisateur):
    adherent = creer_utilisateur("ADHERENT")
    adherent.penalite_impayee = Decimal("2.50")
    adherent.save()
    client.force_login(adherent)

    contenu = client.get(reverse("mes_prets")).content.decode()

    assert "2,50" in contenu  # LANGUAGE_CODE = fr-fr : virgule décimale


def test_liste_des_prets_filtre_par_statut(client, creer_utilisateur):
    """EF-06 : /prets/ liste tous les prêts, filtrables par statut."""
    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    adherent = _autre_adherent()
    _pret(adherent, livre=_livre("Titre reserve"), statut=S.RESERVE)
    _pret(adherent, livre=_livre("Titre encours"), statut=S.EN_COURS)

    tous = client.get(reverse("pret_liste")).content.decode()
    filtre = client.get(reverse("pret_liste"), {"statut": "EN_COURS"}).content.decode()

    assert "Titre reserve" in tous and "Titre encours" in tous
    assert "Titre encours" in filtre
    assert "Titre reserve" not in filtre


# --------------------------------------------------------------------------
# Menu et bouton « Réserver »
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "role, voit_mes_prets, voit_pret_liste",
    [
        ("ADHERENT", True, False),
        ("BIBLIOTHECAIRE", True, True),
        ("ADMIN", True, True),
    ],
)
def test_menu_selon_le_role(client, creer_utilisateur, role, voit_mes_prets, voit_pret_liste):
    """EF-06 : liens « Mes prêts » / « Prêts » selon le rôle."""
    client.force_login(creer_utilisateur(role))

    contenu = client.get("/").content.decode()

    assert (f'href="{reverse("mes_prets")}"' in contenu) is voit_mes_prets
    assert (f'href="{reverse("pret_liste")}"' in contenu) is voit_pret_liste


def test_bouton_reserver_visible_pour_l_adherent_seulement(client, creer_utilisateur):
    livre = _livre()
    url_reserver = reverse("pret_reserver", args=[livre.pk])

    client.force_login(creer_utilisateur("ADHERENT"))
    assert url_reserver in client.get(reverse("livre_liste")).content.decode()

    client.force_login(creer_utilisateur("BIBLIOTHECAIRE"))
    assert url_reserver not in client.get(reverse("livre_liste")).content.decode()