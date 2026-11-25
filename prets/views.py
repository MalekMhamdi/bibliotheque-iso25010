"""Vues des prêts (EF-06) : aucune règle métier ici, seulement des appels aux services."""

from datetime import date

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.models import Livre
from comptes.permissions import role_requis
from prets import services
from prets.models import Pret
from prets.services import RegleMetierError


def _executer(request, action, message_succes):
    """Lance un service ; une erreur métier devient un message, pas une erreur 500."""
    try:
        action()
    except RegleMetierError as erreur:
        messages.error(request, str(erreur))
    else:
        messages.success(request, message_succes)


@role_requis("ADHERENT")
@require_POST
def pret_reserver(request, livre_pk):
    livre = get_object_or_404(Livre, pk=livre_pk)
    try:
        services.reserver(request.user, livre)
    except RegleMetierError as erreur:
        messages.error(request, str(erreur))
        return redirect("livre_liste")
    messages.success(request, f"« {livre.titre} » est réservé.")
    return redirect("mes_prets")


@role_requis("ADMIN", "BIBLIOTHECAIRE", "ADHERENT")
def mes_prets(request):
    prets = Pret.objects.filter(utilisateur=request.user).select_related("livre")
    prets = prets.order_by("-date_reservation", "-pk")
    return render(request, "prets/mes_prets.html", {"prets": prets})


@role_requis("ADMIN", "BIBLIOTHECAIRE")
def pret_liste(request):
    statut = request.GET.get("statut", "")
    prets = Pret.objects.select_related("livre", "utilisateur")
    if statut in Pret.Statut.values:
        prets = prets.filter(statut=statut)
    else:
        statut = ""
    prets = prets.order_by("-date_reservation", "-pk")
    contexte = {
        "prets": prets,
        "statuts": Pret.Statut.choices,
        "statut_courant": statut,
    }
    return render(request, "prets/pret_liste.html", contexte)


@role_requis("BIBLIOTHECAIRE")
@require_POST
def pret_remettre(request, pk):
    pret = get_object_or_404(Pret, pk=pk)
    _executer(
        request,
        lambda: services.remettre(pret, aujourd_hui=date.today()),
        "Livre remis à l'adhérent.",
    )
    return redirect("pret_liste")


@role_requis("BIBLIOTHECAIRE")
@require_POST
def pret_rendre(request, pk):
    pret = get_object_or_404(Pret, pk=pk)
    _executer(
        request,
        lambda: services.rendre(pret, aujourd_hui=date.today()),
        "Retour enregistré.",
    )
    return redirect("pret_liste")


@role_requis("ADHERENT", "BIBLIOTHECAIRE")
@require_POST
def pret_annuler(request, pk):
    pret = get_object_or_404(Pret, pk=pk)
    est_adherent = request.user.role == "ADHERENT"
    if est_adherent and pret.utilisateur_id != request.user.pk:
        raise PermissionDenied  # un adhérent n'annule que SES prêts
    _executer(request, lambda: services.annuler(pret), "Réservation annulée.")
    return redirect("mes_prets" if est_adherent else "pret_liste")
