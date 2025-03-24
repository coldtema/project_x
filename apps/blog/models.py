from django.db import models
from django.contrib.auth.models import User


class Author(models.Model):
    class Subscription(models.TextChoices):
        GOLD = 'GOLD', 'Golden Status'
        SILVER = 'SILVER', 'Silver Status'
        BRONZE = 'BRONZE', 'Bronze Status'
        FREE = 'FREE', 'Free Status'
    nickname = models.CharField(max_length=20, verbose_name='Никнейм')
    age = models.IntegerField(default=0, verbose_name='Возраст')
    subscription = models.CharField(max_length=100, default=Subscription.FREE, choices=Subscription.choices)

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['nickname']

    def __str__(self):
        return self.nickname

class Post(models.Model):
    title = models.CharField(blank=True, null=False, unique=False, help_text='Введите название поста', verbose_name='Название поста', max_length=120)
    slug = models.SlugField(max_length=80, unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Краткое описание')
    text = models.TextField(blank=False, unique=False, help_text='Введите текст поста', verbose_name='Полный текст поста')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    updated = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    fixed = models.BooleanField(blank=False, default=False, verbose_name='Прикреплено')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts', null=True)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        abstract = False
        proxy = False

    def __str__(self):
        return f'{self.text[:20]}...'
    
    # def __repr__(self):
    #     return f'{self.text[:20]}...'



# class Category(models.Model):
#     name = models.CharField(max_length=50, verbose_name='Категории')
#     slug = models.SlugField(unique=True, help_text='Слаг - это часть URL-адреса ресурса')

# class Classroom(models.Model):
#     name = models.CharField(max_length=50)
#     code = models.CharField(unique=True, max_length=11)
#     text = models.TextField(blank=True, default='')
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.name


