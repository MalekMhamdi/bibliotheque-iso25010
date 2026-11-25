"""Vues du catalogue : CRUD des auteurs (EF-04) et des livres (EF-03).

On utilise les VUES GÉNÉRIQUES de Django (des classes toutes faites) :
    ListView   -> afficher une liste        (R = Read)
    CreateView -> formulaire d'ajout        (C = Create)
    UpdateView -> formulaire de modification (U = Update)
    DeleteView -> confirmation + suppression (D = Delete)

Elles gèrent DÉJÀ : l'affichage, le formulaire, la validation,
l'enregistrement et la redirection (302) après succès.
On ajoute seulement : le modèle, les champs, la page HTML, et le VIGILE.
"""

# reverse_lazy : retrouve une adresse à partir de son NOM (défini dans urls.py)
from django.contrib import messages
from django.db.models import ProtectedError
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from catalogue.models import Auteur, Livre
from comptes.permissions import RoleRequisMixin  # le vigile des vues classes

# --- Qui a le droit de quoi (tableau des droits du cadrage) ------------
# Définis UNE fois, réutilisés par toutes les vues.
TOUS_LES_ROLES = ("ADMIN", "BIBLIOTHECAIRE", "ADHERENT")  # lire
GESTIONNAIRES = ("ADMIN", "BIBLIOTHECAIRE")  # créer, modifier, supprimer


# ======================================================================
# CRUD DES AUTEURS (EF-04)
# ======================================================================
# Champs modifiables d'un auteur dans le formulaire
CHAMPS_AUTEUR = ["nom", "nationalite"]


# R = READ : liste des auteurs
# ⚠️ RoleRequisMixin à GAUCHE : le vigile passe AVANT la vue
class AuteurListe(RoleRequisMixin, ListView):
    roles_autorises = TOUS_LES_ROLES  # tous les rôles connectés
    model = Auteur  # quelle table lire
    template_name = "catalogue/auteur_liste.html"  # quelle page HTML
    context_object_name = "auteurs"  # nom de la liste dans le HTML


# C = CREATE : ajouter un auteur
class AuteurCreation(RoleRequisMixin, CreateView):
    roles_autorises = GESTIONNAIRES
    model = Auteur
    fields = CHAMPS_AUTEUR  # seuls ces champs sont acceptés
    template_name = "catalogue/auteur_formulaire.html"
    success_url = reverse_lazy("auteur_liste")  # après succès -> 302 vers la liste


# U = UPDATE : modifier un auteur
class AuteurModification(RoleRequisMixin, UpdateView):
    roles_autorises = GESTIONNAIRES
    model = Auteur
    fields = CHAMPS_AUTEUR
    template_name = "catalogue/auteur_formulaire.html"  # même page que la création
    success_url = reverse_lazy("auteur_liste")


# D = DELETE : supprimer un auteur
class AuteurSuppression(RoleRequisMixin, DeleteView):
    roles_autorises = GESTIONNAIRES
    model = Auteur
    template_name = "catalogue/auteur_suppression.html"  # page de confirmation
    success_url = reverse_lazy("auteur_liste")


# ======================================================================
# CRUD DES LIVRES (EF-03) : même principe que les auteurs
# ======================================================================
# Champs du formulaire d'un livre.
# "auteurs" est la relation N-N : Django la transforme AUTOMATIQUEMENT
# en liste à choix multiple (on peut sélectionner plusieurs auteurs).
CHAMPS_LIVRE = ["titre", "isbn", "auteurs", "annee", "categorie", "nb_exemplaires"]

# 💡 Aucune ligne de code ici pour ces 3 règles : Django les applique
#    TOUT SEUL, car elles sont déclarées dans le MODÈLE (étape 5.3) :
#    - format ISBN (RM-05)  -> validators=[valider_isbn] dans le modèle
#    - ISBN unique (RM-05)  -> unique=True : le formulaire vérifie AVANT
#                              d'enregistrer et affiche un message
#                              (au lieu d'une IntegrityError = erreur 500)
#    - au moins un auteur   -> ManyToManyField sans blank=True
#    => les règles écrites dans le modèle s'appliquent PARTOUT.


# R = READ : liste des livres
class LivreListe(RoleRequisMixin, ListView):
    roles_autorises = TOUS_LES_ROLES
    model = Livre
    template_name = "catalogue/livre_liste.html"
    context_object_name = "livres"

    # PAGINATION : 20 livres par page.
    # Il y aura 10 000 livres à l'étape 7 : tout afficher d'un coup
    # serait lent et illisible (performance EQ-02, facilité d'utilisation EQ-04).
    paginate_by = 20

    def get_queryset(self):
        """Quels livres afficher, et comment les charger.

        prefetch_related("auteurs") : charge les auteurs de TOUS les livres
        de la page en UNE seule requête supplémentaire.
          sans : 1 requête pour les livres + 1 par livre pour ses auteurs
                 = 21 requêtes pour 20 livres
          avec : 2 requêtes seulement   -> plus rapide (EQ-02)
        """
        return Livre.objects.prefetch_related("auteurs")


# C = CREATE : ajouter un livre
class LivreCreation(RoleRequisMixin, CreateView):
    roles_autorises = GESTIONNAIRES
    model = Livre
    fields = CHAMPS_LIVRE
    template_name = "catalogue/livre_formulaire.html"
    success_url = reverse_lazy("livre_liste")


# U = UPDATE : modifier un livre
class LivreModification(RoleRequisMixin, UpdateView):
    roles_autorises = GESTIONNAIRES
    model = Livre
    fields = CHAMPS_LIVRE
    template_name = "catalogue/livre_formulaire.html"  # même page que la création
    success_url = reverse_lazy("livre_liste")


# D = DELETE : supprimer un livre
# (ses auteurs ne sont PAS supprimés : seul le LIEN livre <-> auteur
#  disparaît de la table de liaison ; Goscinny reste en base)
class LivreSuppression(RoleRequisMixin, DeleteView):
    roles_autorises = GESTIONNAIRES
    model = Livre
    template_name = "catalogue/livre_suppression.html"
    success_url = reverse_lazy("livre_liste")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, "Ce livre a des prêts : suppression impossible.")
            return self.render_to_response(self.get_context_data())
