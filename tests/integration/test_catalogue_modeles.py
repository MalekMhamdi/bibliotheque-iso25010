"""Tests des modèles du catalogue : Auteur et Livre.

Règles vérifiées (cadrage, sections 2 et 5) :
  1. Livre <-> Auteur est une relation N-N ;
  2. RM-05 : l'ISBN est unique (contrainte en base) ;
  3. RM-05 : l'ISBN a 13 chiffres (le modèle utilise le validateur) ;
  4. un livre a au moins 1 exemplaire.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from catalogue.models import Auteur, Livre

ISBN_VALIDE = "9782070612758"
AUTRE_ISBN_VALIDE = "9782070612765"


# ----------------------------------------------------------------------
# Règle 1 : relation N-N entre Livre et Auteur
# ----------------------------------------------------------------------
@pytest.mark.django_db
def test_relation_n_n_entre_livres_et_auteurs():
    # Préparer : 2 auteurs et 2 livres
    hugo = Auteur.objects.create(nom="Victor Hugo")
    dumas = Auteur.objects.create(nom="Alexandre Dumas")
    livre1 = Livre.objects.create(titre="Livre écrit à deux", isbn=ISBN_VALIDE)
    livre2 = Livre.objects.create(titre="Autre livre de Hugo", isbn=AUTRE_ISBN_VALIDE)

    # Agir : livre1 a DEUX auteurs, et Hugo a écrit DEUX livres
    livre1.auteurs.add(hugo, dumas)
    livre2.auteurs.add(hugo)

    # Vérifier : on navigue dans les DEUX sens de la relation
    assert livre1.auteurs.count() == 2      # un livre -> plusieurs auteurs
    assert hugo.livres.count() == 2         # un auteur -> plusieurs livres


# ----------------------------------------------------------------------
# Règle 2 : RM-05, ISBN unique (refusé par la BASE elle-même)
# ----------------------------------------------------------------------
@pytest.mark.django_db
def test_isbn_unique_rm05():
    Livre.objects.create(titre="Premier", isbn=ISBN_VALIDE)
    with pytest.raises(IntegrityError):
        Livre.objects.create(titre="Doublon", isbn=ISBN_VALIDE)


# ----------------------------------------------------------------------
# Règle 3 : RM-05, le modèle utilise le validateur de format
# ----------------------------------------------------------------------
@pytest.mark.django_db
def test_modele_refuse_un_isbn_mal_forme():
    livre = Livre(titre="ISBN avec tiret", isbn="978-2070612758")
    # full_clean() = lance TOUTES les validations du modèle
    # (c'est ce que fait un formulaire Django avant d'enregistrer)
    with pytest.raises(ValidationError) as erreur:
        livre.full_clean()
    # On vérifie que l'erreur concerne bien le champ "isbn"
    assert "isbn" in erreur.value.message_dict


# ----------------------------------------------------------------------
# Règle 4 : au moins 1 exemplaire (valeur limite : 0 refusé)
# ----------------------------------------------------------------------
@pytest.mark.django_db
def test_au_moins_un_exemplaire():
    livre = Livre(titre="Sans exemplaire", isbn=ISBN_VALIDE, nb_exemplaires=0)
    with pytest.raises(ValidationError) as erreur:
        livre.full_clean()
    assert "nb_exemplaires" in erreur.value.message_dict