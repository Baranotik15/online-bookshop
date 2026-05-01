from django.db import models


class Users(models.Model):
    username = models.CharField(max_length=200)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
