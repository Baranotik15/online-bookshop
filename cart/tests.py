import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status

from books.models import Author, Book
from users.models import User
from orders.models import Order
from .models import Cart, CartItem


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


# --- Auth ---

@pytest.mark.django_db
def test_get_cart_requires_auth(client):
    r = client.get('/api/cart/')
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize('method,path,body', [
    ('get', '/api/cart/', None),
    ('post', '/api/cart/', {'book_id': 1, 'quantity': 1}),
    ('patch', '/api/cart/', {'item_id': 1, 'quantity': 2}),
    ('delete', '/api/cart/', {'item_id': 1}),
])
def test_cart_endpoints_require_auth(client, method, path, body):
    r = getattr(client, method)(path, body, format='json')
    assert r.status_code == status.HTTP_403_FORBIDDEN


# --- GET cart ---

@pytest.mark.django_db
def test_get_empty_cart(auth_client):
    r = auth_client.get('/api/cart/')
    assert r.status_code == status.HTTP_200_OK
    assert r.data['items'] == []
    assert r.data['total_price'] == 0


@pytest.mark.django_db
def test_get_cart_creates_if_not_exists(auth_client, user):
    assert not Cart.objects.filter(user=user).exists()
    auth_client.get('/api/cart/')
    assert Cart.objects.filter(user=user).exists()


# --- POST add item ---

@pytest.mark.django_db
def test_add_item_to_cart(auth_client, book):
    r = auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 2}, format='json')
    assert r.status_code == status.HTTP_200_OK
    assert r.data['total_items'] == 1  # 1 cart item row
    assert Decimal(r.data['total_price']) == Decimal('200.00')


@pytest.mark.django_db
@pytest.mark.parametrize('qty', [1, 2, 5, 10])
def test_add_item_various_quantities(auth_client, book, qty):
    r = auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': qty}, format='json')
    assert r.status_code == status.HTTP_200_OK
    assert r.data['total_items'] == 1  # 1 cart item row regardless of quantity
    assert Decimal(r.data['total_price']) == book.price * qty


@pytest.mark.django_db
def test_add_same_item_increments_quantity(auth_client, user, book):
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 1}, format='json')
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 2}, format='json')
    cart = Cart.objects.get(user=user)
    item = CartItem.objects.get(cart=cart, book=book)
    assert item.quantity == 3


# --- PATCH update quantity ---

@pytest.mark.django_db
def test_update_cart_item_quantity(auth_client, user, book):
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 1}, format='json')
    cart = Cart.objects.get(user=user)
    item = CartItem.objects.get(cart=cart, book=book)
    r = auth_client.patch('/api/cart/', {'item_id': item.id, 'quantity': 5}, format='json')
    assert r.status_code == status.HTTP_200_OK
    item.refresh_from_db()
    assert item.quantity == 5


@pytest.mark.django_db
def test_update_returns_subtotal_and_total(auth_client, user, book):
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 1}, format='json')
    cart = Cart.objects.get(user=user)
    item = CartItem.objects.get(cart=cart, book=book)
    r = auth_client.patch('/api/cart/', {'item_id': item.id, 'quantity': 3}, format='json')
    assert 'subtotal' in r.data
    assert 'total' in r.data
    assert Decimal(r.data['subtotal']) == Decimal('300.00')


# --- DELETE remove item ---

@pytest.mark.django_db
def test_remove_cart_item(auth_client, user, book):
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 2}, format='json')
    cart = Cart.objects.get(user=user)
    item = CartItem.objects.get(cart=cart, book=book)
    r = auth_client.delete('/api/cart/', {'item_id': item.id}, format='json')
    assert r.status_code == status.HTTP_200_OK
    assert not CartItem.objects.filter(id=item.id).exists()
    assert r.data['total_items'] == 0


# --- Isolation ---

@pytest.mark.django_db
def test_cart_isolated_between_users(auth_client, other_user):
    author = Author.objects.create(first_name='А', last_name='Б')
    book2 = Book.objects.create(title='Чужа книга', price=Decimal('50.00'), stock=5, author=author)
    cart = Cart.objects.create(user=other_user)
    CartItem.objects.create(cart=cart, book=book2, quantity=1)

    r = auth_client.get('/api/cart/')
    assert r.data['items'] == []


# --- Total price ---

@pytest.mark.django_db
def test_total_price_calculation(auth_client, book):
    author = Author.objects.create(first_name='Б', last_name='В')
    book2 = Book.objects.create(title='Друга книга', price=Decimal('50.00'), stock=5, author=author)
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 2}, format='json')
    auth_client.post('/api/cart/', {'book_id': book2.id, 'quantity': 3}, format='json')
    r = auth_client.get('/api/cart/')
    assert Decimal(r.data['total_price']) == Decimal('350.00')


# --- API error cases ---

@pytest.mark.django_db
def test_add_item_without_book_id(auth_client):
    r = auth_client.post('/api/cart/', {}, format='json')
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_patch_with_zero_quantity(auth_client, user, book):
    auth_client.post('/api/cart/', {'book_id': book.id, 'quantity': 1}, format='json')
    item = CartItem.objects.get(cart__user=user, book=book)
    r = auth_client.patch('/api/cart/', {'item_id': item.id, 'quantity': 0}, format='json')
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_patch_nonexistent_item(auth_client):
    r = auth_client.patch('/api/cart/', {'item_id': 99999, 'quantity': 1}, format='json')
    assert r.status_code == status.HTTP_404_NOT_FOUND


# --- Web views ---

@pytest.mark.django_db
def test_cart_page_requires_login():
    from django.test import Client
    r = Client().get('/cart/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_cart_page_renders(user):
    from django.test import Client
    c = Client()
    c.force_login(user)
    r = c.get('/cart/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_checkout_get_redirects_to_cart(user):
    from django.test import Client
    c = Client()
    c.force_login(user)
    r = c.get('/cart/checkout/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_checkout_empty_cart_redirects(user):
    from django.test import Client
    c = Client()
    c.force_login(user)
    r = c.post('/cart/checkout/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_checkout_creates_order_and_clears_cart(user, book):
    from django.test import Client
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, book=book, quantity=1)

    mock_session = MagicMock(id='sess_test_123', url='https://stripe.com/pay/test')
    c = Client()
    c.force_login(user)
    with patch('cart.views.web.stripe.checkout.Session.create', return_value=mock_session):
        r = c.post('/cart/checkout/')

    assert r.status_code == 302
    assert Order.objects.filter(user=user, stripe_session_id='sess_test_123').exists()
    assert not CartItem.objects.filter(cart=cart).exists()
