from django.core.cache import cache
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from books.models import Book, Author, Genre
from books.serializers import BookSerializer, BookShortSerializer, AuthorSerializer, GenreSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.select_related('author').prefetch_related('genres').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BookShortSerializer
        return BookSerializer


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.prefetch_related('books').all()
    serializer_class = AuthorSerializer

    def list(self, request, *args, **kwargs):
        cached = cache.get('authors_list')
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set('authors_list', response.data)
        return response

    def _invalidate(self):
        cache.delete('authors_list')

    def create(self, request, *args, **kwargs):
        self._invalidate()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._invalidate()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._invalidate()
        return super().destroy(request, *args, **kwargs)


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def list(self, request, *args, **kwargs):
        cached = cache.get('genres_list')
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set('genres_list', response.data)
        return response

    def _invalidate(self):
        cache.delete('genres_list')

    def create(self, request, *args, **kwargs):
        self._invalidate()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._invalidate()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._invalidate()
        return super().destroy(request, *args, **kwargs)
