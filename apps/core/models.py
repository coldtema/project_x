from django.db import models
from apps.accounts.models import CustomUser
from apps.wb_checker.models import WBDetailedInfo
from apps.price_checker.models import Product

class Notification(models.Model):
    text = models.CharField(max_length=512, verbose_name='Текст уведомления')
    tg_text = models.CharField(max_length=512, verbose_name='Текст телеграм-уведомления', default='')
    time = models.DateTimeField(auto_now_add = True, verbose_name='Время уведомления')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, verbose_name='Обычный продукт')
    wb_product = models.ForeignKey(WBDetailedInfo, on_delete=models.CASCADE, null=True, verbose_name='WB продукт')
    additional_link = models.URLField(null = True, verbose_name='Доп. ссылка')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, verbose_name='Пользователь')



class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста')
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    date = models.DateField(auto_now_add = True, verbose_name='Дата поста')

