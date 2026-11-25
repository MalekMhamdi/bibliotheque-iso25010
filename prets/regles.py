"""Règles métier des prêts : fonctions PURES (sans base de données)."""
from datetime import date, timedelta
from decimal import Decimal

DUREE_PRET_JOURS = 14                      # RM-02
PENALITE_PAR_JOUR = Decimal("0.50")        # RM-03
PLAFOND_PENALITE = Decimal("10.00")        # RM-03


def date_retour_prevue(date_emprunt: date) -> date:
    """RM-02 : date d'emprunt + 14 jours."""
    return date_emprunt + timedelta(days=DUREE_PRET_JOURS)


def jours_de_retard(date_prevue: date, date_effective: date) -> int:
    """Nombre de jours de retard, jamais négatif."""
    return max(0, (date_effective - date_prevue).days)


def calculer_penalite(jours_retard: int) -> Decimal:
    """RM-03 : 0,50 EUR par jour, plafonnée à 10 EUR."""
    return min(jours_retard * PENALITE_PAR_JOUR, PLAFOND_PENALITE)

def peut_reserver(compte_actif: bool, a_un_retard: bool, penalite_impayee: Decimal) -> bool:
    """RM-04 : compte actif ET aucun prêt en retard ET pénalité impayée = 0."""
    return compte_actif and not a_un_retard and penalite_impayee == 0

MAX_PRETS_ACTIFS = 3  # RM-01


def quota_atteint(nb_prets_actifs: int) -> bool:
    """RM-01 : refusé si l'adhérent a déjà 3 prêts actifs."""
    return nb_prets_actifs >= MAX_PRETS_ACTIFS


def nb_disponibles(nb_exemplaires: int, nb_prets_actifs_du_livre: int) -> int:
    """RM-06 : exemplaires restants (jamais négatif)."""
    return max(0, nb_exemplaires - nb_prets_actifs_du_livre)