from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)\
            .select_related('user')\
            .prefetch_related('items__book')
