from django.urls import path
from .views import BookViewSet

urlpatterns = [
    path('', BookViewSet.as_view({'get': 'page'}), name='home'),
    path('books/<int:pk>/', BookViewSet.as_view({'get': 'detail_page'}), name='book-detail'),
]
