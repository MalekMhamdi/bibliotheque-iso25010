"""Contrôle des droits par rôle (EF-02).

Le « vigile » de l'application : un décorateur à placer devant une vue
pour n'y laisser entrer que certains rôles.
"""
"Un décorateur est une fonction qui enveloppe une autre fonction pour ajouter un contrôle avant elle."
"On le place avec un @ juste au-dessus d'une vue."
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def role_requis(*roles_autorises):
    """N'autorise la vue qu'aux utilisateurs ayant l'un des rôles donnés.

    - visiteur non connecté      -> redirigé vers la page de connexion (302) ;
    - connecté sans le bon rôle  -> accès interdit (403) ;
    - connecté avec le bon rôle  -> la vue s'exécute normalement.

    Exemple :
        @role_requis("ADMIN")
        def liste_utilisateurs(request): ...
    """

    def decorateur(vue):
        @wraps(vue)  # garde le nom et la documentation de la vue d'origine
        def vue_protegee(request, *args, **kwargs):
            # Contrôle n°1 : est-il connecté ?
            if not request.user.is_authenticated:
                # Non -> "connecte-toi d'abord" (302), puis retour ici
                return redirect_to_login(request.get_full_path())

            # Contrôle n°2 : a-t-il un rôle autorisé ?
            if request.user.role not in roles_autorises:
                # Non -> "interdit" (403)
                raise PermissionDenied

            # Les deux contrôles sont passés : on exécute la vraie vue
            return vue(request, *args, **kwargs)

        return vue_protegee

    return decorateur