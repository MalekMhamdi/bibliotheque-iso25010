from rest_framework import generics

from api.serializers import LivreSerializer
from catalogue.models import Livre


class LivreListe(generics.ListAPIView):
    serializer_class = LivreSerializer
    queryset = Livre.objects.prefetch_related("auteurs")


class LivreDetail(generics.RetrieveAPIView):
    serializer_class = LivreSerializer
    queryset = Livre.objects.prefetch_related("auteurs")
