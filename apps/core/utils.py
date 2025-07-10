from apps.accounts.models import CustomUser, TelegramUser
import math
from django.db import transaction
from apps.core.models import Notification
from django.db.models import Prefetch

class NotificationsClearer:
    def __init__(self, wb_clearing=True):
        '''Инициализация необходимых атрибутов'''
        self.batch_size = 100
        self.len_all_authors_list = CustomUser.objects.all().count()
        self.batched_authors_list = []
        self.notification_ids_to_delete = []
        self.wb_clearing = wb_clearing


    def run(self):
        '''Запуск процесса удаления лишних уведомлений + батчинг по авторам'''
        for i in range(math.ceil(self.len_all_authors_list / self.batch_size)):
            self.batched_authors_list = CustomUser.objects.all().prefetch_related(Prefetch('notification_set', 
                                                                                           queryset=Notification.objects.filter(wb_product__isnull=self.wb_clearing)))[i*self.batch_size:(i+1)*self.batch_size]
            self.go_through_all_authors()     
            self.delete_notif_in_db()
            self.notification_ids_to_delete = []


    def go_through_all_authors(self):
        '''Функция, в которой идет проход по одному автору из батча'''
        for i in range(len(self.batched_authors_list)):
            if self.batched_authors_list[i].notification_set.count() > 20:
                self.notification_ids_to_delete.extend(list(map(lambda x: x['pk'], self.batched_authors_list[i].notification_set.order_by('-time')[20:].values('pk'))))


    @transaction.atomic
    def delete_notif_in_db(self):
        '''Занесение в БД обновления наличия'''
        Notification.objects.filter(pk__in=self.notification_ids_to_delete).delete()



def check_tg_code(tg_code, chat_id):
    user_to_connect = CustomUser.objects.filter(tg_token=tg_code).first()
    if user_to_connect:
        user_to_connect.tg_user = TelegramUser.objects.get(tg_id=chat_id)
        user_to_connect.save()
        return True
    return False
