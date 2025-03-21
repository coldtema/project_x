from django.db import models
from apps.blog.models import Author
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта')
    shop = models.CharField(max_length=100, blank=True, verbose_name='Магазин')
    category = models.CharField(max_length=100, verbose_name='Категория', blank=True)
    latest_price = models.IntegerField(verbose_name='Последняя цена')
    url = models.URLField(verbose_name='URL')
    enabled = models.BooleanField(default=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='products', verbose_name='Никнейм автора')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления продукта')
    updated = models.DateTimeField(default=timezone.now, verbose_name='Время обновления продукта')
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-updated']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.pk:  # Проверяем, что объект уже существует (не новый)
            original = Product.objects.get(pk=self.pk)
            if self.latest_price != original.latest_price:  # Проверяем, изменилось ли нужное поле
                self.updated = timezone.now()  # Обновляем вручную
            else:
                self.updated = original.updated
        super().save(*args, **kwargs)
    

class Price(models.Model):
    price = models.IntegerField(verbose_name='Цена')
    added_time = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Имя продукта')

    class Meta:
        ordering = ['added_time']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'


class Shop(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя магазина')
    regex_name = models.CharField(max_length=100, verbose_name='Имя из url')
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'