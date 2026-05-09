from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from books.models import Book, Author, Genre
from books.serializers import BookSerializer, BookShortSerializer, AuthorSerializer, GenreSerializer
from books.cache import get_cached_authors, invalidate_authors, get_cached_genres, invalidate_genres


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
        return Response(get_cached_authors())

    def create(self, request, *args, **kwargs):
        invalidate_authors()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        invalidate_authors()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        invalidate_authors()
        return super().destroy(request, *args, **kwargs)


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def list(self, request, *args, **kwargs):
        return Response(get_cached_genres())

    def create(self, request, *args, **kwargs):
        invalidate_genres()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        invalidate_genres()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        invalidate_genres()
        return super().destroy(request, *args, **kwargs)
