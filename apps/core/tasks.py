from celery import shared_task
from apps.core.utils import NotificationsClearer
from apps.accounts.models import CustomUser, SubRequest
from django.db.models import F, IntegerField, ExpressionWrapper
from django.db.models.aggregates import Sum
from dateutil.relativedelta import relativedelta
from datetime import date
from django.core.mail import send_mail
import os
from django.conf import settings
from apps.accounts.models import TelegramUser
from apps.core import bot


@shared_task
def clear_notifications():
    NotificationsClearer(True).run()
    NotificationsClearer(False).run()
    return True

@shared_task
def update_discount_balance():
    all_users = CustomUser.objects.all()
    for user in all_users:
        balance_prods = user.product_set.all().annotate(discount_delta=ExpressionWrapper(F('first_price') - F('latest_price'), output_field=IntegerField())).aggregate(Sum('discount_delta'))['discount_delta__sum']
        balance_wb_prods = user.wbdetailedinfo_set.all().annotate(discount_delta=ExpressionWrapper(F('first_price') - F('latest_price'), output_field=IntegerField())).aggregate(Sum('discount_delta'))['discount_delta__sum']
        if balance_prods is None: balance_prods = 0
        if balance_wb_prods is None: balance_wb_prods = 0
        balance = balance_prods + balance_wb_prods
        user.discount_balance = balance
        user.save()


@shared_task
def give_subs():
    subs_to_finish = SubRequest.objects.filter(status=SubRequest.Status.ACCEPTED).select_related('user')
    for sub_request in subs_to_finish:
        sub_request.user.subscription = sub_request.sub_plan
        sub_request.user.sub_expire = date.today() + relativedelta(months=int(sub_request.duration.split()[0]))
        sub_request.user.save()
        sub_request.status = SubRequest.Status.FINISHED
        sub_request.save()


@shared_task
def admin_sub_notif():
    subs_to_accept = SubRequest.objects.filter(status=SubRequest.Status.PENDING).select_related('user')
    for sub in subs_to_accept:
        sub.status = 'SENT'
        sub.save()
        send_mail(subject='SUB REQUEST', 
                    message=f'''ID пользователя: {sub.user.pk}
Username: {sub.user.username},
План: {sub.sub_plan}
Длительность: {sub.duration} мес.
Сумма: {sub.price} руб.
Время создания: {sub.created}''',
                    from_email=os.getenv('EMAIL_HEAVY'),
                    recipient_list=[os.getenv('EMAIL_HEAVY')],
                    fail_silently=True)
        



@shared_task
def cancel_subs():
    subs_to_check = CustomUser.objects.filter(subscription__in=['PLATINUM', 'ULTIMA'])
    for sub in subs_to_check:
        if sub.sub_expire < date.today():
            sub.subscription = 'FREE'
            sub.sub_expire = None
            sub.save()


@shared_task
def send_mail_support_form(name, email, message):
    send_mail(subject='from support form', 
                  message=f'''От: {name}
Email: {email}
Текст обращения: {message}''',
                  from_email=os.getenv('EMAIL_HEAVY'),
                  recipient_list=[os.getenv('EMAIL_HEAVY')],
                  fail_silently=True)
    

@shared_task
def add_tg_user(chat_id, username, first_name):
    TelegramUser.objects.get_or_create(defaults={'tg_id':chat_id},
                                       username=username,
                                       first_name=first_name)
    return True

@shared_task
def send_tg_notification(chat_id, text, photo_url=None):
    bot.send_notification_message(chat_id, text, photo_url)