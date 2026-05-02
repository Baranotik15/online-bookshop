from django.urls import path
from cart.views.web import cart, checkout

urlpatterns = [
    path('cart/', cart, name='cart'),
    path('cart/checkout/', checkout, name='cart-checkout'),
]
