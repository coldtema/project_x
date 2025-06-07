from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    class Subscription(models.TextChoices):
        ULTIMA = 'ULTIMA', 'Ultima Status'
        PLATINUM = 'PLATINUM', 'Platinum Status'
        FREE = 'FREE', 'Free Status'
    email = models.EmailField(unique=True)
    subscription = models.CharField(max_length=8, default=Subscription.FREE, choices=Subscription.choices)
    slots = models.IntegerField(default=10)
    dest_name = models.CharField(max_length=1000, default="Москва")
    dest_id = models.CharField(max_length=100, default="-1257786")
    discount_balance = models.IntegerField(default=0)
    notification_discount_price = models.IntegerField(default=100, verbose_name='Скидка для уведомления (руб)')
    notification_discount = models.IntegerField(default=10, verbose_name='Скидка для уведомления (%)')

    def __str__(self):
        return self.username