"""Validateurs du catalogue : règles sur le FORMAT des données.

Ces fonctions sont PURES : elles n'utilisent ni la base de données
ni une requête HTTP -> elles se testent en tests unitaires.
"""

import re

from django.core.exceptions import ValidationError

# RM-05 : exactement 13 chiffres de 0 à 9, et rien d'autre.
#   [0-9] = un chiffre de 0 à 9 UNIQUEMENT
#           (on n'utilise pas \d, qui accepte aussi d'autres chiffres,
#            par exemple les chiffres arabes-indiens ٠١٢٣٤٥٦٧٨٩)
#   {13}  = exactement 13 fois
FORMAT_ISBN = re.compile(r"[0-9]{13}")


def valider_isbn(valeur: str) -> None:
    """Vérifie qu'un ISBN respecte RM-05 (exactement 13 chiffres de 0 à 9).

    Ne renvoie rien si l'ISBN est valide.
    Lève une ValidationError sinon.
    """
    # fullmatch = la valeur ENTIÈRE doit correspondre au format
    # (pas seulement un morceau : "12345678901234" serait refusé)
    if not FORMAT_ISBN.fullmatch(valeur):
        raise ValidationError(
            "L'ISBN doit contenir exactement 13 chiffres (sans tiret ni espace).",
            code="isbn_invalide",
        )