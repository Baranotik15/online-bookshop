from django.urls import path

from books.views.web import book_list

urlpatterns = [
    path('', book_list, name='book-list'),
]
