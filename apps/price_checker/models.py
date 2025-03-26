from django.db import models
from apps.blog.models import Author
from django.utils import timezone

class EnabledManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(enabled=True)

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
    name = models.CharField(max_length=100, verbose_name='Имя продукта')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин', null=True)
    latest_price = models.IntegerField(verbose_name='Последняя цена')
    url = models.URLField(verbose_name='URL')
    ref_url = models.URLField(verbose_name='Ref-URL')
    enabled = models.BooleanField(default=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='products', verbose_name='Никнейм автора')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления продукта')
    updated = models.DateTimeField(default=timezone.now, verbose_name='Время обновления продукта')
    objects = models.Manager()
    enabled_products = EnabledManager()
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-updated']
        indexes = [
            models.Index(fields=['shop', 'author']),
            ]
    
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
        indexes = [
            models.Index(fields=['product'])
        ]


class WBSeller(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продавца WB')
    wb_id = models.CharField(max_length=100, verbose_name='ID продавца WB') 
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')
    catalog_count = models.IntegerField(verbose_name='Всего товаров в каталоге продавца')

    class Meta:
        verbose_name = 'Продавец WB'
        verbose_name_plural = 'Продавцы WB'
        indexes = [
            models.Index(fields=['name']),
            ]

    def __str__(self):
        return self.name
    

class WBBrand(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя бренда WB')
    wb_id = models.CharField(max_length=100, verbose_name='ID бренда WB') 
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')
    catalog_count = models.IntegerField(verbose_name='Всего товаров в каталоге бренда')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        indexes = [
            models.Index(fields=['name']),
            ]

    def __str__(self):
        return self.name
    


class WBProduct(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта WB')
    artikul = models.CharField(max_length=100, verbose_name='Артикул продукта WB')
    latest_price = models.IntegerField(verbose_name='Последняя цена')
    wb_cosh = models.BooleanField(default=True)
    # shop_name = models.ForeignKey(max_length=100, verbose_name='Продавец продукта WB') - будет в другой таблице
    seller = models.ForeignKey(WBSeller, on_delete=models.CASCADE, verbose_name='Продавец продукта WB')
    # brand_name = models.CharField(max_length=100, verbose_name='Бренд продукта WB') - будет в другой таблице
    brand = models.ForeignKey(WBBrand, on_delete = models.CASCADE, verbose_name='Бренд продукта WB')
    url = models.URLField(verbose_name='URL')
    enabled = models.BooleanField(default=True)
    authors = models.ManyToManyField(Author, verbose_name='Никнеймы авторов')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления продукта WB')
    updated = models.DateTimeField(default=timezone.now, verbose_name='Время обновления продукта WB')
    objects = models.Manager()
    enabled_products = EnabledManager()
    class Meta:
        verbose_name = 'Продукт WB'
        verbose_name_plural = 'Продукты WB'
        ordering = ['-updated']
        # indexes = [
        #     models.Index(fields=['authors']),
        #     ]
    
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



class WBPrice(models.Model):
    price = models.IntegerField(verbose_name='Цена продукта WB')
    added_time = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    product = models.ForeignKey(WBProduct, on_delete=models.CASCADE, verbose_name='Продукт WB')

    class Meta:
        ordering = ['added_time']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        indexes = [
            models.Index(fields=['product'])
        ]