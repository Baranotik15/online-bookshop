from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.shortcuts import render, get_object_or_404

from .models import Book, Author
from .serializers import BookSerializer, BookShortSerializer, AuthorSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.select_related('author').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BookShortSerializer
        return BookSerializer

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def page(self, request):
        books = self.get_queryset()
        return render(request, 'books/list.html', {'books': books})

    @action(detail=True, methods=['get'])
    def detail_page(self, request, pk=None):
        book = get_object_or_404(self.get_queryset(), pk=pk)
        return render(request, 'books/detail.html', {'book': book})


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.prefetch_related('books').all()
    serializer_class = AuthorSerializer
