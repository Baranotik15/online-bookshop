import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order


@login_required
def order_success(request):
    session_id = request.GET.get('session_id', '')
    order = Order.objects.filter(
        stripe_session_id=session_id, user=request.user
    ).prefetch_related('items__book').first()
    return render(request, 'orders/success.html', {'order': order})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        Order.objects.filter(stripe_session_id=session['id']).update(status='paid')

    return HttpResponse(status=200)
