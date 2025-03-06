from django.db import models
from apps.blog.models import Author

class Product(models.Model):
    name = models.CharField(max_length=100)
    latest_price = models.IntegerField()
    url = models.URLField()
    image = models.URLField(null=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='products')

class Price(models.Model):
    price = models.IntegerField()
    added_time = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price')

