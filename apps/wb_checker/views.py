from django.shortcuts import render
from django.urls import reverse
from .forms import WBProductForm
from django.http import HttpResponseRedirect, HttpResponse
import apps.wb_checker.backend_explorer as backend_explorer
import time
from functools import wraps

def time_count(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(end - start)
        return result
    return wrapper

action_type_dict = {'product': backend_explorer.check_repetitions_product, 
             'brand': backend_explorer.check_repetitions_brand, 
             'seller': backend_explorer.check_repetitions_seller,
}



def all_price_list(request):
    form = WBProductForm()
    if request.method == 'POST':
        form = WBProductForm(request.POST)
        if form.is_valid():
            author_id = 2 #пока не знаю, как точно передавать author_id в функцию, но это как-то через аунтефикацию надо делать (пока эмулирую)
            #проверяем поле action_type, чтобы понять какую функцию юзать (можно как альтернативу сделать regex's по урлу, но пока проще так)
            action_type=request.POST['action_type']
            action_type_dict[action_type](request.POST['url'], author_id)

            #если бренд, то прежде всего проверяем, сколько всего товаров в total на api (если total > 1000, то пока выдаем ошибку (но будем выдавать варианты (все, первая 100, кастомное значение)))
            #если все ок, то:
            #идем в общую базу, вытаскиваем товары этого бренда, если они есть
            #парсим товары и преобразуем их в удобный словарь (во время парсинга смотрим на повторюшки, и, если повторюшка, то меняем поле authors у уже созданной повторюшки, если нет, то добавляем новый товар + цена итд)
            #если добавляем новый товар, но продавца такого нет, то нужно создать продавца

            #примерно то же самое с продавцом 
            return HttpResponseRedirect(reverse('all_price_list'))
    return render(request, 'index.html', context={'form': form})
