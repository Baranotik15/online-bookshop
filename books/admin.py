from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from proj.admin_mixins import SuperuserEditMixin
from .models import Genre, Author, Book


@admin.register(Genre)
class GenreAdmin(SuperuserEditMixin, ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Author)
class AuthorAdmin(SuperuserEditMixin, ModelAdmin):
    list_display = ['last_name', 'first_name', 'birth_date', 'death_date', 'book_count']
    search_fields = ['first_name', 'last_name']
    list_filter = ['birth_date']
    fieldsets = (
        ('Ім\'я', {'fields': (('first_name', 'last_name'),)}),
        ('Дати', {'fields': (('birth_date', 'death_date'),)}),
    )

    @display(description='Книг', ordering='books__count')
    def book_count(self, obj):
        return obj.books.count()


@admin.register(Book)
class BookAdmin(SuperuserEditMixin, ModelAdmin):
    list_display = ['title', 'author', 'price', 'stock', 'display_genres', 'created_at']
    list_filter = ['genres', 'author']
    search_fields = ['title', 'author__first_name', 'author__last_name']
    autocomplete_fields = ['author']
    filter_horizontal = ['genres']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основне', {'fields': ('title', 'author', 'genres')}),
        ('Деталі', {'fields': ('description', ('price', 'stock'), 'image')}),
        ('Дати', {'classes': ('collapse',), 'fields': (('created_at', 'updated_at'),)}),
    )

    @display(description='Жанри')
    def display_genres(self, obj):
        return ', '.join(obj.genres.values_list('name', flat=True))
