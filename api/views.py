from rest_framework import generics

from api.serializers import LivreSerializer
from catalogue.models import Livre
from catalogue.recherche import rechercher_livres


class LivreListe(generics.ListAPIView):
    serializer_class = LivreSerializer

    def get_queryset(self):
        return rechercher_livres(self.request.query_params.get("q", ""))


class LivreDetail(generics.RetrieveAPIView):
    serializer_class = LivreSerializer
    queryset = Livre.objects.prefetch_related("auteurs")
