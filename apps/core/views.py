from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.price_checker.models import Product
from apps.accounts.models import CustomUser
from datetime import date
from django.core.mail import send_mail
import os
from django.contrib import messages


def index(request):
    post = {'title':'first post', 
            'date': date(year=2002, month=9, day=25),
            'summary': 'text of post',
            'image_url': 'http://avatars.mds.yandex.net/get-vthumb/2044023/a3932f1604e45342599fd8f71f767935/800x450',
            'image': '1'}
    post1 = {'title':'first post', 
            'date': date(year=2002, month=9, day=25),
            'summary': 'text of post',
            'image_url': 'https://basket-12.wbbasket.ru/vol1679/part167964/167964984/images/c516x688/1.webp',
            'image': '1'}
    post2 = {'title':'first post', 
            'date': date(year=2002, month=9, day=25),
            'summary': 'text of post',
            'image_url': 'https://basket-12.wbbasket.ru/vol1679/part167964/167964984/images/c516x688/1.webp',}
    return render(request, 'core/index.html', context={'posts':[post, post1, post2]})


# @login_required
# def menu(request):
#     return render(request, 'core/menu.html')


def contacts(request):
    if request.method == 'POST':
        send_mail(subject='from support form', 
                  message=f'''От: {request.POST['name']}
Email: {request.POST['email']}
Текст обращения: {request.POST['message']}''',
                  from_email=os.getenv('EMAIL_HOST_USER'),
                  recipient_list=[os.getenv('EMAIL_HOST_USER')],
                  fail_silently=True)
        messages.success(request, message='Успех!')
        return render(request, 'core/partials/support_form.html')
    return render(request, 'core/contacts.html')


class MenuView(LoginRequiredMixin, View):
    def get(self, request):
        prods_snippet = request.user.product_set.filter(enabled=True)[:5]
        brands = request.user.wbbrand_set.all().prefetch_related('topwbproduct_set')
        sellers = request.user.wbseller_set.all().prefetch_related('topwbproduct_set')
        menu_categories = request.user.wbmenucategory_set.all().prefetch_related('topwbproduct_set')
        raw_prods_brands = list(map(lambda x: x.topwbproduct_set.all(), brands))
        raw_prods_sellers = list(map(lambda x: x.topwbproduct_set.all(), sellers))
        raw_prods_menu_categories = list(map(lambda x: x.topwbproduct_set.all(), menu_categories))
        raw_prods_brands.extend(raw_prods_sellers)
        raw_prods_brands.extend(raw_prods_menu_categories)
        prods = []
        for prod in raw_prods_brands:
            prods.extend(prod)
        prods = sorted(prods, key=lambda x: x.true_discount, reverse=True)
        recs_snippet = sorted(prods, key=lambda x: x.true_discount)[-5:]
        return render(request, 'core/menu.html', context={'prods_snippet': prods_snippet,
                                                          'recs_snippet': recs_snippet})
    

def faq(request):
    return render(request, 'core/faq.html')