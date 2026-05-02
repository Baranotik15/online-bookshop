from django.urls import path
from cart.views.api import CartAPIView

urlpatterns = [
    path('cart/', CartAPIView.as_view(), name='cart'),
]
