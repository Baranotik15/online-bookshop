from django.db import models
from users.models import Users
from books.models import Book


class Cart(models.Model):
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id}"


class CartItems(models.Model):
    cart_id = models.ForeignKey(Cart, on_delete=models.CASCADE)
    book_id = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cart_id},{self.book_id},{self.quantity}"
