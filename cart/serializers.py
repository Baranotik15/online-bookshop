from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    book_title = serializers.StringRelatedField(source='book')

    class Meta:
        model = CartItem
        fields = ['id', 'book', 'book_title', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'created_at']

    def get_total_price(self, obj):
        total = 0
        for item in obj.items.all():
            total += item.book.price * item.quantity
        return total
