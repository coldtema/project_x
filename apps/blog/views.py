from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound, HttpResponseBadRequest
from .models import Author, Post
from .forms import UserForm, UserEditForm

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
    
def reg_edit(request, id):
    if request.method == 'POST':
        form_to_validate = UserEditForm(request.POST)
        if form_to_validate.is_valid():
            object_to_edit = Author.objects.get(id=request.POST.get('id'))
            object_to_edit.nickname, object_to_edit.age=request.POST.get('nickname'), request.POST.get('age')
            object_to_edit.save()
            return HttpResponseRedirect('/blog/reg')
    else:
        object_to_edit = Author.objects.get(id=id)
        object_form = UserEditForm(initial={'age': object_to_edit.age, 'nickname': object_to_edit.nickname, 'id':object_to_edit.id}) #при создании формы initial уже не может измениться
        # object_form.age.initial=object_to_edit.age
        return render(request, 'blog/reg_edit.html', context={'object_to_edit': object_to_edit, 'object_form': object_form})

def reg_delete(request, id):
    Author.objects.get(id=id).delete()
    return HttpResponseRedirect('/blog/reg')

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