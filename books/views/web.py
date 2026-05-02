from django.shortcuts import render

from books.models import Book


def book_list(request):
    books = Book.objects.select_related('author').all()
    return render(request, 'books/list.html', {'books': books})
