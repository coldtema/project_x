from celery import shared_task, chain
from apps.wb_checker.utils.notifications import SmartNotification
from apps.wb_checker.utils.categories import update_menu_cats
from apps.wb_checker.utils.single_prods import PriceUpdater, AvaliabilityUpdater, WBPriceClearer
from apps.wb_checker import wb_menu_categories, wb_brands, wb_sellers
from apps.wb_checker.utils.top_prods import UpdaterInfoOfTop


@shared_task
def make_notif():
    '''Делаем уведомления внутри БД с обновленными ценами'''
    print('Делаем уведомления внутри БД с обновленными ценами')
    notif = SmartNotification()
    notif.run()
    del notif
    return True


@shared_task
def update_prices():
    '''Обновление цен на продукты и их наличия'''
    print('Обновление цен на продукты и их наличия')
    price_updater = PriceUpdater()
    price_updater.run()
    del price_updater
    return True


@shared_task
def update_avaliability():
    '''Проверка наличия продуктов, которых не было в наличии'''
    print('Проверка наличия продуктов, которых не было в наличии')
    avaliability_updater = AvaliabilityUpdater()
    avaliability_updater.run()
    del avaliability_updater
    return True


@shared_task
def update_top_prods():
    '''Обновление всех топ продуктов'''
    print('Обновление всех топ продуктов')
    wb_brands.TopWBProductBrandUpdater().run()
    wb_sellers.TopWBProductSellerUpdater().run()
    wb_menu_categories.TopWBProductMenuCategoryUpdater().run()
    return True


@shared_task
def update_top_prods_info():
    '''Обновление только информации топ продуктов'''
    print('Обновление только информации топ продуктов')
    updater_info_of_top = UpdaterInfoOfTop()
    updater_info_of_top.run()
    del updater_info_of_top
    return True


@shared_task
def update_menu_categories():
    '''Обновление категорий общего меню wb'''
    print('Обновление категорий общего меню wb')
    update_menu_cats()
    return True


@shared_task
def clear_prices():
    '''Удаление ненужных цен в wb_checker'''
    p_c = WBPriceClearer()
    p_c.run()
    del p_c
    return True


@shared_task
def update_single_prods_plus_make_notif():
    '''Обновление каждого продукта в приложении wb_checker + создание уведомлений'''
    print('Обновление каждого продукта в приложении wb_checker + создание уведомлений')
    chain(
        update_prices.si(),
        update_avaliability.si(),
        clear_prices.si(),
        make_notif.si(),
    )()
    return True
