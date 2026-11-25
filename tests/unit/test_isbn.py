"""Tests UNITAIRES de la validation de l'ISBN (RM-05).

RM-05 : un ISBN est composé d'exactement 13 chiffres.

Techniques utilisées (fiche n°2) :
  - classes d'équivalence : 1 classe valide, plusieurs classes invalides ;
  - valeurs limites : 12 / 13 / 14 chiffres (la frontière est 13).

Test UNITAIRE : on teste une seule fonction, isolée.
-> pas de base de données (pas de @pytest.mark.django_db), pas de serveur.
"""

import pytest
from django.core.exceptions import ValidationError

from catalogue.validators import valider_isbn


# ----------------------------------------------------------------------
# Classe VALIDE : exactement 13 chiffres -> aucune erreur
# ----------------------------------------------------------------------
def test_isbn_de_13_chiffres_est_accepte():
    # Si la fonction lève une erreur, le test échoue automatiquement.
    # Ici, on attend qu'il ne se passe RIEN : l'ISBN est accepté.
    valider_isbn("9782070612758")


# ----------------------------------------------------------------------
# Classes INVALIDES -> une ValidationError doit être levée
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "isbn_invalide",
    [
        "978207061275",  # 12 chiffres -> valeur limite - 1
        "97820706127580",  # 14 chiffres -> valeur limite + 1
        "978207061275X",  # 13 caractères mais une LETTRE
        "978-2070612758",  # contient un TIRET
        "",  # VIDE
        "٩٧٨٢٠٧٠٦١٢٧٥٨",  # 13 chiffres ARABES-INDIENS (pas 0-9)
    ],
)
def test_isbn_invalide_est_refuse(isbn_invalide):
    # pytest.raises : le test réussit SEULEMENT si l'erreur se produit.
    with pytest.raises(ValidationError):
        valider_isbn(isbn_invalide)
