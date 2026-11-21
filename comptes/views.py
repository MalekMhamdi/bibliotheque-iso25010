

from django.contrib.auth import get_user_model
from django.shortcuts import render

from comptes.permissions import role_requis

Utilisateur = get_user_model()


@role_requis(Utilisateur.Role.ADMIN)   # 🛡️ le vigile : ADMIN uniquement
def liste_utilisateurs(request):
    """Espace admin : liste de tous les utilisateurs (EF-05)."""
    utilisateurs = Utilisateur.objects.order_by("username")   # tous, triés par nom
    return render(
        request,
        "comptes/liste_utilisateurs.html",
        {"utilisateurs": utilisateurs},   # données envoyées à la page HTML
    )
