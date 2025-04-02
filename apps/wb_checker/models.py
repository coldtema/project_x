from django.db import models
from apps.blog.models import Author
from django.utils import timezone

class EnabledManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(enabled=True)
    

class WBSeller(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продавца WB')
    wb_id = models.IntegerField(verbose_name='ID продавца WB') 
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')
    # catalog_count = models.IntegerField(verbose_name='Всего товаров в каталоге продавца')
    full_control = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Продавец WB'
        verbose_name_plural = 'Продавцы WB'
        indexes = [
            models.Index(fields=['wb_id']),
            ]

    def __str__(self):
        return self.name
    

class WBBrand(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя бренда WB')
    wb_id = models.IntegerField(verbose_name='ID бренда WB') 
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')
    # catalog_count = models.IntegerField(verbose_name='Всего товаров в каталоге бренда')
    full_control = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        indexes = [
            models.Index(fields=['wb_id']),
            ]

    def __str__(self):
        return self.name
    

class WBPromotion(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя промоакции WB')
    wb_id = models.IntegerField(verbose_name='ID промоации WB') 
    main_url = models.URLField(blank=True, verbose_name='URL страницы промоакции')
    shard_key = models.CharField(max_length=200, verbose_name='Часть url для достука к api промоакции WB')
    query = models.CharField(max_length=200, verbose_name='Параметр для передачи в api промоакции WB')

    class Meta:
        verbose_name = 'Промоакция'
        verbose_name_plural = 'Промоакции'
        indexes = [
            models.Index(fields=['wb_id']),
            ]

    def __str__(self):
        return self.name
    


class WBProduct(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта WB')
    artikul = models.IntegerField(unique=True, verbose_name='Артикул продукта WB')
    latest_price = models.IntegerField(verbose_name='Последняя цена')
    wb_cosh = models.BooleanField(default=True)
    seller = models.ForeignKey(WBSeller, on_delete=models.CASCADE, verbose_name='Продавец продукта WB')
    brand = models.ForeignKey(WBBrand, on_delete = models.CASCADE, verbose_name='Бренд продукта WB')
    url = models.URLField(verbose_name='URL')
    enabled = models.BooleanField(default=True)
    authors = models.ManyToManyField(Author, verbose_name='Никнеймы авторов')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления продукта WB')
    updated = models.DateTimeField(default=timezone.now, verbose_name='Время обновления продукта WB')
    promotion = models.ForeignKey(WBPromotion, on_delete = models.CASCADE, verbose_name='Промоакция продукта WB', null=True)

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
            original = WBProduct.objects.get(pk=self.pk)
            if self.latest_price != original.latest_price:  # Проверяем, изменилось ли нужное поле
                self.updated = timezone.now()  # Обновляем вручную
            else:
                self.updated = original.updated
        super().save(*args, **kwargs)



class WBPrice(models.Model):
    price = models.IntegerField(verbose_name='Цена продукта WB')
    added_time = models.DateTimeField(verbose_name='Добавлено')
    product = models.ForeignKey(WBProduct, on_delete=models.CASCADE, verbose_name='Продукт WB')

    class Meta:
        ordering = ['added_time']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        indexes = [
            models.Index(fields=['product'])
        ]

class WBCategory(models.Model):
    wb_id = models.CharField(max_length=100, verbose_name='ID категории WB') 
    url = models.URLField(blank=True, verbose_name='URL категории')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        indexes = [
            models.Index(fields=['wb_id']),
            ]
