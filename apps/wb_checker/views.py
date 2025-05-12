from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from apps.accounts.models import CustomUser
from apps.wb_checker.utils.general_utils import time_count, check_detailed_info_of_user, get_sparkline_points
from apps.wb_checker.utils.single_prods import PriceUpdater, AvaliabilityUpdater
from apps.wb_checker.utils.categories import update_menu_cats
from apps.wb_checker.utils.top_prods import UpdaterInfoOfTop
from apps.wb_checker import wb_menu_categories, wb_products, wb_brands, wb_sellers
from .forms import WBProductForm, SearchForm
from .models import WBBrand, WBSeller, TopWBProduct, WBDetailedInfo, WBPrice, WBMenuCategory
import re
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector




class WBCheckerMain(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        self.form_parse = WBProductForm()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        prods = request.user.wbdetailedinfo_set.all().select_related('product', 'author')
        paginator = Paginator(prods, 12)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)
        return render(request, 'wb_checker/index.html', context={'form': self.form_parse,
                                                      'prods': db_products_page,
                                                      'page_range': page_range})
    
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


    @staticmethod
    def get_page_range(db_products_page, paginator):
        page_number = db_products_page.number
        number_of_pages = paginator.num_pages
        if page_number - 2 < 1:
            lowest_page = 1
        else:
            lowest_page = page_number - 2
        if page_number + 2 > number_of_pages:
            highest_page = number_of_pages
        else:
            highest_page = page_number + 2
        return list(range(lowest_page, highest_page+1))


class RecommentationsList(LoginRequiredMixin, View):
    @time_count
    def get(self, request, *args, **kwargs): #по факту можно все в кэш вынести
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
        sort = request.GET.get('sort', '')
        if sort == 'price':
            prods = sorted(prods, key=lambda x: x.latest_price)
        if sort == 'discount':
            prods = sorted(prods, key=lambda x: x.true_discount, reverse=True)
        if sort == '':
            prods = sorted(prods, key=lambda x: x.score, reverse=True)
        if sort == 'rating':
            prods = sorted(prods, key=lambda x: x.rating, reverse=True)
        if sort == 'feedbacks':
            prods = sorted(prods, key=lambda x: x.feedbacks, reverse=True)
        
        paginator = Paginator(prods, 24)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)

        print(len(prods))
        return render(request, "wb_checker/recommendations.html", context={'prods': db_products_page,
                                                                           'page_range': page_range})
    
    @staticmethod
    def get_page_range(db_products_page, paginator):
        page_number = db_products_page.number
        number_of_pages = paginator.num_pages
        if page_number - 2 < 1:
            lowest_page = 1
        else:
            lowest_page = page_number - 2
        if page_number + 2 > number_of_pages:
            highest_page = number_of_pages
        else:
            highest_page = page_number + 2
        return list(range(lowest_page, highest_page+1))




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
    return render(request, 'wb_checker/product_details.html', context={'product_to_watch': detailed_info_to_watch, 
                                                                       'prices_of_product': prices_of_detailed_info,
                                                                       'svg_data': svg_data})


@login_required
def delete_wb_product(request, id):
    '''Функция представления для удаления конкретного продукта'''
    product_to_delete = check_detailed_info_of_user(id, request.user)
    if not product_to_delete:
        return Http404('??? (нет такого продукта)')
    WBDetailedInfo.objects.get(pk=id).delete() #сделать доп функцию у продукта, что если он нигде не фигурирует в качестве Foreign Key, то его нужно удалить
    request.user.slots += 1
    request.user.save()
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@login_required
def delete_price(request, id):
    '''Функция представления для удаления цены конкретного продукта'''
    product_to_redirect = WBPrice.objects.get(id=id).detailed_info
    product_to_redirect = check_detailed_info_of_user(product_to_redirect.id, request.user)
    if not product_to_redirect:
        return Http404('??? (нет цены такого продукта)')
    WBPrice.objects.get(id=id).delete()
    return HttpResponseRedirect(reverse('wb_checker:wb_product_details', args=[product_to_redirect.id]))




def clear_db(request):
    '''Полная очистка таблиц, связанных с вб'''
    # TopWBProduct.objects.all().delete()
    WBMenuCategory.objects.all().delete()
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


class RecommendationSettings(View):
    def dispatch(self, request, *args, **kwargs):
        self.subs_brand = request.user.wbbrand_set.all()
        self.subs_brand_ids = list(map(lambda x: x.id, self.subs_brand))
        self.subs_seller = request.user.wbseller_set.all()
        self.subs_seller_ids = list(map(lambda x: x.id, self.subs_seller))
        self.subs_cats = request.user.wbmenucategory_set.all()
        self.subs_cats_ids = list(map(lambda x: x.id, self.subs_cats))
        self.search_products = None
        self.form = SearchForm()
        self.context = {'subs_brand':self.subs_brand,
                        'subs_brand_ids':self.subs_brand_ids,
                        'subs_seller':self.subs_seller,
                        'subs_seller_ids':self.subs_seller_ids,
                        'subs_cats':self.subs_cats,
                        'subs_cats_ids':self.subs_cats_ids,
                        'form':self.form,
                        'search_products': self.search_products}
        return super().dispatch(request, *args, **kwargs)
    

    def get(self, request, *args, **kwargs):
        return render(request, 'wb_checker/recommendation_settings.html', context=self.context)
    
    def post(self, request, *args, **kwargs):
        self.form = SearchForm(request.POST)
        self.context['form'] = self.form
        if self.form.is_valid():
            self.search_products = WBMenuCategory.objects.all().annotate(search=SearchVector('name')).filter(search=self.form.cleaned_data['query'])
            self.search_products = list(filter(lambda x: True if x.shard_key != 'blackhole' else False, self.search_products))
            self.context['search_products'] = self.search_products
        return render(request, 'wb_checker/recommendation_settings.html', context=self.context)
                                                                                
    