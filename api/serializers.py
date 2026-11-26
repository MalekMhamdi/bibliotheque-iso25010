from rest_framework import serializers

from catalogue.models import Livre


class LivreSerializer(serializers.ModelSerializer):
    auteurs = serializers.StringRelatedField(many=True)

    class Meta:
        model = Livre
        fields = ["id", "titre", "isbn", "annee", "categorie", "nb_exemplaires", "auteurs"]
