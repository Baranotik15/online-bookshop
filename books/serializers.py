from rest_framework import serializers
from datetime import date
from .models import Book, Author


class BookShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'price']


class AuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    books = BookShortSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'birth_date',
            'death_date',
            'age',
            'books'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        if not obj.birth_date:
            return None

        end_date = obj.death_date or date.today()
        return end_date.year - obj.birth_date.year


class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        source='author',
        write_only=True
    )
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'description',
            'price',
            'author',
            'author_id',
            'author_name',
            'stock',
            'image',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"
