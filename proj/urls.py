from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('admin/', admin.site.urls),

    # Web
    path('', include('books.urls.web')),
    path('', include('users.urls.web')),
    path('', include('cart.urls.web')),
    path('', include('orders.urls.web')),

    # API
    path('api/', include('books.urls.api')),
    path('api/', include('orders.urls.api')),
    path('api/', include('cart.urls.api')),

    # Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
