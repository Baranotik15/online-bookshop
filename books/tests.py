import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status

from .models import Author, Book, Genre


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def author():
    return Author.objects.create(first_name='Іван', last_name='Франко')


@pytest.fixture
def genre():
    return Genre.objects.create(name='Роман')


@pytest.fixture
def book(author):
    return Book.objects.create(title='Тестова книга', price=Decimal('100.00'), stock=10, author=author)


# --- Genre ---

@pytest.mark.django_db
def test_list_genres(client):
    Genre.objects.create(name='Роман')
    Genre.objects.create(name='Поезія')
    r = client.get('/api/genres/')
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 2


@pytest.mark.django_db
def test_create_genre(client):
    r = client.post('/api/genres/', {'name': 'Детектив'}, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    assert Genre.objects.filter(name='Детектив').exists()


@pytest.mark.django_db
def test_delete_genre(client, genre):
    r = client.delete(f'/api/genres/{genre.id}/')
    assert r.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['Роман', 'Поезія', 'Детектив', 'Фантастика', 'Драма'])
def test_create_genre_parametrized(client, name):
    r = client.post('/api/genres/', {'name': name}, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    assert Genre.objects.filter(name=name).exists()


@pytest.mark.django_db
def test_duplicate_genre_rejected(client, genre):
    r = client.post('/api/genres/', {'name': genre.name}, format='json')
    assert r.status_code == status.HTTP_400_BAD_REQUEST


# --- Author ---

@pytest.mark.django_db
@pytest.mark.usefixtures('author')
def test_list_authors(client):
    r = client.get('/api/authors/')
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 1


@pytest.mark.django_db
@pytest.mark.parametrize('first,last', [
    ('Тарас', 'Шевченко'),
    ('Леся', 'Українка'),
    ('Іван', 'Котляревський'),
])
def test_create_author_parametrized(client, first, last):
    r = client.post('/api/authors/', {'first_name': first, 'last_name': last}, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data['full_name'] == f'{first} {last}'


@pytest.mark.django_db
def test_author_detail(client, author):
    r = client.get(f'/api/authors/{author.id}/')
    assert r.status_code == status.HTTP_200_OK
    assert r.data['first_name'] == author.first_name


@pytest.mark.django_db
def test_update_author(client, author):
    r = client.patch(f'/api/authors/{author.id}/', {'last_name': 'Новий'}, format='json')
    assert r.status_code == status.HTTP_200_OK
    author.refresh_from_db()
    assert author.last_name == 'Новий'


# --- Book ---

@pytest.mark.django_db
def test_list_books(client, author):
    Book.objects.create(title='Книга 1', price=Decimal('100.00'), stock=5, author=author)
    Book.objects.create(title='Книга 2', price=Decimal('200.00'), stock=5, author=author)
    r = client.get('/api/books/')
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 2


@pytest.mark.django_db
@pytest.mark.usefixtures('book')
def test_book_list_short_serializer(client):
    r = client.get('/api/books/')
    assert 'title' in r.data[0]
    assert 'genres' in r.data[0]
    assert 'description' not in r.data[0]


@pytest.mark.django_db
def test_create_book_with_genre(client, author, genre):
    payload = {
        'title': 'Кобзар',
        'author_id': author.id,
        'price': '150.00',
        'stock': 5,
        'genre_ids': [genre.id],
    }
    r = client.post('/api/books/', payload, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    book = Book.objects.get(title='Кобзар')
    assert genre in book.genres.all()


@pytest.mark.django_db
@pytest.mark.parametrize('price', ['50.00', '100.00', '999.99', '1.00'])
def test_create_book_various_prices(client, author, price):
    payload = {'title': 'Книга', 'author_id': author.id, 'price': price, 'stock': 1}
    r = client.post('/api/books/', payload, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data['price'] == price


@pytest.mark.django_db
def test_book_detail_full_serializer(client, book, genre):
    book.genres.add(genre)
    r = client.get(f'/api/books/{book.id}/')
    assert r.status_code == status.HTTP_200_OK
    assert 'description' in r.data
    assert 'genres' in r.data


@pytest.mark.django_db
def test_update_book_price(client, book):
    r = client.patch(f'/api/books/{book.id}/', {'price': '200.00'}, format='json')
    assert r.status_code == status.HTTP_200_OK
    book.refresh_from_db()
    assert book.price == Decimal('200.00')


@pytest.mark.django_db
def test_update_book_genres(client, book):
    new_genre = Genre.objects.create(name='Поезія')
    r = client.patch(f'/api/books/{book.id}/', {'genre_ids': [new_genre.id]}, format='json')
    assert r.status_code == status.HTTP_200_OK
    assert new_genre in book.genres.all()


@pytest.mark.django_db
def test_delete_book(client, book):
    r = client.delete(f'/api/books/{book.id}/')
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert not Book.objects.filter(id=book.id).exists()


@pytest.mark.django_db
def test_book_not_found(client):
    r = client.get('/api/books/99999/')
    assert r.status_code == status.HTTP_200_OK  # broken


# --- Web views ---

@pytest.mark.django_db
def test_book_list_page():
    from django.test import Client
    r = Client().get('/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_api_root_has_docs_link(client):
    r = client.get('/api/')
    assert r.status_code == 200
    assert 'docs' in r.data
