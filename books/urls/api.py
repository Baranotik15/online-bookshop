from rest_framework.routers import DefaultRouter

from books.views.api import BookViewSet, AuthorViewSet


class BookShopRouter(DefaultRouter):
    class APIRootView(DefaultRouter.APIRootView):
        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            response.data['docs'] = request.build_absolute_uri('/api/docs/')
            return response


router = BookShopRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'authors', AuthorViewSet, basename='author')

urlpatterns = router.urls
