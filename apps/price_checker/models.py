from django.db import models
from apps.blog.models import Author

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта')
    shop = models.CharField(max_length=100, blank=True, verbose_name='Магазин')
    category = models.CharField(max_length=100, verbose_name='Категория', blank=True)
    latest_price = models.IntegerField(verbose_name='Последняя цена')
    url = models.URLField(verbose_name='URL')
    image = models.URLField(null=True, verbose_name='Картинка')
    enabled = models.BooleanField(default=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='products', verbose_name='Никнейм автора')
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-id']
    
    def __str__(self):
        return self.name
    

class Price(models.Model):
    price = models.IntegerField(verbose_name='Цена')
    added_time = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Имя продукта')

    class Meta:
        ordering = ['added_time']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'