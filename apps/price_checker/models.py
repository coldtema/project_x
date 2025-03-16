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



# class DeletedProduct(models.Model):
#     name = models.CharField(max_length=100, verbose_name='Имя удаленного продукта')
#     shop = models.CharField(max_length=100, blank=True, verbose_name='Магазин удаленного продукта')
#     category = models.CharField(max_length=100, verbose_name='Категория удаленного продукта', blank=True)
#     latest_price = models.IntegerField(verbose_name='Последняя цена удаленного продукта')
#     url = models.URLField(verbose_name='URL удаленного продукта')
#     image = models.URLField(null=True, verbose_name='Картинка удаленного продукта')
#     author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='deletedproducts', verbose_name='Никнейм автора удаленного продукта')
#     class Meta:
#         verbose_name = 'Удаленный продукт'
#         verbose_name_plural = 'Удаленные продукты'
#         ordering = ['-id']
    
#     def __str__(self):
#         return self.name
    

# class DeletedPrice(models.Model):
#     price = models.IntegerField(verbose_name='Цена удаленного продукта')
#     added_time = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен удаленный продукт')
#     product = models.ForeignKey(DeletedProduct, on_delete=models.CASCADE, verbose_name='Имя удаленного продукта')

#     class Meta:
#         ordering = ['added_time']
#         verbose_name = 'Цена удаленного продукта'
#         verbose_name_plural = 'Цены удаленного продукта'

