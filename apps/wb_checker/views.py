from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from apps.accounts.models import CustomUser
from apps.wb_checker.utils.general_utils import time_count, check_detailed_info_of_user, get_sparkline_points, get_brand_and_seller_from_prod, get_seller_from_link, get_brand_from_link
from apps.wb_checker.utils.single_prods import PriceUpdater, AvaliabilityUpdater
from apps.wb_checker.utils.categories import update_menu_cats
from apps.wb_checker.utils.top_prods import UpdaterInfoOfTop
from apps.wb_checker import wb_menu_categories, wb_products, wb_brands, wb_sellers
from .forms import WBProductForm, SearchForm
from .models import WBBrand, WBSeller, TopWBProduct, WBDetailedInfo, WBPrice, WBMenuCategory, WBProduct
import re
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector
from django.contrib import messages
from django.db.models import ExpressionWrapper, IntegerField, F
from apps.wb_checker.utils.notifications import SmartNotification




class WBCheckerMain(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        self.form_parse = WBProductForm()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        sort = request.GET.get('sort', '')
        if sort == '':
            prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author')
        if sort == 'price_asc':
            prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author').order_by('latest_price')
        if sort == 'price_desc':
            prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author').order_by('-latest_price')
        if sort == 'discount':
            prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author').annotate(delta=ExpressionWrapper(F('first_price')-F('latest_price'), output_field=IntegerField())).order_by('-delta')
        
    
        
        if request.GET.get('lazy-load'):
            paginator = Paginator(prods, 24)
            page_number = request.GET.get('page', 1)
            if page_number == '': 
                page_number = 2
            else: 
                page_number = int(page_number) + 1
            if paginator.num_pages < page_number:
                return HttpResponse(status=413)#пока заглушка - лучше переделать
            prods = paginator.get_page(page_number)
            return render(request, 'wb_checker/partials/lazy_product_cards.html', context={'prods':prods,
                                                                                           'lazy_page': page_number})
        
        
        paginator = Paginator(prods, 24)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)
        disabled_prod_count = request.user.wbdetailedinfo_set.filter(enabled=False).count()
        return render(request, 'wb_checker/index.html', context={'form': self.form_parse,
                                                                 'prods': db_products_page,
                                                                 'page_range': page_range,
                                                                 'disabled_prod_count': disabled_prod_count})
    
    def post(self, request, *args, **kwargs):
        form = WBProductForm(request.POST)
        if form.is_valid():
            author_object = CustomUser.objects.get(pk=request.user.id)
            try:
                form = WBProductForm()
                if request.POST.getlist('size', None): #пользователь выбрал размер
                    temp_dict = dict()
                    for elem in request.POST.getlist('size'):
                        temp_dict.setdefault(elem.split(' | ')[0], (elem.split(' | ')[1], elem.split(' | ')[2]))
                    self.url_dispatcher(request.POST['url'], author_object, temp_dict)

                else: #пользователь только хочет добавить продукт
                    raw_sizes = self.url_dispatcher(request.POST['url'], author_object)
                    if raw_sizes:
                        prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author')
                        disabled_prod_count = request.user.wbdetailedinfo_set.filter(enabled=False).count()
                        list_of_all_size_info = []
                        for size, volume_and_price in raw_sizes.items():
                            list_of_all_size_info.append([size, volume_and_price[0], volume_and_price[1]])
                        paginator = Paginator(prods, 24)
                        prods = paginator.get_page(1)
                        if request.POST.get('from_recs', None):
                            messages.success(request, 'Успех!')
                            return render(request, 'wb_checker/index.html', context={'form': self.form_parse,
                                                                                    'prods': prods,
                                                                                    'disabled_prod_count': disabled_prod_count,
                                                                                    'raw_sizes':list_of_all_size_info,
                                                                                    'url': request.POST['url']})
                        messages.success(request, 'Успех!')
                        return render(request, 'wb_checker/partials/product_cards.html', context={'raw_sizes':list_of_all_size_info,
                                                                                                    'prods':prods,
                                                                                                    'form': form,
                                                                                                    'disabled_prod_count': disabled_prod_count,
                                                                                                    'url': request.POST['url']}) 
                    else:
                        prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author')
                        disabled_prod_count = request.user.wbdetailedinfo_set.filter(enabled=False).count()
                        if request.POST.get('from_recs', None):
                            return redirect('wb_checker:all_price_list')
                        paginator = Paginator(prods, 24)
                        prods = paginator.get_page(1)
                        messages.success(request, 'Успех!')
                        return render(request, 'wb_checker/partials/product_cards.html', context={'prods':prods,
                                                                                                'form': form,
                                                                                  'disabled_prod_count': disabled_prod_count})
                messages.success(request, 'Успех!')
            except:
                print('отловленное уведомление об исключении')
                messages.error(request, 'Ошибка..')
            prods = request.user.wbdetailedinfo_set.filter(enabled=True).select_related('product', 'author')
            disabled_prod_count = request.user.wbdetailedinfo_set.filter(enabled=False).count()
            return render(request, 'wb_checker/partials/product_cards.html', context={'prods':prods,
                                                                                            'form': form,
                                                                                            'disabled_prod_count': disabled_prod_count})


    @time_count
    def url_dispatcher(self, url, author_object, sizes_to_save=None):
        '''Функция разведения по разным модулям парсинга исходя из введенного текста'''
        if re.search(pattern=r'catalog\/\d+\/detail', string=url):
            product = wb_products.Product(url, author_object, sizes_to_save)
            if product.sizes_dict: #надо потестить с удалением объекта класса
                return product.sizes_dict
            product.get_product_info()
            del product
        elif url.isdigit():
            product = wb_products.Product(f'https://www.wildberries.ru/catalog/{url}/detail.aspx', author_object, sizes_to_save)
            if product.sizes_dict: #надо потестить с удалением объекта класса
                return product.sizes_dict
            product.get_product_info()
            del product
        else:
            raise Exception


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


class WBDisabledProds(View):
    @time_count
    def get(self, request, *args, **kwargs):
        prods = request.user.wbdetailedinfo_set.filter(enabled=False).select_related('product', 'author')
        paginator = Paginator(prods, 12)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)
        return render(request, 'wb_checker/disabled_prods.html', context={'prods': db_products_page,
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



class RecommentationsList(LoginRequiredMixin, View):
    @time_count
    def get(self, request, *args, **kwargs): #по факту можно все в кэш вынести
        brands = request.user.wbbrand_set.all().prefetch_related('topwbproduct_set')
        sellers = request.user.wbseller_set.all().prefetch_related('topwbproduct_set')
        menu_categories = request.user.wbmenucategory_set.all().prefetch_related('topwbproduct_set')
        raw_prods_brands = list(map(lambda x: x.topwbproduct_set.filter(source='BRAND'), brands))
        raw_prods_sellers = list(map(lambda x: x.topwbproduct_set.filter(source='SELLER'), sellers))
        raw_prods_menu_categories = list(map(lambda x: x.topwbproduct_set.filter(source='CATEGORY'), menu_categories))
        raw_prods_brands.extend(raw_prods_sellers)
        raw_prods_brands.extend(raw_prods_menu_categories)
        prods = []
        for prod in raw_prods_brands:
            prods.extend(prod)
        prods_dict = dict()
        for prod in prods:
            prods_dict.update({prod.artikul:prod})
        prods = prods_dict.values()
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


        if request.GET.get('lazy-load'):
            paginator = Paginator(prods, 24)
            page_number = request.GET.get('page', 1)
            if page_number == '': 
                page_number = 2
            else: 
                page_number = int(page_number) + 1
            if paginator.num_pages < page_number:
                return HttpResponse(status=413)#пока заглушка - лучше переделать
            prods = paginator.get_page(page_number)
            return render(request, 'wb_checker/partials/lazy_recs_cards.html', context={'prods':prods,
                                                                                           'lazy_page': page_number})
        
        paginator = Paginator(prods, 24)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)
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

def price_chart(request , id):
    product_to_redirect = check_detailed_info_of_user(id, request.user)
    if not product_to_redirect:
        return HttpResponse()
    prices_of_detailed_info = product_to_redirect.wbprice_set.all().order_by('added_time')
    dates = []
    prices = []
    for elem in prices_of_detailed_info:
        dates.append(elem.added_time)
        prices.append(elem.price)
    if prices and prices[0] != product_to_redirect.first_price:
        dates.insert(0, product_to_redirect.created)
        prices.insert(0, product_to_redirect.first_price)
    elif not prices:
        dates.insert(0, product_to_redirect.created)
        prices.insert(0, product_to_redirect.first_price)
    svg_data = get_sparkline_points(prices)
    svg_data = list(map(lambda x: list(x), svg_data))
    for i in range(len(svg_data)):
        svg_data[i].append(dates[i])
    return render(request, 'wb_checker/partials/price_chart.html', context={'svg_data': svg_data})



@login_required
def delete_wb_product(request, id):
    '''Функция представления для удаления конкретного продукта'''
    product_to_delete = check_detailed_info_of_user(id, request.user)
    if not product_to_delete:
        return HttpResponse()
    WBDetailedInfo.objects.get(pk=id).delete() #сделать доп функцию у продукта, что если он нигде не фигурирует в качестве Foreign Key, то его нужно удалить
    request.user.slots += 1
    request.user.save()
    return HttpResponse()


def make_notif(request):
    notif = SmartNotification()
    notif.run()
    del notif
    return redirect('core:menu')

@login_required
def delete_price(request, id):
    '''Функция представления для удаления цены конкретного продукта'''
    detailed_info_to_watch = WBPrice.objects.get(id=id).detailed_info
    product_to_redirect = check_detailed_info_of_user(detailed_info_to_watch.id, request.user)
    if not product_to_redirect:
        return HttpResponse()
    WBPrice.objects.get(id=id).delete()
    prices_of_detailed_info = detailed_info_to_watch.wbprice_set.all().order_by('added_time')
    return render(request, 'wb_checker/partials/price_table.html', context={'prices_of_product': prices_of_detailed_info,
                                                                            'product_to_watch': detailed_info_to_watch})




def clear_db(request):
    '''Полная очистка таблиц, связанных с вб'''
    TopWBProduct.objects.all().delete()
    WBMenuCategory.objects.all().delete()
    WBBrand.objects.all().delete()
    WBSeller.objects.all().delete()
    WBProduct.objects.all().delete()
    WBDetailedInfo.objects.all().delete()
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
    @time_count
    def dispatch(self, request, *args, **kwargs):
        self.subs_brand = request.user.wbbrand_set.all()
        self.subs_brand_ids = list(map(lambda x: x.id, self.subs_brand))
        self.subs_seller = request.user.wbseller_set.all()
        self.subs_seller_ids = list(map(lambda x: x.id, self.subs_seller))
        self.subs_cats = request.user.wbmenucategory_set.all()
        self.subs_cats_ids = list(map(lambda x: x.id, self.subs_cats))
        self.search_categories = None
        self.form = SearchForm()
        self.form_add = WBProductForm()
        self.context = {'subs_brand':self.subs_brand,
                        'subs_brand_ids':self.subs_brand_ids,
                        'subs_seller':self.subs_seller,
                        'subs_seller_ids':self.subs_seller_ids,
                        'subs_cats':self.subs_cats,
                        'subs_cats_ids':self.subs_cats_ids,
                        'form':self.form,
                        'search_categories': self.search_categories,
                        'form_add': self.form_add}
        return super().dispatch(request, *args, **kwargs)
    

    def get(self, request, *args, **kwargs):
        if request.GET.get('form_type', None) == 'search_categories':
            search_categories = WBMenuCategory.objects.all().annotate(search=SearchVector('name')).filter(search=request.GET.get('query'))
            search_categories = list(filter(lambda x: True if x.shard_key != 'blackhole' else False, search_categories))
            subs_cats_ids = request.user.wbmenucategory_set.all().values('pk')
            subs_cats_ids = list(map(lambda x: x['pk'], subs_cats_ids))
            return render(request, 'wb_checker/partials/category_list.html', context={'search_categories': search_categories,
                                                                                      'subs_cats_ids': subs_cats_ids})
        if request.GET.get('form_type', None) == 'search_brand_seller':
            self.context['form_add'] =  WBProductForm(request.GET)
            try:
                self.context.setdefault('search_brand_seller', self.url_dispatcher(request))
            except:
                pass
            return render(request, 'wb_checker/partials/brand_seller_list.html', context=self.context)
        
        return render(request, 'wb_checker/recommendation_settings.html', context=self.context)
    
    def post(self, request, *args, **kwargs):
        try:
            return self.post_dispatcher(request)
        except:
            print('отлов ошибки')
        return render(request, 'wb_checker/recommendation_settings.html', context=self.context)
    
    @time_count
    def post_dispatcher(self, request):

        if request.POST.get('form_type', None) == 'search_submit_changes':
            search_subs = request.POST.getlist('search_subs', [])
            old_search_subs = request.POST.getlist('old_search_subs', None)
            if search_subs:
                request.user.wbmenucategory_set.add(*map(lambda x: int(x), search_subs))
            if old_search_subs:
                for old_sub in old_search_subs:
                    if old_sub not in search_subs:
                        request.user.wbmenucategory_set.remove(WBMenuCategory.objects.all().get(pk=int(old_sub)))
            self.context['form'] = self.form
            self.context['subs_cats'] = request.user.wbmenucategory_set.all()
            self.context['subs_cats_ids'] = list(map(lambda x: x.id, self.context['subs_cats']))
            messages.success(request=request, message='Успех!', extra_tags='success_search')
            return render(request, 'wb_checker/partials/recommendation_settings_main_part.html', context=self.context)
        

        if request.POST.get('form_type', None) == 'old_submit_changes':
            categories = request.POST.getlist('categories', [])
            brands = request.POST.getlist('brands', [])
            sellers = request.POST.getlist('sellers', [])
            request.user.wbmenucategory_set.set(map(lambda x: int(x), categories))
            request.user.wbbrand_set.set(map(lambda x: int(x), brands))
            request.user.wbseller_set.set(map(lambda x: int(x), sellers))
            self.context['subs_cats'] = request.user.wbmenucategory_set.all()
            self.context['subs_cats_ids'] = list(map(lambda x: x.id, self.context['subs_cats']))
            self.context['subs_brand'] = request.user.wbbrand_set.all()
            self.context['subs_brand_ids'] = list(map(lambda x: x.id, self.subs_brand))
            self.context['subs_seller'] = request.user.wbseller_set.all()
            self.context['subs_seller_ids'] = list(map(lambda x: x.id, self.subs_seller))
            messages.success(request=request, message='Успех!', extra_tags='success_old_submit')
            return render(request, 'wb_checker/partials/old_submit_changes.html', context=self.context)
        

        if request.POST.get('form_type', None) == 'search_brand_seller_submit_changes':
            brand_sub = request.POST.get('brand_sub', None)
            seller_sub = request.POST.get('seller_sub', None)
            old_brand_sub = request.POST.get('old_brand_sub', None)
            old_seller_sub = request.POST.get('old_seller_sub', None)
            if old_brand_sub and not brand_sub:
                request.user.wbbrand_set.remove(old_brand_sub)
                self.context['subs_brand'] = request.user.wbbrand_set.all()
                self.context['subs_brand_ids'] = list(map(lambda x: x.id, self.context['subs_brand']))
            if old_seller_sub and not seller_sub:
                request.user.wbseller_set.remove(old_seller_sub)
                self.context['subs_seller'] = request.user.wbseller_set.all()
                self.context['subs_seller_ids'] = list(map(lambda x: x.id, self.context['subs_seller']))
            if brand_sub:
                brand = wb_brands.Brand(WBBrand.objects.get(pk=int(brand_sub)).main_url, request.user)
                brand.run()
                del brand
                self.context['subs_brand'] = request.user.wbbrand_set.all()
                self.context['subs_brand_ids'] = list(map(lambda x: x.id, self.context['subs_brand']))
            if seller_sub:
                seller = wb_sellers.Seller(WBSeller.objects.get(pk=int(seller_sub)).main_url, request.user)
                seller.run()
                del seller
                self.context['subs_seller'] = request.user.wbseller_set.all()
                self.context['subs_seller_ids'] = list(map(lambda x: x.id, self.context['subs_seller']))
            messages.success(request=request, message='Успех!', extra_tags='success_search_brand_seller')
            return render(request, 'wb_checker/partials/recommendation_settings_main_part.html', context=self.context)


                                                                    
    @time_count
    def url_dispatcher(self, request):
        '''Функция разведения по разным модулям парсинга исходя из введенного текста'''
        if re.search(pattern=r'catalog\/\d+\/detail', string=request.GET['url']):
            product_artikul = re.search(r'\/(\d+)\/', request.GET['url']).group(1)
            return get_brand_and_seller_from_prod(product_artikul)
        elif request.GET['url'].isdigit():
            return get_brand_and_seller_from_prod(request.GET['url'])
        elif re.search(pattern=r'\/(seller)\/', string=request.GET['url']):
            return get_seller_from_link(request.GET['url'])
        elif re.search(pattern=r'\/(brands)\/', string=request.GET['url']):
            return get_brand_from_link(request.GET['url'])
        else:
            raise Exception