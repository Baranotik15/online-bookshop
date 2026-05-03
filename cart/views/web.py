import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

from cart.models import Cart
from orders.models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def cart(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    raw = list(cart_obj.items.select_related('book').all())
    items = [
        {'id': i.id, 'book': i.book, 'quantity': i.quantity, 'subtotal': i.book.price * i.quantity}
        for i in raw
    ]
    total = sum(i['subtotal'] for i in items)
    return render(request, 'cart/cart.html', {'items': items, 'total': total})


@login_required
def checkout(request):
    if request.method != 'POST':
        return redirect('/cart/')

    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    raw = list(cart_obj.items.select_related('book').all())

    if not raw:
        return redirect('/cart/')

    total = sum(i.book.price * i.quantity for i in raw)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'uah',
                    'product_data': {'name': i.book.title},
                    'unit_amount': int(i.book.price * 100),
                },
                'quantity': i.quantity,
            }
            for i in raw
        ],
        mode='payment',
        success_url=request.build_absolute_uri('/orders/success/?session_id={CHECKOUT_SESSION_ID}'),
        cancel_url=request.build_absolute_uri('/cart/'),
    )

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total_price=total,
            stripe_session_id=session.id,
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, book=i.book, quantity=i.quantity, price=i.book.price)
            for i in raw
        ])
        cart_obj.items.all().delete()

    return redirect(session.url, code=303)
