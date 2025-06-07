from django.db import models
from apps.accounts.models import CustomUser
from django.utils import timezone

class EnabledManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(enabled=True)
    

class WBMenuCategory(models.Model):
    name = models.CharField(max_length=1000, verbose_name='Имя категории WB')
    shard_key = models.CharField(null=True, max_length=1000, verbose_name='Ключ шардирования категории WB')
    wb_id =  models.IntegerField(unique=True, verbose_name='WB ID категории WB')
    query = models.CharField(null=True, max_length=1000, verbose_name='Строка запроса к api')
    main_url = models.URLField(null=True, verbose_name='URL категории')
    subs = models.ManyToManyField(CustomUser, verbose_name='Подписчики категории')
    parent = models.IntegerField(null=True, verbose_name='ID родительской категории')
    ru_path = models.CharField(max_length=1000, null=True, verbose_name='RU путь с родительскими категориями')

    class Meta:
        verbose_name = 'Категория меню WB'
        verbose_name_plural = 'Категории меню WB'
        indexes = [
            models.Index(fields=['wb_id']),
            ]

    def __str__(self):
        return self.name

    

class WBSeller(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продавца WB')
    wb_id = models.IntegerField(unique=True, verbose_name='ID продавца WB') 
    main_url = models.URLField(blank=True, verbose_name='URL главной страницы')
    subs = models.ManyToManyField(CustomUser, verbose_name='Подпичсики селлера')

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
    subs = models.ManyToManyField(CustomUser, verbose_name='Подписчики бренда')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        indexes = [
            models.Index(fields=['wb_id']),
            ]

    def __str__(self):
        return self.name

    


class WBProduct(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя продукта WB')
    artikul = models.IntegerField(unique=True, verbose_name='Артикул продукта WB')
    wb_cosh = models.BooleanField(default=True)
    seller = models.ForeignKey(WBSeller, on_delete=models.CASCADE, verbose_name='Продавец продукта WB')
    brand = models.ForeignKey(WBBrand, on_delete = models.CASCADE, verbose_name='Бренд продукта WB')
    url = models.URLField(verbose_name='URL')
    image_url = models.URLField(verbose_name='Ссылка на картинку')

    class Meta:
        verbose_name = 'Продукт WB'
        verbose_name_plural = 'Продукты WB'
        # ordering = ['-updated']
        indexes = [
            models.Index(fields=['artikul']),
            ]
    
    def __str__(self):
        return self.name



class WBDetailedInfo(models.Model):
    product = models.ForeignKey(WBProduct, on_delete=models.CASCADE, verbose_name='Продукт WB')
    latest_price = models.IntegerField(verbose_name='Цена продукта WB')
    first_price = models.IntegerField(verbose_name='Первая цена продукта WB')
    last_notified_price = models.IntegerField(verbose_name='Цена уведомления пользователя', null=True)
    size = models.CharField(max_length=20, null=True, verbose_name='Размер')
    volume = models.IntegerField(verbose_name='Количество')
    enabled = models.BooleanField(default=True, verbose_name='Есть в наличии')
    updated = models.DateTimeField(default=timezone.now, verbose_name='Время обновления продукта')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Автор продукта')
    

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информация о продуктах'
        ordering = ['-updated']
        indexes = [
            models.Index(fields=['product', 'author'])
        ]
        constraints = [
            models.UniqueConstraint(fields=['product', 'latest_price', 'first_price', 'size', 'volume', 'enabled', 'updated', 'author'], name='total_repetition')
        ]
    # def save(self, *args, **kwargs):
    #     if self.pk:  # Проверяем, что объект уже существует (не новый)
    #         original = WBProduct.objects.get(pk=self.pk)
    #         if self.latest_price != original.latest_price:  # Проверяем, изменилось ли нужное поле
    #             self.updated = timezone.now()  # Обновляем вручную
    #         else:
    #             self.updated = original.updated
        # super().save(*args, **kwargs)

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



class TopWBProduct(models.Model):
    class Source(models.TextChoices):
        BRAND = 'BRAND', ' Бренд'
        SELLER = 'SELLER', 'Продавец'
        CATEGORY = 'CATEGORY', 'Категория'
    name = models.CharField(max_length=100, verbose_name='Имя продукта WB')
    artikul = models.IntegerField(verbose_name='Артикул продукта WB')
    score = models.FloatField(verbose_name='Внутренний рейтинг топ продукта WB')
    wb_cosh = models.BooleanField(default=True)
    latest_price = models.IntegerField(verbose_name='Цена топ продукта WB')
    true_discount = models.IntegerField(verbose_name='Честная скидка топ продукта WB')
    rating = models.FloatField(verbose_name='Рейтинг')
    feedbacks = models.IntegerField(verbose_name='Отзывы')
    seller = models.ForeignKey(WBSeller, on_delete=models.CASCADE, verbose_name='Продавец продукта WB')
    brand = models.ForeignKey(WBBrand, on_delete = models.CASCADE, verbose_name='Бренд продукта WB')
    menu_category = models.ForeignKey(WBMenuCategory, on_delete=models.CASCADE, verbose_name='Категория продукта WB', null=True)
    url = models.URLField(verbose_name='URL')
    image_url = models.URLField(verbose_name='URL картинки товара')
    created = models.DateField(verbose_name='Время добавления топ продукта WB')
    source = models.CharField(max_length=8, choices=Source.choices)

    class Meta:
        verbose_name = 'Топ продукт WB'
        verbose_name_plural = 'Топ продукты WB'
        ordering = ['artikul']
        indexes = [
            models.Index(fields=['artikul'])]
    
    def __str__(self):
        return str(self.artikul)
    


