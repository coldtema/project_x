from celery import shared_task
from apps.core.utils import NotificationsClearer
from apps.accounts.models import CustomUser, SubRequest
from django.db.models import F, IntegerField, ExpressionWrapper
from django.db.models.aggregates import Sum
from dateutil.relativedelta import relativedelta
from datetime import date


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