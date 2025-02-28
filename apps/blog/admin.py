from django.contrib import admin
from .models import Post, Author

admin.site.register(Post) #site - это объект представляющий собой административный сайт в django
admin.site.register(Author)
