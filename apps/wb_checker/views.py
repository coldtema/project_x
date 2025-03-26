from django.shortcuts import render
from django.urls import reverse
from .forms import WBProductForm
from django.http import HttpResponseRedirect, HttpResponse


def all_price_list(request):
    form = WBProductForm()
    if request.method == 'POST':
        form = WBProductForm(request.POST)
        if form.is_valid():
            #проверяем поле action_type, чтобы понять какую функцию юзать

            #если просто продукт:
            #проверка на дубликат (полная база)
            #если дубликат, то у продукта, который продублировался меняем поле authors (просто добавляем новую many-to-many связь)

            #если бренд, то прежде всего проверяем, сколько всего товаров в total на api (если total > 1000, то пока выдаем ошибку (но будем выдавать варианты (все, первая 100, кастомное значение)))
            #если все ок, то:
            #идем в общую базу, вытаскиваем товары этого бренда, если они есть
            #парсим товары и преобразуем их в удобный словарь (во время парсинга смотрим на повторюшки, и, если повторюшка, то меняем поле authors у уже созданной повторюшки, если нет, то добавляем новый товар + цена итд)
            #если добавляем новый товар, но продавца такого нет, то нужно создать продавца

            #примерно то же самое с продавцом 
            return HttpResponseRedirect(reverse('all_price_list'))
    return render(request, 'index.html', context={'form': form})
