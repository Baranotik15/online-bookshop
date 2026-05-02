from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from books.views import BookViewSet
from orders.views import OrderViewSet
from cart.views import CartViewSet


router = DefaultRouter()

router.register(r'books', BookViewSet, basename='books')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    #WEB
    path('', include('books.web_urls')),
    #API
    path('admin/', admin.site.urls),
    path('api/', include('books.urls')),
    # path('api/', include('users.urls')),
    path('api/', include('orders.urls')),
    # path('api/', include('cart.urls')),
    path('api/', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
