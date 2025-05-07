from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from apps.accounts.models import CustomUser
from apps.wb_checker.utils.general_utils import time_count, check_detailed_info_of_user, get_sparkline_points
from apps.wb_checker.utils.single_prods import PriceUpdater, AvaliabilityUpdater
from apps.wb_checker.utils.categories import update_menu_cats
from apps.wb_checker.utils.top_prods import UpdaterInfoOfTop
from apps.wb_checker import wb_menu_categories, wb_products, wb_brands, wb_sellers
from .forms import WBProductForm
from .models import WBBrand, WBSeller, TopWBProduct
import re
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin




class WBCheckerMain(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        self.form_parse = WBProductForm()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        prods = request.user.wbdetailedinfo_set.all().select_related('product', 'author') 
        return render(request, 'index.html', context={'form': self.form_parse,
                                                      'prods': prods})
    
    def post(self, request, *args, **kwargs):
        form = WBProductForm(request.POST)
        if form.is_valid():
            author_object = CustomUser.objects.get(pk=request.user.id)
            self.url_dispatcher(request.POST['url'], author_object)
        return HttpResponseRedirect(reverse('wb_checker:all_price_list'))

    @time_count
    def url_dispatcher(self, url, author_object):
        '''Функция разведения по разным модулям парсинга исходя из введенного текста'''
        if re.search(pattern=r'catalog\/\d+\/detail', string=url):
            product = wb_products.Product(url, author_object)
            product.get_product_info()
            del product
        elif re.search(pattern=r'\/(seller)\/', string=url):
            seller = wb_sellers.Seller(url, author_object)
            seller.run()
            del seller
        elif re.search(pattern=r'\/(brands)\/', string=url):
            brand = wb_brands.Brand(url, author_object)
            brand.run()
            del brand
        elif re.search(pattern=r'catalog\/\D+\/?', string=url):
            menu_category = wb_menu_categories.MenuCategory(url, author_object)
            menu_category.run()
            del menu_category


class RecommentationsList(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        brands = request.user.wbbrand_set.all().prefetch_related('topwbproduct_set')
        raw_prods = list(map(lambda x: x.topwbproduct_set.all(), brands))
        prods = []
        for prod in raw_prods:
            prods.extend(prod)
        print(prods)
        return render(request, "recommendations.html", context={'prods': prods})




@login_required
def wbproduct_details(request, id):
    '''Функция для открытия истории цены конкретного продукта'''
    detailed_info_to_watch = check_detailed_info_of_user(id, request.user)
    if not detailed_info_to_watch:
        return Http404('??? (нет такого продукта)')
    prices_of_detailed_info = detailed_info_to_watch.wbprice_set.all().order_by('added_time')
    dates = []
    prices = []
    for elem in prices_of_detailed_info:
        dates.append(elem.added_time)
        prices.append(elem.price)
    svg_data = get_sparkline_points(prices)
    svg_data = list(map(lambda x: list(x), svg_data))
    for i in range(len(svg_data)):
        svg_data[i].append(dates[i])
    return render(request, 'product_details.html', context={'product_to_watch': detailed_info_to_watch, 
                                                            'prices_of_product': prices_of_detailed_info,
                                                            'svg_data': svg_data})



def delete_price(request):
    pass


def clear_db(request):
    '''Полная очистка таблиц, связанных с вб'''
    TopWBProduct.objects.all().delete()
    
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
def update_menu_categories(request):
    '''Обновление категорий общего меню wb'''
    update_menu_cats()
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
def update_prices(request):
    '''Обновление цен на продукты и их наличия'''
    price_updater = PriceUpdater()
    price_updater.run()
    del price_updater
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
def update_avaliability(request):
    '''Проверка наличия продуктов, которых не было в наличии'''
    avaliability_updater = AvaliabilityUpdater()
    avaliability_updater.run()
    del avaliability_updater
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))

            



@time_count
def update_top_prods(request):
    wb_brands.TopWBProductBrandUpdater().run()
    wb_sellers.TopWBProductSellerUpdater().run()
    wb_menu_categories.TopWBProductMenuCategoryUpdater().run()
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))




@time_count
def update_top_prods_info(request):
    updater_info_of_top = UpdaterInfoOfTop()
    updater_info_of_top.run()
    del updater_info_of_top
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))