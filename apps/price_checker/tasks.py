from celery import shared_task, chain
from apps.price_checker.utils import RepetitionsPriceUpdater, PriceUpdater
from apps.price_checker.notifications import SmartNotification

@shared_task
def update_avaliability():
    p_u = RepetitionsPriceUpdater(False)
    p_u.run()
    p_u = PriceUpdater(False)
    p_u.run()
    del p_u
    return True


@shared_task
def make_notif():
    '''Формирование уведомлений внутри БД в price_checker'''
    SmartNotification().run()
    return True


@shared_task
def update_prices():
    '''Обновление цен в price_checker'''
    p_u = RepetitionsPriceUpdater(True)
    p_u.run()
    p_u = PriceUpdater(True)
    p_u.run()
    del p_u
    return True



@shared_task
def update_all_price_checker():
    chain(
        update_avaliability.si(),
        update_prices.si(),
        make_notif.si()
    )()
    return True