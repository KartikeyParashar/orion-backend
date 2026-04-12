from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sale
from .serializers import SaleSerializer

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'subcategory', 'item', 'store', 'week', 'season']
