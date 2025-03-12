from django.contrib import admin
from .models import Post, Author

# admin.site.register(Post) site - это объект представляющий собой административный сайт в django

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title','slug', 'description', 'text', 'created', 'updated', 'fixed', 'author__nickname']
    list_filter = ['title', 'author__nickname', 'created', 'fixed']
    prepopulated_fields = {'slug': ('title', )}
    search_fields = ['title', 'author__nickname'] #обязательно указываем поле, по которому делаем серч
    ordering = ['-created']
    # raw_id_fields = ['author'] - круче встроенный



@admin.register(Author)
class PostAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'age']
    list_filter = ['nickname', 'age']
    search_fields = ['nickname']
    ordering = ['-age']
    # raw_id_fields = ['author'] - круче встроенный