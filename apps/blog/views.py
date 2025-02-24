from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    print(request)
    return HttpResponse('<h2>Hello in app BLOG</h2>')


def accounts(request, user_name = 'NoName'):
    return HttpResponse(f'Имя аккаунта: {user_name}')



def about(request, name = '??', age='??'):
    print(request.GET)
    if name == '??' and age == '??':
        return HttpResponse(f'''<h2>О сайте</h2>
                    <h2>name: {request.GET.get('name', 'Не передал имени, амебус')}</h2>
                    <h2>age: {request.GET.get('age', 'Не передал возраста, 0 лет')}</h2>
                    ''')   # альтернативно -> request.GET['name'] - но будет выдавать ошибку, если не найдет нужный параметр
    return HttpResponse(f'''<h2>О сайте</h2>
                        <h2>name: {name}</h2>
                        <h2>age: {age}</h2>
                        ''')




def contacts(request, phone_number):
    return HttpResponse(f'<h2>Контакты: {phone_number}</h2>')






def products_new(request):
    return HttpResponse("<h1>Новые продукты</h1>")


def products_top(request):
    return HttpResponse("<h1>Топ продуктов</h1>")

def products_def(request, id=None):
    if id is None:
        return HttpResponse("<h1>Главная страница в продуктах блога</h1>")
    return HttpResponse(f"<h1>Продукт {id}</h1>")

def products_def_questions(request, id):
    return HttpResponse(f"<h1>Вопросы о продукте {id}</h1>")

def products_def_comments(request, id):
    return HttpResponse(f"<h1>Комментарии о продукте {id}</h1>")




def message(request, category, subcategory, theme, number):
    return HttpResponse(f'''<ul>
<li>Категория: {category}</li>
<li>Подкатегория: {subcategory}</li>
<li>Тема: {theme}</li>
<li>Номер: {number}</li>
</ul>
 ''')