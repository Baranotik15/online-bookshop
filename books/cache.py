import json

from django.core.cache import cache
from rest_framework.renderers import JSONRenderer

CACHE_TIMEOUT = 60 * 5


def _serialize(serializer_class, queryset, **kwargs):
    data = serializer_class(queryset, many=True, **kwargs).data
    return json.loads(JSONRenderer().render(data))


def get_cached_genres():
    cached = cache.get('genres_list')
    if cached is not None:
        return cached
    from books.models import Genre
    from books.serializers import GenreSerializer
    data = _serialize(GenreSerializer, Genre.objects.all())
    cache.set('genres_list', data, CACHE_TIMEOUT)
    return data


def invalidate_genres():
    cache.delete('genres_list')


def get_cached_authors():
    cached = cache.get('authors_list')
    if cached is not None:
        return cached
    from books.models import Author
    from books.serializers import AuthorSerializer
    data = _serialize(AuthorSerializer, Author.objects.prefetch_related('books').all())
    cache.set('authors_list', data, CACHE_TIMEOUT)
    return data


def invalidate_authors():
    cache.delete('authors_list')
