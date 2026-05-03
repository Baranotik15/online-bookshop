from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'book',
            'book_title',
            'quantity',
            'price'
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'user_email',
            'total_price',
            'status',
            'created_at',
            'items'
        ]
        read_only_fields = ['user', 'created_at']
