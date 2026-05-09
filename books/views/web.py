from django.shortcuts import render

from books.models import Book
from books.cache import get_cached_authors


def book_list(request):
    books = Book.objects.select_related('author').prefetch_related('genres').all()
    authors = get_cached_authors()
    return render(request, 'books/list.html', {'books': books, 'authors': authors})
