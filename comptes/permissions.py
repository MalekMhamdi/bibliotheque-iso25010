"""Contrôle d'accès par rôle (EF-02) : le « vigile » de l'application.

Organisation du fichier :

    verifier_role()      <- LE CONTRÔLE, écrit UNE seule fois
        ▲          ▲
        │          │
  @role_requis   RoleRequisMixin
  (pages         (pages
   FONCTIONS)     CLASSES : ListView, CreateView, UpdateView, DeleteView)

Les deux vigiles appellent le même contrôle : si on change la règle,
on la change à UN seul endroit (maintenabilité), et on ne peut pas
oublier un contrôle dans une page (sécurité).
"""

# wraps : outil Python qui garde le nom de la page d'origine (messages d'erreur lisibles)
from functools import wraps

# redirect_to_login : fabrique une redirection (302) vers la page de connexion
from django.contrib.auth.views import redirect_to_login

# PermissionDenied : erreur que Django transforme automatiquement en réponse 403
from django.core.exceptions import PermissionDenied


# ======================================================================
# 1. LE CONTRÔLE (commun aux deux vigiles)
# ======================================================================
def verifier_role(request, roles_autorises):
    """Vérifie si le visiteur a le droit d'entrer.

    request          = la requête du visiteur (qui est-il ? est-il connecté ?)
    roles_autorises  = les rôles qui ont le droit, ex. ("ADMIN", "BIBLIOTHECAIRE")

    3 résultats possibles :
      - pas connecté   -> renvoie une redirection vers la connexion (302)
      - mauvais rôle   -> lève PermissionDenied   (Django répond 403)
      - rôle autorisé  -> renvoie None            ("rien à signaler, entre")
    """
    # Question 1 : le visiteur est-il connecté ?
    if not request.user.is_authenticated:
        # Non -> on l'envoie se connecter.
        # get_full_path() = l'adresse demandée, pour y REVENIR après connexion
        # (elle sera ajoutée dans l'adresse : ?next=/catalogue/auteurs/)
        return redirect_to_login(request.get_full_path())

    # Question 2 : son rôle fait-il partie des rôles autorisés ?
    if request.user.role not in roles_autorises:
        # Non -> interdit. "raise" = on lève l'erreur, Django répond 403
        # et affiche notre page templates/403.html.
        raise PermissionDenied

    # Les deux contrôles sont passés : None = "aucun refus"
    return None


# ======================================================================
# 2. LE VIGILE DES PAGES « FONCTIONS » : le décorateur @role_requis
# ======================================================================
# Utilisation :
#     @role_requis("ADMIN")
#     def liste_utilisateurs(request): ...
#
# Python transforme ce @ en :
#     liste_utilisateurs = role_requis("ADMIN")(liste_utilisateurs)
# => la page est REMPLACÉE par une version protégée.
#
# 3 fonctions emboîtées, car 3 informations arrivent à 3 moments différents :
#   niveau 1 : les rôles autorisés   -> quand Python lit "@role_requis(...)"
#   niveau 2 : la page à protéger    -> au démarrage du site
#   niveau 3 : la requête du visiteur -> à CHAQUE visite
def role_requis(*roles_autorises):
    # NIVEAU 1 : reçoit les rôles.
    # *roles_autorises (avec une étoile) = accepte 1 ou plusieurs rôles :
    #   @role_requis("ADMIN")  ou  @role_requis("ADMIN", "BIBLIOTHECAIRE")

    def decorateur(vue):
        # NIVEAU 2 : reçoit la page à protéger (ex. liste_utilisateurs)

        @wraps(vue)  # la version protégée garde le nom de la vraie page
        def vue_protegee(request, *args, **kwargs):
            # NIVEAU 3 : appelé à CHAQUE visite.
            # *args, **kwargs = "tous les autres paramètres" (ex. le pk de
            # /auteurs/3/), qu'on transmet tels quels à la vraie page.

            # On demande le contrôle commun
            refus = verifier_role(request, roles_autorises)

            # S'il y a un refus (une redirection vers la connexion), on le renvoie.
            # (le cas 403 n'arrive jamais ici : PermissionDenied a déjà été levée)
            if refus is not None:
                return refus

            # Aucun refus : on ouvre la VRAIE page
            return vue(request, *args, **kwargs)

        # Le niveau 2 renvoie la version protégée (qui remplace la page)
        return vue_protegee

    # Le niveau 1 renvoie le décorateur (qui va recevoir la page)
    return decorateur


# ======================================================================
# 3. LE VIGILE DES PAGES « CLASSES » : le mixin RoleRequisMixin
# ======================================================================
# Utilisation :
#     class AuteurCreation(RoleRequisMixin, CreateView):
#         roles_autorises = ("ADMIN", "BIBLIOTHECAIRE")
#
# Un MIXIN = une petite classe qu'on AJOUTE à une autre pour lui donner
# un comportement en plus (comme une option "antivol" sur une voiture).
#
# ⚠️ Le mixin doit être À GAUCHE dans la liste : Python cherche les méthodes
# de gauche à droite, donc le vigile passe AVANT le formulaire de CreateView.
class RoleRequisMixin:

    # Valeur par défaut : aucun rôle autorisé.
    # Chaque page la REMPLACE par ses propres rôles.
    # (si une page oublie de la remplacer -> personne n'entre : c'est sûr)
    roles_autorises = ()

    def dispatch(self, request, *args, **kwargs):
        # dispatch() = la PORTE D'ENTRÉE d'une vue classe.
        # Django l'appelle EN PREMIER à chaque visite, avant d'afficher
        # le formulaire (GET) ou de l'enregistrer (POST).
        # -> c'est l'endroit idéal pour poster le vigile.

        # Le même contrôle que le décorateur.
        # self.roles_autorises = les rôles indiqués par la page elle-même.
        refus = verifier_role(request, self.roles_autorises)

        # Refus (pas connecté) -> on renvoie la redirection
        if refus is not None:
            return refus

        # Aucun refus -> super().dispatch() = "continue normalement" :
        # on passe la main au dispatch de CreateView / ListView / ...
        # qui affiche ou enregistre le formulaire.
        return super().dispatch(request, *args, **kwargs)