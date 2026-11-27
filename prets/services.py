"""Services des prêts : workflow EF-06, EF-07 (règles RM-01 à RM-06).

Chaque fonction vérifie les règles, change le statut et s'exécute dans
transaction.atomic() : tout ou rien.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F

from audit.models import JournalAudit
from audit.services import journaliser
from prets import regles
from prets.models import Pret

S = Pret.Statut


class RegleMetierError(Exception):
    """Une règle métier n'est pas respectée (le message est affichable)."""


@transaction.atomic
def reserver(utilisateur, livre):
    """EF-06 : crée un prêt RESERVE (RM-01, RM-04, RM-06)."""
    a_un_retard = utilisateur.prets.filter(statut=S.EN_RETARD).exists()
    if not regles.peut_reserver(utilisateur.is_active, a_un_retard, utilisateur.penalite_impayee):
        raise RegleMetierError(
            "Réservation impossible : compte inactif, prêt en retard ou pénalité impayée."
        )

    nb_prets_actifs = utilisateur.prets.filter(statut__in=Pret.STATUTS_ACTIFS).count()
    if regles.quota_atteint(nb_prets_actifs):
        raise RegleMetierError(
            f"Réservation impossible : {regles.MAX_PRETS_ACTIFS} prêts actifs au maximum."
        )

    nb_actifs_du_livre = livre.prets.filter(statut__in=Pret.STATUTS_ACTIFS).count()
    if regles.nb_disponibles(livre.nb_exemplaires, nb_actifs_du_livre) == 0:
        raise RegleMetierError("Réservation impossible : aucun exemplaire disponible.")

    pret = Pret.objects.create(utilisateur=utilisateur, livre=livre)
    journaliser(utilisateur, JournalAudit.Action.RESERVATION, pret, detail=f"Livre : {livre.titre}")
    return pret


@transaction.atomic
def remettre(pret, aujourd_hui, acteur=None):
    """EF-07 : RESERVE -> EN_COURS, retour prévu = emprunt + 14 jours (RM-02)."""
    if pret.statut != S.RESERVE:
        raise RegleMetierError("Seul un prêt réservé peut être remis à l'adhérent.")
    pret.statut = S.EN_COURS
    pret.date_emprunt = aujourd_hui
    pret.date_retour_prevue = regles.date_retour_prevue(aujourd_hui)
    pret.save()
    journaliser(acteur, JournalAudit.Action.REMISE, pret)
    return pret


@transaction.atomic
def marquer_retards(aujourd_hui):
    """EF-07 : EN_COURS -> EN_RETARD si dépassé. Chaque passage est journalisé (EF-10)."""
    prets = list(
        Pret.objects.filter(statut=S.EN_COURS, date_retour_prevue__lt=aujourd_hui)
    )
    for pret in prets:
        pret.statut = S.EN_RETARD
        pret.save()
        journaliser(None, JournalAudit.Action.RETARD, pret)
    return len(prets)


@transaction.atomic
def rendre(pret, aujourd_hui, acteur=None):
    """EF-07 : EN_COURS/EN_RETARD -> RENDU, pénalité calculée (RM-03)."""
    if pret.statut not in (S.EN_COURS, S.EN_RETARD):
        raise RegleMetierError("Seul un prêt en cours ou en retard peut être rendu.")
    jours = regles.jours_de_retard(pret.date_retour_prevue, aujourd_hui)
    penalite = regles.calculer_penalite(jours)

    pret.statut = S.RENDU
    pret.date_retour_effective = aujourd_hui
    pret.penalite = penalite
    pret.save()

    get_user_model().objects.filter(pk=pret.utilisateur_id).update(
        penalite_impayee=F("penalite_impayee") + penalite
    )
    journaliser(acteur, JournalAudit.Action.RETOUR, pret, detail=f"Pénalité : {penalite} €")
    return pret


@transaction.atomic
def annuler(pret, acteur=None):
    """EF-06 : RESERVE -> ANNULE."""
    if pret.statut != S.RESERVE:
        raise RegleMetierError("Seule une réservation peut être annulée.")
    pret.statut = S.ANNULE
    pret.save()
    journaliser(acteur, JournalAudit.Action.ANNULATION, pret)
    return pret
