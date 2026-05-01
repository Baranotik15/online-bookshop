from django.db import models


class Orders(models.Model):
    user_id = models.IntegerField()
    total_price = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"Order {self.id} - User {self.user_id}"
    

class OrderItem(models.Model):
    order_id = models.ForeignKey(Orders, on_delete=models.CASCADE)
    book_id = models.IntegerField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"OrderItem {self.id} - Order {self.order_id.id} - Book {self.book_id}"
