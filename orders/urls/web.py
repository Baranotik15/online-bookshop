from django.urls import path
from orders.views.web import order_success, stripe_webhook

urlpatterns = [
    path('orders/success/', order_success, name='order-success'),
    path('orders/webhook/', stripe_webhook, name='stripe-webhook'),
]
