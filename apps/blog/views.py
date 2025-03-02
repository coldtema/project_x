from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound, HttpResponseBadRequest
from .models import Author, Post
from .forms import UserForm

user_list = [{'name': 'Дмитрий', 'experience': 9},
             {'name': 'Павел',   'experience': 5},
             {'name': 'Алексей', 'experience': 3},
             {'name': 'Иван',    'experience': 0},
             {'name': 'Денис',   'experience': 2},
             {'name': 'Игорь',   'experience': 7},
             {'name': 'Руслан',  'experience': 1},
             {'name': 'Евгений', 'experience': 4},
             {'name': 'Андрей',  'experience': 2},
             {'name': 'Николай', 'experience': 8}]



def index(request):
    return render(request, 'blog/index.html', context={'user_list': user_list, 'name': request.GET.get('name', 'stranger'), 'age': int(request.GET.get('age', 0)), 'say_hello_variants': ['lesgou', 'lesgetit']})


def accounts(request):
    data = Author.objects.all()
    return render(request, 'blog/accounts.html', context={'data': data})


def posts(request):
    data = Post.objects.all()
    return render(request, 'blog/posts.html', context={'data': data})


def reg(request):
    if request.method == 'POST':
        form_obj = UserForm(request.POST)
        if form_obj.is_valid():
            Author.objects.create(nickname=request.POST.get('nickname'), age=request.POST.get('age'))
            return HttpResponseRedirect('/blog/reg')
        else:
            return HttpResponse('Неправильно введены данные в форме')
    elif request.method == 'GET':
        user_form = UserForm()
        user_model = Author.objects.all()
        return render(request, 'blog/reg.html', context={'form': user_form, 'user_model': user_model})


def about(request):
    return render(request, 'blog/about.html')


# def contacts(request, phone_number):
#     return HttpResponse(f'<h2>Контакты: {phone_number}</h2>')


# def products_new(request):
#     return HttpResponse("<h1>Новые продукты</h1>")


# def products_top(request):
#     return HttpResponse("<h1>Топ продуктов</h1>")

# def products_def(request, id=None):
#     if id is None:
#         return render(request, 'blog/main_product.html')
#     return HttpResponse(f"<h1>Продукт {id}</h1>")

# def products_def_questions(request, id):
#     return HttpResponse(f"<h1>Вопросы о продукте {id}</h1>")

# def products_def_comments(request, id):
#     return HttpResponse(f"<h1>Комментарии о продукте {id}</h1>")




# def message(request, category, subcategory, theme, number):
#     return HttpResponsePermanentRedirect('blog')
#     return HttpResponse(f'''<ul>
# <li>Категория: {category}</li>
# <li>Подкатегория: {subcategory}</li>
# <li>Тема: {theme}</li>
# <li>Номер: {number}</li>
# </ul>
#  ''')