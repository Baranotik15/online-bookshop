from django.shortcuts import render

from books.models import Book, Author, Genre


def book_list(request):
    books = Book.objects.select_related('author').prefetch_related('genres').all()
    authors = Author.objects.order_by('last_name', 'first_name')
    genres = Genre.objects.all()
    return render(request, 'books/list.html', {'books': books, 'authors': authors, 'genres': genres})
