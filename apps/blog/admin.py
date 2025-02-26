from django.contrib import admin
from .models import Post

admin.site.register(Post) #site - это объект представляющий собой административный сайт в django
