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
from .tasks import send_mail_support_form, add_tg_user
from apps.core import bot
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apps.accounts.models import TelegramUser
from apps.core.utils import check_tg_code, check_tg_connection
from django.utils import timezone


def index(request):
    posts = Post.objects.all()
    return render(request, 'core/index.html', context={'posts':posts})



def contacts(request):
    if request.method == 'POST':
        send_mail_support_form.delay(request.POST['name'], request.POST['email'], request.POST['message'])
        messages.success(request, message='Успех!')
        return render(request, 'core/partials/support_form.html')
    return render(request, 'core/contacts.html')


class MenuView(LoginRequiredMixin, View):
    def get(self, request):
        prods_snippet = request.user.product_set.filter(enabled=True)[:3]
        prods_wb_snippet = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product')[:3]
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
                                                          'prods_wb_snippet': prods_wb_snippet,
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
    

@csrf_exempt
def bot_webhook(request):
    print('📩 Получен запрос', timezone.now())
    if request.method == 'POST':
        try:
            raw_body = request.body.decode('utf-8')
            print("📦 raw_body:", raw_body)
            data = json.loads(raw_body)
        except Exception as e:
            print("❌ Ошибка при разборе JSON:", str(e))
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        print("✅ Parsed JSON:", data)

        message = data.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        username = message.get('from', {}).get('username')
        first_name = message.get('from', {}).get('first_name')

        print(f"🧾 message: {text} от @{username}")
        if text == '/start':
            print(f"User @{username} ({chat_id}) нажал /start")
            add_tg_user.delay(chat_id, username, first_name)
            bot.send_first_telegram_message(chat_id)
        elif text == '🔔 Вставить код':
                bot.send_message_to_paste_code(chat_id)
        elif text == '💬 Поддержка':
            bot.send_support_message(chat_id)
        elif text == '52':
            bot.send_52_message(chat_id)
        elif text.isdigit() and len(text) == 6:
            if check_tg_code(text, chat_id):
                bot.send_success_of_pasting_code(chat_id)
            else:
                bot.send_unsuccess_of_pasting_code(chat_id)
        else:
            bot.send_unknown_message(chat_id)
        return JsonResponse({'ok': True})

