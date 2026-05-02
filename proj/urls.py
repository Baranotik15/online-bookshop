from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web
    path('', include('books.urls.web')),

    # API
    path('api/', include('books.urls.api')),
    path('api/', include('orders.urls.api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
