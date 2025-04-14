from django.db import models
from apps.blog.models import Author
from django.utils import timezone

class EnabledManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(enabled=True)

    

class WBSeller(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продавца WB')
    wb_id = models.IntegerField(unique=True, verbose_name='ID продавца WB') 
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
    wb_id = models.IntegerField(unique=True, verbose_name='ID бренда WB') 
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
    

# class WBPromotion(models.Model):
#     name = models.CharField(max_length=100, verbose_name='Имя промоакции WB')
#     wb_id = models.IntegerField(unique=True, verbose_name='ID промоации WB') 
#     main_url = models.URLField(blank=True, verbose_name='URL страницы промоакции')
#     shard_key = models.CharField(max_length=200, verbose_name='Часть url для достука к api промоакции WB')
#     query = models.CharField(max_length=200, verbose_name='Параметр для передачи в api промоакции WB')

#     class Meta:
#         verbose_name = 'Промоакция'
#         verbose_name_plural = 'Промоакции'
#         indexes = [
#             models.Index(fields=['wb_id']),
#             ]

#     def __str__(self):
#         return self.name
    


class WBProduct(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта WB')
    artikul = models.IntegerField(unique=True, verbose_name='Артикул продукта WB')
    wb_cosh = models.BooleanField(default=True)
    seller = models.ForeignKey(WBSeller, on_delete=models.CASCADE, verbose_name='Продавец продукта WB')
    brand = models.ForeignKey(WBBrand, on_delete = models.CASCADE, verbose_name='Бренд продукта WB')
    url = models.URLField(verbose_name='URL')

    class Meta:
        verbose_name = 'Продукт WB'
        verbose_name_plural = 'Продукты WB'
        # ordering = ['-updated']
        indexes = [
            models.Index(fields=['artikul']),
            ]
    
    def __str__(self):
        return self.name
    

    # def save(self, *args, **kwargs):
    #     if self.pk:  # Проверяем, что объект уже существует (не новый)
    #         original = WBProduct.objects.get(pk=self.pk)
    #         if self.latest_price != original.latest_price:  # Проверяем, изменилось ли нужное поле
    #             self.updated = timezone.now()  # Обновляем вручную
    #         else:
    #             self.updated = original.updated
    #     super().save(*args, **kwargs)



class WBDetailedInfo(models.Model):
    product = models.ForeignKey(WBProduct, on_delete=models.CASCADE, verbose_name='Продукт WB')
    latest_price = models.IntegerField(verbose_name='Цена продукта WB')
    size = models.CharField(max_length=20, null=True, verbose_name='Размер')
    volume = models.IntegerField(verbose_name='Количество')
    enabled = models.BooleanField(default=True, verbose_name='Есть в наличии')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Автор продукта')
    
    enabled_products = EnabledManager()
    objects = models.Manager()

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информация о продуктах'
        indexes = [
            models.Index(fields=['product', 'author'])
        ]
        constraints = [
            models.UniqueConstraint(fields=['product', 'latest_price', 'size', 'volume', 'enabled', 'author'], name='total_repetition')
        ]

    def __str__(self):
        return str((self.product, self.latest_price, self.size, self.volume, self.enabled, self.author))


class WBPrice(models.Model):
    price = models.IntegerField(verbose_name='Цена продукта WB')
    added_time = models.DateTimeField(verbose_name='Добавлено')
    detailed_info = models.ForeignKey(WBDetailedInfo, on_delete=models.CASCADE, verbose_name='Продукт WB')

    class Meta:
        ordering = ['added_time']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        indexes = [
            models.Index(fields=['detailed_info'])
        ]

    def __str__(self):
        return str(self.detailed_info_id)
    


class WBCategory(models.Model):
    wb_id = models.CharField(max_length=100, verbose_name='ID категории WB') 
    url = models.URLField(blank=True, verbose_name='URL категории')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        indexes = [
            models.Index(fields=['wb_id']),
            ]
        


class WBPreset(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя пресета')
    main_url = models.URLField(verbose_name='URL пресета')
    max_elems=models.IntegerField(default=0, verbose_name='Количество продуктов, добавленных из пресета')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Никнеймы авторов')
    products = models.ManyToManyField(WBProduct, verbose_name='Продукты пресета')



class TopWBProduct(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта WB')
    artikul = models.IntegerField(unique=True, verbose_name='Артикул продукта WB')
    score = models.FloatField(verbose_name='Внутренний рейтинг топ продукта WB')
    wb_cosh = models.BooleanField(default=True)
    latest_price = models.IntegerField(verbose_name='Цена топ продукта WB')
    rating = models.FloatField(verbose_name='Рейтинг')
    feedbacks = models.IntegerField(verbose_name='Отзывы')
    seller = models.ForeignKey(WBSeller, on_delete=models.CASCADE, verbose_name='Продавец продукта WB')
    brand = models.ForeignKey(WBBrand, on_delete = models.CASCADE, verbose_name='Бренд продукта WB')
    url = models.URLField(verbose_name='URL')

    class Meta:
        verbose_name = 'Топ продукт WB'
        verbose_name_plural = 'Топ продукты WB'
        # ordering = ['-updated']
        indexes = [
            models.Index(fields=['artikul']),
            ]
    
    def __str__(self):
        return self.name