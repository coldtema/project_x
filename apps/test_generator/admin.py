from django.contrib import admin
from .models import Test, Question


#admin.site.register(Test)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['name', 'added', 'best_result']
    list_filter = ['name']
    search_fields = ['name', 'text']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'answer1', 'answer2', 'answer3', 'right_answer', 'test__name'] 
    list_filter = ['test__name']
    search_fields = ['name', 'text', 'test__name']
    ordering = ['-test__name']