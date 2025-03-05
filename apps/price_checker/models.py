from django.db import models
from apps.blog.models import Author

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    old_price = models.IntegerField()
    url = models.URLField()
    image = models.URLField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='products')

