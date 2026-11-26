"""EF-09 : statistiques du tableau de bord, en requêtes agrégées."""
from decimal import Decimal

from django.db.models import Count, Sum

from catalogue.models import Livre
from prets.models import Pret

S = Pret.Statut


def calculer_statistiques(debut=None, fin=None):
    """Chiffres du tableau de bord ; debut/fin (inclus) filtrent sur date_reservation."""
    prets = Pret.objects.all()
    if debut:
        prets = prets.filter(date_reservation__gte=debut)
    if fin:
        prets = prets.filter(date_reservation__lte=fin)

    top = (
        Livre.objects.filter(prets__in=prets)
        .annotate(nb_prets=Count("prets"))
        .order_by("-nb_prets", "titre")[:5]
    )
    total = prets.aggregate(total=Sum("penalite"))["total"] or Decimal("0.00")

    return {
        "nb_actifs": prets.filter(statut__in=Pret.STATUTS_ACTIFS).count(),
        "nb_retard": prets.filter(statut=S.EN_RETARD).count(),
        "top_livres": list(top),
        "total_penalites": total,
    }