"""Règles métier des prêts : fonctions PURES (sans base de données)."""
from datetime import date, timedelta
from decimal import Decimal

DUREE_PRET_JOURS = 14                      # RM-02
PENALITE_PAR_JOUR = Decimal("0.50")        # RM-03
PLAFOND_PENALITE = Decimal("10.00")        # RM-03


def date_retour_prevue(date_emprunt: date) -> date:
    """RM-02 : date d'emprunt + 14 jours (timedelta gère mois et bissextiles)."""
    return date_emprunt + timedelta(days=DUREE_PRET_JOURS)


def jours_de_retard(date_prevue: date, date_effective: date) -> int:
    """Nombre de jours de retard, jamais négatif (rendu en avance = 0)."""
    return max(0, (date_effective - date_prevue).days)


def calculer_penalite(jours_retard: int) -> Decimal:
    """RM-03 : 0,50 EUR par jour, plafonnée à 10 EUR."""
    return min(jours_retard * PENALITE_PAR_JOUR, PLAFOND_PENALITE)