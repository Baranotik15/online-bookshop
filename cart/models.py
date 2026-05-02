from django.db import models
from users.models import Users
from books.models import Book


class Cart(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.book} x {self.quantity}"
