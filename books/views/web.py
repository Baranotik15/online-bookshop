from django.shortcuts import render, get_object_or_404

from books.models import Book


def book_list(request):
    books = Book.objects.select_related('author').all()
    return render(request, 'books/list.html', {'books': books})


def book_detail(request, pk):
    book = get_object_or_404(Book.objects.select_related('author'), pk=pk)
    return render(request, 'books/detail.html', {'book': book})
