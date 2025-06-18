from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from datetime import date
from django.core.mail import send_mail
import os
from django.contrib import messages
from apps.core.models import Notification
from django.http import HttpResponse
from .models import Post


def index(request):
    posts = Post.objects.all()
    return render(request, 'core/index.html', context={'posts':posts})



def contacts(request):
    if request.method == 'POST':
        send_mail(subject='from support form', 
                  message=f'''От: {request.POST['name']}
Email: {request.POST['email']}
Текст обращения: {request.POST['message']}''',
                  from_email=os.getenv('EMAIL_HOST_USER'),
                  recipient_list=[os.getenv('EMAIL_HEAVY')],
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
        prods_dict = dict()
        for prod in prods:
            prods_dict.update({prod.artikul:prod})
        prods = prods_dict.values()
        prods = sorted(prods, key=lambda x: x.true_discount, reverse=True)
        recs_snippet = sorted(prods, key=lambda x: x.true_discount)[-5:]
        wb_notifications = sorted(Notification.objects.filter(user=request.user, wb_product__isnull=False).select_related('wb_product'), key=lambda x: x.time, reverse=True)

        return render(request, 'core/menu.html', context={'prods_snippet': prods_snippet,
                                                          'recs_snippet': recs_snippet,
                                                          'wb_notifications': wb_notifications})
    

def faq(request):
    return render(request, 'core/faq.html')


def guide(request):
    return render(request, 'core/guide.html')

@login_required
def delete_notification(request, id):
    notif_to_delete = Notification.objects.filter(pk=id).select_related('user').first()
    if request.user.pk == notif_to_delete.user.pk:
        notif_to_delete.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=413)

@login_required
def notifications_swap(request):
    if request.GET['type-toggle'] == 'shops':
        shops_notifications = sorted(Notification.objects.filter(user=request.user, product__isnull=False).select_related('product'), key=lambda x: x.time, reverse=True)
        return render(request, 'core/partials/shops_notifications.html', context={'shops_notifications': shops_notifications})
    if request.GET['type-toggle'] == 'WB':
        wb_notifications = sorted(Notification.objects.filter(user=request.user, wb_product__isnull=False).select_related('wb_product'), key=lambda x: x.time, reverse=True)
        return render(request, 'core/partials/shops_notifications.html', context={'wb_notifications': wb_notifications})
