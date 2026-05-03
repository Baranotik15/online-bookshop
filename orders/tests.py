import pytest
from decimal import Decimal
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status

from books.models import Author, Book
from users.models import User
from .models import Order, OrderItem


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email='test@example.com', username='testuser', password='pass1234')


@pytest.fixture
def other_user():
    return User.objects.create_user(email='other@example.com', username='otheruser', password='pass1234')


@pytest.fixture
def book():
    author = Author.objects.create(first_name='Автор', last_name='Тест')
    return Book.objects.create(title='Книга', price=Decimal('100.00'), stock=10, author=author)


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user)
    return client


@pytest.fixture
def order(user):
    return Order.objects.create(user=user, total_price=Decimal('100.00'), status='pending', stripe_session_id='sess_test_abc')


# --- Auth ---

@pytest.mark.django_db
def test_list_orders_requires_auth(client):
    r = client.get('/api/orders/')
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize('method', ['get', 'post'])
def test_orders_endpoints_require_auth(client, method):
    r = getattr(client, method)('/api/orders/', {}, format='json')
    assert r.status_code == status.HTTP_403_FORBIDDEN


# --- List ---

@pytest.mark.django_db
def test_list_only_own_orders(auth_client, user, other_user):
    Order.objects.create(user=user, total_price=Decimal('100.00'), status='pending')
    Order.objects.create(user=other_user, total_price=Decimal('200.00'), status='pending')

    r = auth_client.get('/api/orders/')
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 1
    assert r.data[0]['user_email'] == user.email


# --- Create ---

@pytest.mark.django_db
def test_create_order(auth_client):
    payload = {'total_price': '200.00', 'status': 'pending'}
    r = auth_client.post('/api/orders/', payload, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    assert Order.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize('order_status', ['pending', 'paid', 'shipped', 'cancelled'])
def test_create_order_with_various_statuses(auth_client, order_status):
    payload = {'total_price': '100.00', 'status': order_status}
    r = auth_client.post('/api/orders/', payload, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data['status'] == order_status


# --- Detail ---

@pytest.mark.django_db
def test_order_detail(auth_client, order, book):
    OrderItem.objects.create(order=order, book=book, quantity=1, price=book.price)
    r = auth_client.get(f'/api/orders/{order.id}/')
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data['items']) == 1


@pytest.mark.django_db
def test_cannot_view_other_users_order(auth_client, other_user):
    other_order = Order.objects.create(user=other_user, total_price=Decimal('100.00'), status='pending')
    r = auth_client.get(f'/api/orders/{other_order.id}/')
    assert r.status_code == status.HTTP_404_NOT_FOUND


# --- Update ---

@pytest.mark.django_db
def test_update_order_status(auth_client, order):
    r = auth_client.patch(f'/api/orders/{order.id}/', {'status': 'cancelled'}, format='json')
    assert r.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.status == 'cancelled'


# --- Delete ---

@pytest.mark.django_db
def test_delete_order(auth_client, order):
    r = auth_client.delete(f'/api/orders/{order.id}/')
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert not Order.objects.filter(id=order.id).exists()


@pytest.mark.django_db
def test_order_items_cascade_delete(order, book):
    item = OrderItem.objects.create(order=order, book=book, quantity=1, price=book.price)
    order.delete()
    assert not OrderItem.objects.filter(id=item.id).exists()


# --- Web views ---

@pytest.mark.django_db
def test_order_success_page_requires_login():
    from django.test import Client
    r = Client().get('/orders/success/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_order_success_renders(user, order):
    from django.test import Client
    c = Client()
    c.force_login(user)
    r = c.get(f'/orders/success/?session_id={order.stripe_session_id}')
    assert r.status_code == 200


@pytest.mark.django_db
def test_stripe_webhook_invalid_signature():
    from django.test import Client
    r = Client().post('/orders/webhook/', b'{}', content_type='application/json')
    assert r.status_code == 400


@pytest.mark.django_db
def test_stripe_webhook_payment_completed(order):
    from django.test import Client
    event = {'type': 'checkout.session.completed', 'data': {'object': {'id': order.stripe_session_id}}}
    with patch('orders.views.web.stripe.Webhook.construct_event', return_value=event):
        r = Client().post('/orders/webhook/', b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='t=1,v1=abc')
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.status == 'paid'


@pytest.mark.django_db
def test_stripe_webhook_other_event_ignored(order):
    from django.test import Client
    event = {'type': 'payment_intent.created', 'data': {'object': {}}}
    with patch('orders.views.web.stripe.Webhook.construct_event', return_value=event):
        r = Client().post('/orders/webhook/', b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='t=1,v1=abc')
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.status == 'pending'
