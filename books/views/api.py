from rest_framework.viewsets import ModelViewSet

from books.models import Book, Author
from books.serializers import BookSerializer, BookShortSerializer, AuthorSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.select_related('author').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BookShortSerializer
        return BookSerializer


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.prefetch_related('books').all()
    serializer_class = AuthorSerializer
