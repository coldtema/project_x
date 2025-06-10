import math
from apps.wb_checker.models import WBDetailedInfo
from apps.core.models import Notification
from django.db import transaction


class SmartNotification():
    def __init__(self):
        self.batch_size = 10000
        self.notifications_to_save = []
        self.len_detailed_info_list = WBDetailedInfo.objects.filter(enabled=True).count()


    def run(self):
        for i in range(math.ceil(self.len_detailed_info_list / self.batch_size)):
            self.batched_detailed_info_list = WBDetailedInfo.objects.filter(enabled=True).select_related('author', 'product')[i*self.batch_size:(i+1)*self.batch_size]
            self.check_batch()
            self.save_notif()
            self.notifications_to_save = []

            
    def check_batch(self):
        for current_detailed_info in self.batched_detailed_info_list:
            if current_detailed_info.last_notified_price:
                if abs(current_detailed_info.latest_price - current_detailed_info.last_notified_price) > current_detailed_info.author.notification_discount_price or \
                abs(int((current_detailed_info.latest_price-current_detailed_info.last_notified_price)/(current_detailed_info.latest_price/100))) > current_detailed_info.author.notification_discount:
                    self.make_notification(current_detailed_info)
            else:
                if abs(current_detailed_info.latest_price - current_detailed_info.first_price) > current_detailed_info.author.notification_discount_price or \
                    abs(int((current_detailed_info.latest_price-current_detailed_info.first_price)/(current_detailed_info.latest_price/100))) > current_detailed_info.author.notification_discount:
                    self.make_notification(current_detailed_info)

    def make_notification(self, current_detailed_info):
        if current_detailed_info.last_notified_price:
            if current_detailed_info.last_notified_price > current_detailed_info.latest_price and current_detailed_info.author.pricedown_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{current_detailed_info.product.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{current_detailed_info.last_notified_price - current_detailed_info.latest_price} ₽</b>! (-{int((current_detailed_info.last_notified_price-current_detailed_info.latest_price)/(current_detailed_info.last_notified_price/100))}%)',
                                                                wb_product=current_detailed_info,
                                                                user=current_detailed_info.author))
                current_detailed_info.last_notified_price = current_detailed_info.latest_price
            elif current_detailed_info.author.priceup_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{current_detailed_info.product.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {current_detailed_info.latest_price - current_detailed_info.last_notified_price} ₽</b>! (+{int((current_detailed_info.latest_price - current_detailed_info.last_notified_price)/(current_detailed_info.latest_price/100))}%)',
                                                                wb_product=current_detailed_info,
                                                                user=current_detailed_info.author))
                current_detailed_info.last_notified_price = current_detailed_info.latest_price
        else:
            if current_detailed_info.first_price > current_detailed_info.latest_price and current_detailed_info.author.pricedown_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{current_detailed_info.product.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{current_detailed_info.first_price - current_detailed_info.latest_price} ₽</b>! (-{int((current_detailed_info.first_price-current_detailed_info.latest_price)/(current_detailed_info.first_price/100))}%)',
                                                                wb_product=current_detailed_info,
                                                                user=current_detailed_info.author))
                current_detailed_info.last_notified_price = current_detailed_info.latest_price
            elif current_detailed_info.author.priceup_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{current_detailed_info.product.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {current_detailed_info.latest_price - current_detailed_info.first_price} ₽</b>! (+{int((current_detailed_info.latest_price - current_detailed_info.first_price)/(current_detailed_info.latest_price/100))}%)',
                                                                wb_product=current_detailed_info,
                                                                user=current_detailed_info.author))
                current_detailed_info.last_notified_price = current_detailed_info.latest_price


    @transaction.atomic
    def save_notif(self):
        Notification.objects.bulk_create(self.notifications_to_save)
        WBDetailedInfo.objects.bulk_update(self.batched_detailed_info_list, ['last_notified_price'])


