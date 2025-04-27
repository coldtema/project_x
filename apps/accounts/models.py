from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    class Subscription(models.TextChoices):
        GOLD = 'GOLD', 'Golden Status'
        SILVER = 'SILVER', 'Silver Status'
        BRONZE = 'BRONZE', 'Bronze Status'
        FREE = 'FREE', 'Free Status'
    email = models.EmailField(unique=True)
    subscription = models.CharField(max_length=6, default=Subscription.FREE, choices=Subscription.choices)
    slots = models.IntegerField(default=1000)
    dest_name = models.CharField(max_length=1000, default="Москва")
    dest_id = models.CharField(max_length=100, default="-1257786")

    def __str__(self):
        return self.username