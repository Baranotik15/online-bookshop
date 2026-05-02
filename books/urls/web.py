from django.urls import path

from books.views.web import book_list, book_detail

urlpatterns = [
    path('', book_list, name='book-list'),
    path('books/<int:pk>/', book_detail, name='book-detail'),
]
