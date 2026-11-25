"""Workflow des prêts : EF-06, EF-07 (+ RM-01, RM-02, RM-03, RM-04, RM-06).

Les résultats attendus viennent du cadrage (docs/01-cadrage-exigences.md),
pas du code. La date « aujourd'hui » est passée en paramètre : aucune
dépendance à l'horloge.
"""

from datetime import date
from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model

from catalogue.models import Livre
from prets import services
from prets.models import Pret
from prets.services import RegleMetierError

pytestmark = pytest.mark.django_db

S = Pret.Statut  # RESERVE, EN_COURS, EN_RETARD, RENDU, ANNULE
STATUTS_ACTIFS = (S.RESERVE, S.EN_COURS, S.EN_RETARD)

_isbn = count(9780000000001)  # ISBN uniques de 13 chiffres


# --------------------------------------------------------------------------
# Aides
# --------------------------------------------------------------------------
def _livre(nb_exemplaires=1):
    return Livre.objects.create(
        titre="Livre de test",
        isbn=str(next(_isbn)),
        categorie="Roman",
        nb_exemplaires=nb_exemplaires,
    )


def _autre_adherent():
    """Un 2e adhérent (creer_utilisateur("ADHERENT") ne peut servir qu'une fois par test)."""
    return get_user_model().objects.create_user(
        username="autre", email="autre@exemple.com", password="MotDePasse!2026"
    )


def _pret(utilisateur, livre=None, statut=S.RESERVE, **champs):
    return Pret.objects.create(
        utilisateur=utilisateur, livre=livre or _livre(), statut=statut, **champs
    )


def _pret_en_cours(utilisateur, emprunt=date(2026, 3, 1), statut=S.EN_COURS):
    """Prêt emprunté le 01/03/2026 -> retour prévu le 15/03/2026 (RM-02)."""
    return _pret(
        utilisateur,
        statut=statut,
        date_emprunt=emprunt,
        date_retour_prevue=date(2026, 3, 15),
    )


@pytest.fixture
def adherent(creer_utilisateur):
    return creer_utilisateur("ADHERENT")


# --------------------------------------------------------------------------
# Transitions AUTORISÉES : nouveau statut + effets
# --------------------------------------------------------------------------
def test_remettre_passe_en_cours_et_fixe_les_dates(adherent):
    """EF-07 / RM-02 : RESERVE -> EN_COURS, retour prévu = emprunt + 14 jours."""
    pret = _pret(adherent)

    services.remettre(pret, aujourd_hui=date(2026, 3, 2))

    pret.refresh_from_db()
    assert pret.statut == S.EN_COURS
    assert pret.date_emprunt == date(2026, 3, 2)
    assert pret.date_retour_prevue == date(2026, 3, 16)


@pytest.mark.parametrize(
    "aujourd_hui, statut_attendu",
    [
        (date(2026, 3, 14), S.EN_COURS),  # avant la date prévue
        (date(2026, 3, 15), S.EN_COURS),  # valeur limite : le jour prévu
        (date(2026, 3, 16), S.EN_RETARD),  # limite + 1
    ],
)
def test_marquer_retards_selon_la_date(adherent, aujourd_hui, statut_attendu):
    """EF-07 : EN_COURS -> EN_RETARD seulement si aujourd'hui > date prévue."""
    pret = _pret_en_cours(adherent)

    services.marquer_retards(aujourd_hui=aujourd_hui)

    pret.refresh_from_db()
    assert pret.statut == statut_attendu


def test_marquer_retards_ne_touche_pas_aux_autres_statuts(adherent):
    """EF-07 : seuls les prêts EN_COURS peuvent passer EN_RETARD."""
    reserve = _pret(adherent, statut=S.RESERVE, date_retour_prevue=date(2026, 3, 15))
    rendu = _pret(adherent, statut=S.RENDU, date_retour_prevue=date(2026, 3, 15))

    services.marquer_retards(aujourd_hui=date(2026, 4, 30))

    reserve.refresh_from_db()
    rendu.refresh_from_db()
    assert reserve.statut == S.RESERVE
    assert rendu.statut == S.RENDU


@pytest.mark.parametrize("statut_depart", [S.EN_COURS, S.EN_RETARD])
@pytest.mark.parametrize(
    "date_rendu, penalite_attendue",
    [
        (date(2026, 3, 14), Decimal("0.00")),  # en avance
        (date(2026, 3, 15), Decimal("0.00")),  # valeur limite
        (date(2026, 3, 16), Decimal("0.50")),  # 1 jour
        (date(2026, 4, 3), Decimal("9.50")),  # 19 jours : plafond - 1
        (date(2026, 4, 4), Decimal("10.00")),  # 20 jours : le plafond
        (date(2026, 4, 5), Decimal("10.00")),  # 21 jours : plafond + 1 (RM-03)
    ],
)
def test_rendre_calcule_la_penalite(adherent, statut_depart, date_rendu, penalite_attendue):
    """EF-07 / RM-03 : -> RENDU, pénalité 0,50 €/jour plafonnée à 10 €."""
    pret = _pret_en_cours(adherent, statut=statut_depart)

    services.rendre(pret, aujourd_hui=date_rendu)

    pret.refresh_from_db()
    adherent.refresh_from_db()
    assert pret.statut == S.RENDU
    assert pret.date_retour_effective == date_rendu
    assert pret.penalite == penalite_attendue
    assert adherent.penalite_impayee == penalite_attendue


def test_rendre_ajoute_la_penalite_au_cumul_de_l_utilisateur(adherent):
    """RM-03 : la pénalité s'ajoute à la pénalité impayée déjà existante."""
    adherent.penalite_impayee = Decimal("2.00")
    adherent.save()
    pret = _pret_en_cours(adherent)

    services.rendre(pret, aujourd_hui=date(2026, 3, 16))  # 1 jour = 0,50 €

    adherent.refresh_from_db()
    assert adherent.penalite_impayee == Decimal("2.50")


def test_annuler_passe_en_annule(adherent):
    """EF-06 : RESERVE -> ANNULE."""
    pret = _pret(adherent)

    services.annuler(pret)

    pret.refresh_from_db()
    assert pret.statut == S.ANNULE


# --------------------------------------------------------------------------
# Transitions INTERDITES : RegleMetierError et statut inchangé
# --------------------------------------------------------------------------
ACTIONS = {
    "remettre": lambda p: services.remettre(p, aujourd_hui=date(2026, 3, 16)),
    "rendre": lambda p: services.rendre(p, aujourd_hui=date(2026, 3, 16)),
    "annuler": lambda p: services.annuler(p),
}

TRANSITIONS_INTERDITES = [
    ("remettre", S.EN_COURS),
    ("remettre", S.EN_RETARD),
    ("remettre", S.RENDU),
    ("remettre", S.ANNULE),
    ("rendre", S.RESERVE),
    ("rendre", S.RENDU),
    ("rendre", S.ANNULE),
    ("annuler", S.EN_COURS),
    ("annuler", S.EN_RETARD),
    ("annuler", S.RENDU),
    ("annuler", S.ANNULE),
]


@pytest.mark.parametrize(
    "action, statut_depart",
    TRANSITIONS_INTERDITES,
    ids=[f"{a}-{s}" for a, s in TRANSITIONS_INTERDITES],
)
def test_transition_interdite_refusee(adherent, action, statut_depart):
    """EF-06 / EF-07 : transition interdite -> erreur métier, rien ne change."""
    pret = _pret_en_cours(adherent, statut=statut_depart)

    with pytest.raises(RegleMetierError):
        ACTIONS[action](pret)

    pret.refresh_from_db()
    adherent.refresh_from_db()
    assert pret.statut == statut_depart
    assert pret.date_retour_effective is None
    assert pret.penalite == Decimal("0.00")
    assert adherent.penalite_impayee == Decimal("0.00")


# --------------------------------------------------------------------------
# reserver : cas accepté
# --------------------------------------------------------------------------
def test_reserver_cree_un_pret_reserve(adherent):
    """EF-06 : un adhérent éligible réserve un livre disponible."""
    livre = _livre(nb_exemplaires=1)

    pret = services.reserver(adherent, livre)

    assert pret.statut == S.RESERVE
    assert Pret.objects.filter(utilisateur=adherent, livre=livre).count() == 1


def test_reserver_accepte_avec_2_prets_actifs(adherent):
    """RM-01 : 2 prêts actifs -> la 3e réservation est encore permise."""
    _pret(adherent, statut=S.RESERVE)
    _pret(adherent, statut=S.EN_COURS)

    services.reserver(adherent, _livre())

    assert Pret.objects.filter(utilisateur=adherent).count() == 3


def test_reserver_ignore_les_prets_rendus_et_annules_dans_le_quota(adherent):
    """RM-01 : RENDU et ANNULE ne comptent pas parmi les prêts actifs."""
    for statut in (S.RENDU, S.ANNULE, S.RENDU, S.ANNULE):
        _pret(adherent, statut=statut)

    services.reserver(adherent, _livre())

    assert Pret.objects.filter(utilisateur=adherent, statut=S.RESERVE).count() == 1


# --------------------------------------------------------------------------
# reserver : refus (erreur métier + aucun prêt créé)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("statut_actif", STATUTS_ACTIFS)
def test_reserver_refuse_au_quota_de_3_prets_actifs(adherent, statut_actif):
    """RM-01 : 3 prêts actifs -> réservation refusée (quel que soit le statut actif)."""
    for _ in range(3):
        _pret(adherent, statut=statut_actif)
    livre = _livre()

    with pytest.raises(RegleMetierError):
        services.reserver(adherent, livre)

    assert not Pret.objects.filter(utilisateur=adherent, livre=livre).exists()


def test_reserver_refuse_si_aucun_exemplaire_disponible(adherent):
    """RM-06 : 1 exemplaire, 1 prêt actif d'un autre -> 0 disponible -> refusé."""
    livre = _livre(nb_exemplaires=1)
    _pret(_autre_adherent(), livre=livre, statut=S.EN_COURS)

    with pytest.raises(RegleMetierError):
        services.reserver(adherent, livre)

    assert not Pret.objects.filter(utilisateur=adherent).exists()


def test_reserver_accepte_si_l_exemplaire_a_ete_rendu(adherent):
    """RM-06 : un prêt RENDU libère l'exemplaire."""
    livre = _livre(nb_exemplaires=1)
    _pret(_autre_adherent(), livre=livre, statut=S.RENDU)

    services.reserver(adherent, livre)

    assert Pret.objects.filter(utilisateur=adherent, livre=livre).count() == 1


def test_reserver_refuse_compte_inactif(adherent):
    """RM-04 : compte inactif -> refusé."""
    adherent.is_active = False
    adherent.save()
    livre = _livre()

    with pytest.raises(RegleMetierError):
        services.reserver(adherent, livre)

    assert not Pret.objects.filter(utilisateur=adherent).exists()


def test_reserver_refuse_avec_un_pret_en_retard(adherent):
    """RM-04 : un prêt EN_RETARD bloque toute nouvelle réservation."""
    _pret(adherent, statut=S.EN_RETARD)
    livre = _livre()

    with pytest.raises(RegleMetierError):
        services.reserver(adherent, livre)

    assert not Pret.objects.filter(utilisateur=adherent, livre=livre).exists()


@pytest.mark.parametrize("penalite", [Decimal("0.01"), Decimal("0.50"), Decimal("10.00")])
def test_reserver_refuse_avec_penalite_impayee(adherent, penalite):
    """RM-04 : pénalité impayée > 0 (dès 0,01 €) -> refusé."""
    adherent.penalite_impayee = penalite
    adherent.save()
    livre = _livre()

    with pytest.raises(RegleMetierError):
        services.reserver(adherent, livre)

    assert not Pret.objects.filter(utilisateur=adherent).exists()
