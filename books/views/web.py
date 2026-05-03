from django.shortcuts import render

from books.models import Book, Author


def book_list(request):
    books = Book.objects.select_related('author').prefetch_related('genres').all()
    authors = Author.objects.order_by('last_name', 'first_name')
    return render(request, 'books/list.html', {'books': books, 'authors': authors})
