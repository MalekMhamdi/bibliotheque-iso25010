"""Vues du catalogue : CRUD des auteurs (EF-04).

On utilise les vues génériques de Django, qui gèrent déjà
l'affichage, le formulaire, la validation et la redirection (302).
On ajoute seulement : le modèle, les champs, la page HTML, et le VIGILE.
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from catalogue.models import Auteur
from comptes.permissions import RoleRequisMixin

# Les rôles autorisés, définis UNE fois (tableau des droits du cadrage)
TOUS_LES_ROLES = ("ADMIN", "BIBLIOTHECAIRE", "ADHERENT")
GESTIONNAIRES = ("ADMIN", "BIBLIOTHECAIRE")

# Les champs modifiables d'un auteur dans le formulaire
CHAMPS_AUTEUR = ["nom", "nationalite"]


# R = READ : liste des auteurs (tous les rôles connectés)
class AuteurListe(RoleRequisMixin, ListView):
    roles_autorises = TOUS_LES_ROLES
    model = Auteur
    template_name = "catalogue/auteur_liste.html"
    context_object_name = "auteurs"     # nom de la liste dans la page HTML


# C = CREATE : ajouter un auteur (gestionnaires uniquement)
class AuteurCreation(RoleRequisMixin, CreateView):
    roles_autorises = GESTIONNAIRES
    model = Auteur
    fields = CHAMPS_AUTEUR
    template_name = "catalogue/auteur_formulaire.html"
    success_url = reverse_lazy("auteur_liste")   # après succès -> 302 vers la liste
# reverse_lazy :retrouve l'adresse par son nom

# U = UPDATE : modifier un auteur (gestionnaires uniquement)
class AuteurModification(RoleRequisMixin, UpdateView):
    roles_autorises = GESTIONNAIRES
    model = Auteur
    fields = CHAMPS_AUTEUR
    template_name = "catalogue/auteur_formulaire.html"   # même page que la création
    success_url = reverse_lazy("auteur_liste")


# D = DELETE : supprimer un auteur (gestionnaires uniquement)
class AuteurSuppression(RoleRequisMixin, DeleteView):
    roles_autorises = GESTIONNAIRES
    model = Auteur
    template_name = "catalogue/auteur_suppression.html"
    success_url = reverse_lazy("auteur_liste")