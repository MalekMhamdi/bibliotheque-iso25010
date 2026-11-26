"""Recherche de livres (EF-08), partagée par la page web et par l'API."""

from django.db.models import Q

from catalogue.models import Livre


def rechercher_livres(q=""):
    """Titre, auteur, catégorie (contient) ; ISBN (exact). Sans doublon."""
    livres = Livre.objects.prefetch_related("auteurs")
    q = (q or "").strip()
    if q:
        livres = livres.filter(
            Q(titre__icontains=q)
            | Q(auteurs__nom__icontains=q)
            | Q(isbn=q)
            | Q(categorie__icontains=q)
        ).distinct()  # un livre à 2 auteurs ne doit apparaître qu'une fois
    return livres
