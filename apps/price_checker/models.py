from django.db import models
from apps.accounts.models import CustomUser
from django.utils import timezone

class SecureManager(models.Manager):
    def secure_get(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except:
            return None




class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя тега')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        indexes = [
            models.Index(fields=['name']),
            ]

    def __str__(self):
        return self.name




class Shop(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя магазина')
    regex_name = models.CharField(max_length=100, verbose_name='Имя из url')
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')
    tags = models.ManyToManyField(Tag)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        indexes = [
            models.Index(fields=['name']),
            ]

    def __str__(self):
        return self.name




class Product(models.Model):
    name = models.CharField(max_length=150, verbose_name='Имя продукта')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин', null=True)
    latest_price = models.IntegerField(verbose_name='Последняя цена')
    first_price = models.IntegerField(verbose_name='Первая цена')
    last_notified_price = models.IntegerField(verbose_name='Цена уведомления пользователя', null=True)
    url = models.URLField(verbose_name='URL')
    ref_url = models.URLField(verbose_name='Ref-URL')
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления продукта')
    updated = models.DateTimeField(default=timezone.now, verbose_name='Время обновления продукта')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Подписчики продукта') #по идее - foreign key
    repeated = models.BooleanField(default=False)

    objects = SecureManager()

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-updated']
        indexes = [
            models.Index(fields=['shop']),
            models.Index(fields=['url'])
            ]
    
    def __str__(self):
        return self.name
    
    # def save(self, *args, **kwargs):
    #     if self.pk:  # Проверяем, что объект уже существует (не новый)
    #         original = Product.objects.get(pk=self.pk)
    #         if self.latest_price != original.latest_price:  # Проверяем, изменилось ли нужное поле
    #             self.updated = timezone.now()  # Обновляем вручную
    #         else:
    #             self.updated = original.updated
    #     super().save(*args, **kwargs)
    



class Price(models.Model):
    price = models.IntegerField(verbose_name='Цена')
    added_time = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Имя продукта')

    class Meta:
        ordering = ['-added_time']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        indexes = [
            models.Index(fields=['product'])
        ]
