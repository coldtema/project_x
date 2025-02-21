from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse('<h2>Главная</h2>')


def about(request, name = '??', age='??'):
    return HttpResponse(f'''<h2>О сайте</h2>
                        <h2>name: {name}</h2>
                        <h2>age: {age}</h2>
                        ''')


def contacts(request):
    return HttpResponse('<h2>Контакты</h2>')