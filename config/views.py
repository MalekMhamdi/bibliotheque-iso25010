"""Vues techniques du projet (hors métier)."""

from django.http import JsonResponse


def health(request):
    """Contrôle de santé : indique que le serveur répond.

    Utilisé par Docker (healthcheck) et par les tests.
    """
    return JsonResponse({"status": "ok"})