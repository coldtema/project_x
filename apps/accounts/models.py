from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone



class TelegramUser(models.Model):
    username = models.CharField(max_length=256, null=True, blank=True)
    first_name = models.CharField(max_length=256, null=True, blank=True)
    tg_id = models.BigIntegerField()

    def __str__(self):
        return self.username



class CustomUser(AbstractUser):
    class Subscription(models.TextChoices):
        ULTIMA = 'ULTIMA', 'Ultima Status'
        PLATINUM = 'PLATINUM', 'Platinum Status'
        FREE = 'FREE', 'Free Status'
    email = models.EmailField(unique=True)
    subscription = models.CharField(max_length=8, default=Subscription.FREE, choices=Subscription.choices)
    sub_expire = models.DateField(null=True, blank=True)
    slots = models.IntegerField(default=20)
    prods = models.IntegerField(default=0, verbose_name='Количество продуктов')
    dest_name = models.CharField(max_length=1000, default="Москва")
    dest_id = models.CharField(max_length=100, default="-1257786")
    discount_balance = models.IntegerField(default=0)
    notification_discount_price = models.IntegerField(default=300, verbose_name='Скидка для уведомления (руб)')
    notification_discount = models.IntegerField(default=10, verbose_name='Скидка для уведомления (%)')
    pricedown_notification = models.BooleanField(default=True)
    priceup_notification = models.BooleanField(default=True)
    tg_user = models.OneToOneField(to=TelegramUser, on_delete=models.CASCADE, related_name='web_user', null=True, blank=True)
    tg_token = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.username



class SubRequest(models.Model):
    class Subscription(models.TextChoices):
        ULTIMA = 'ULTIMA', 'Ultima Status'
        PLATINUM = 'PLATINUM', 'Platinum Status'
        FREE = 'FREE', 'Free Status'

    class Status(models.TextChoices):
        FINISHED = 'FINISHED', 'FINISHED'
        ACCEPTED = 'ACCEPTED', 'ACCEPTED'
        SENT = 'SENT', 'SENT'
        PENDING = 'PENDING', 'PENDING'
        DECLINED = 'DECLINED', 'DECLINED'
    price = models.IntegerField()
    duration = models.CharField(max_length=8, default='1')
    sub_plan = models.CharField(max_length=8, default=Subscription.FREE, choices=Subscription.choices)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, default=Status.PENDING, choices=Status.choices)
    created = models.DateTimeField(default=timezone.now)

    