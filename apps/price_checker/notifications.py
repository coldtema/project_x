import math
from apps.price_checker.models import Product
from apps.core.models import Notification
from django.db import transaction
from apps.core import tasks


class SmartNotification():
    def __init__(self):
        self.batch_size = 10000
        self.notifications_to_save = []
        self.len_prod_list = Product.objects.filter(enabled=True).count()


    def run(self):
        for i in range(math.ceil(self.len_prod_list / self.batch_size)):
            self.batched_prod_list = Product.objects.filter(enabled=True).select_related('author', 'shop')[i*self.batch_size:(i+1)*self.batch_size]
            self.check_batch()
            self.save_notif()
            self.send_tg_notifications()
            self.notifications_to_save = []

            
    def check_batch(self):
        for current_prod in self.batched_prod_list:
            if current_prod.last_notified_price:
                if abs(current_prod.latest_price - current_prod.last_notified_price) > current_prod.author.notification_discount_price or \
                abs(int((current_prod.latest_price-current_prod.last_notified_price)/(current_prod.latest_price/100))) > current_prod.author.notification_discount:
                    self.make_notification(current_prod)
            else:
                if abs(current_prod.latest_price - current_prod.first_price) > current_prod.author.notification_discount_price or \
                    abs(int((current_prod.latest_price-current_prod.first_price)/(current_prod.latest_price/100))) > current_prod.author.notification_discount:
                    self.make_notification(current_prod)

    def make_notification(self, current_prod):
        detailed_text = ''
        if current_prod.latest_price < current_prod.first_price:
            detailed_text = f' (↓ {abs(current_prod.first_price-current_prod.latest_price)}₽)'
        elif current_prod.latest_price > current_prod.first_price:
            detailed_text = f' (↑ {abs(current_prod.first_price-current_prod.latest_price)}₽)'

        if current_prod.last_notified_price:
            if current_prod.last_notified_price > current_prod.latest_price and current_prod.author.pricedown_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒{current_prod.shop.name}</i> <br> <b>📦{current_prod.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{current_prod.last_notified_price - current_prod.latest_price} ₽</b>! (-{int((current_prod.last_notified_price-current_prod.latest_price)/(current_prod.last_notified_price/100))}%)<br>💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                tg_text=f'<i>🛒{current_prod.shop.name}</i>\n<a href="{current_prod.url}"><b>📦{current_prod.name}</b></a>\n🟢 Цена <b>упала</b> на <b>{current_prod.last_notified_price - current_prod.latest_price} ₽</b>! (-{int((current_prod.last_notified_price-current_prod.latest_price)/(current_prod.last_notified_price/100))}%)\n💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                product=current_prod,
                                                                user=current_prod.author))
                current_prod.last_notified_price = current_prod.latest_price
            elif current_prod.author.priceup_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒{current_prod.shop.name}</i> <br> <b>📦{current_prod.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {current_prod.latest_price - current_prod.last_notified_price} ₽</b>! (+{int((current_prod.latest_price - current_prod.last_notified_price)/(current_prod.latest_price/100))}%)<br>💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                    tg_text=f'<i>{current_prod.shop.name}</i>\n<a href="{current_prod.url}"><b>📦{current_prod.name}</b></a>\n🔴 Цена <b>поднялась</b> на <b> {current_prod.latest_price - current_prod.last_notified_price} ₽</b>! (+{int((current_prod.latest_price - current_prod.last_notified_price)/(current_prod.latest_price/100))}%)\n💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                    product=current_prod,
                                                                    user=current_prod.author))
                current_prod.last_notified_price = current_prod.latest_price
        else:
            if current_prod.first_price > current_prod.latest_price and current_prod.author.pricedown_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒{current_prod.shop.name}</i> <br> <b>📦{current_prod.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{current_prod.first_price - current_prod.latest_price} ₽</b>! (-{int((current_prod.first_price-current_prod.latest_price)/(current_prod.first_price/100))}%)<br>💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                               tg_text=f'<i>🛒{current_prod.shop.name}</i>\n<a href="{current_prod.url}"><b>📦{current_prod.name}</b></a>\n🟢 Цена <b>упала</b> на <b>{current_prod.first_price - current_prod.latest_price} ₽</b>! (-{int((current_prod.first_price-current_prod.latest_price)/(current_prod.first_price/100))}%)\n💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                product=current_prod,
                                                                user=current_prod.author))
                current_prod.last_notified_price = current_prod.latest_price
            elif current_prod.author.priceup_notification is True:
                self.notifications_to_save.append(Notification(text=f'<i>🛒{current_prod.shop.name}</i> <br> <b>📦{current_prod.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {current_prod.latest_price - current_prod.first_price} ₽</b>! (+{int((current_prod.latest_price - current_prod.first_price)/(current_prod.latest_price/100))}%)<br>💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                    tg_text=f'<i>{current_prod.shop.name}</i>\n<a href="{current_prod.url}"><b>📦{current_prod.name}</b></a>\n🔴 Цена <b>поднялась</b> на <b> {current_prod.latest_price - current_prod.first_price} ₽</b>! (+{int((current_prod.latest_price - current_prod.first_price)/(current_prod.latest_price/100))}%)\n💵<b>Текущая цена:</b> {current_prod.latest_price}₽{detailed_text}',
                                                                    product=current_prod,
                                                                    user=current_prod.author))
                current_prod.last_notified_price = current_prod.latest_price

    @transaction.atomic
    def save_notif(self):
        Notification.objects.bulk_create(self.notifications_to_save)
        Product.objects.bulk_update(self.batched_prod_list, ['last_notified_price'])

    def send_tg_notifications(self):
        for notif in self.notifications_to_save:
            if notif.user.tg_user:
                tasks.send_tg_notification.delay(notif.user.tg_user.tg_id, notif.tg_text)


