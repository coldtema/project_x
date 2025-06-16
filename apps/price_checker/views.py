import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from .forms import ProductForm, SendMailForm, SearchForm
from .models import Product, Price, Shop, Tag
from .site_explorer import get_shop_of_product
from django.urls import reverse
from apps.price_checker.utils import PriceUpdater, RepetitionsPriceUpdater
from apps.price_checker.utils import time_count, get_sparkline_points
from django.core.paginator import Paginator
from django.views.generic import FormView
from django.views import View
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.postgres.search import SearchVector
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import ExpressionWrapper, F, IntegerField
from django.contrib import messages
from django.utils import timezone
from apps.price_checker.notifications import SmartNotification



class PriceCheckerMain(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        product_form = ProductForm()
        sort = request.GET.get('sort', '')
        if sort == '':
            db_products = request.user.product_set.filter(enabled=True)
        if sort == 'price_asc':
            db_products =  request.user.product_set.filter(enabled=True).order_by('latest_price')
        if sort == 'price_desc':
            db_products =  request.user.product_set.filter(enabled=True).order_by('-latest_price')
        if sort == 'discount':
            db_products =  request.user.product_set.filter(enabled=True).annotate(delta=ExpressionWrapper(F('first_price')-F('latest_price'), output_field=IntegerField())).order_by('-delta')
        
        if request.GET.get('lazy-load'):
            paginator = Paginator(db_products, 24)
            page_number = request.GET.get('page', 1)
            if page_number == '': 
                page_number = 2
            else: 
                page_number = int(page_number) + 1
            if paginator.num_pages < page_number:
                return HttpResponse(status=413)#пока заглушка - лучше переделать
            db_products_page = paginator.get_page(page_number)
            return render(request, 'price_checker/partials/lazy_product_cards.html', context={'db_products_page':db_products_page,
                                                                                              'lazy_page': page_number})
        
        paginator = Paginator(db_products, 24)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)
        all_categories = Tag.objects.all().prefetch_related('shop_set')
        all_categories_dict = dict()
        for category in all_categories:
            all_categories_dict.setdefault(category, category.shop_set.all().values('name', 'main_url'))
        disabled_prod_count = request.user.product_set.filter(enabled=False).count()
        return render(request, 'price_checker/index.html', context={'form': product_form, 
                                                                    'db_products_page': db_products_page,
                                                                    'page_range': page_range,
                                                                    'all_categories_dict': all_categories_dict,
                                                                    'disabled_prod_count': disabled_prod_count})
    

    def post(self, request, *args, **kwargs):
        product_form = ProductForm(request.POST)
        try:
            self.get_product_info_and_save(request)
            #убрать в dispatch потом
            messages.success(request, 'Успех!')
        except:
            messages.success(request, 'Ошибка..')
        db_products = request.user.product_set.filter(enabled=True) 
        paginator = Paginator(db_products, 24)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        all_categories = Tag.objects.all().prefetch_related('shop_set')
        all_categories_dict = dict()
        for category in all_categories:
            all_categories_dict.setdefault(category, category.shop_set.all().values('name', 'main_url'))
        disabled_prod_count = request.user.product_set.filter(enabled=False).count()
        product_form = ProductForm()
        return render(request, 'price_checker/partials/product_cards.html', context={'form': product_form, 
                                                                                    'db_products_page': db_products_page,
                                                                                    'all_categories_dict': all_categories_dict,
                                                                                    'disabled_prod_count': disabled_prod_count})
            

    def get_product_info_and_save(self, request):
        potential_repetitions = Product.objects.filter(url=request.POST.get('url'))
        if not potential_repetitions:
            product_data = get_shop_of_product(request.POST.get('url'))
            if len(product_data['name']) > 150:
                product_data['name'] = product_data['name'][:147]+'...'
            new_product = Product.objects.create(name=product_data['name'],
                                                author=request.user,
                                                url=request.POST.get('url'),
                                                shop=Shop.objects.get(regex_name=product_data['shop']),  
                                                ref_url=request.POST.get('url'),
                                                latest_price=product_data['price_element'],
                                                first_price=product_data['price_element'])
            Price.objects.create(product=new_product, price=product_data['price_element'])
            request.user.slots-=1
            request.user.save()
        else:
            new_product, was_not_in_authors_db = Product.objects.get_or_create(name=potential_repetitions[0].name,
                                                                                author=request.user,
                                                                                url=request.POST.get('url'),
                                                                                shop=Shop.objects.get(regex_name=potential_repetitions[0].shop),  
                                                                                ref_url=request.POST.get('url'),
                                                                                defaults={'latest_price':potential_repetitions[0].latest_price,
                                                                                        'first_price':potential_repetitions[0].latest_price,
                                                                                        'repeated': True})
            if was_not_in_authors_db:
                Price.objects.create(product=new_product, price=potential_repetitions[0].latest_price)
                request.user.slots-=1
                request.user.save()
            else:
                new_product.updated=timezone.now()
                new_product.save()
            for repetiton in potential_repetitions:
                repetiton.repeated=True
            Product.objects.bulk_update(potential_repetitions, fields=['repeated'])
        return True



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


class DisabledProds(View):
    @time_count
    def get(self, request, *args, **kwargs):
        db_products =  request.user.product_set.filter(enabled=False)
        paginator = Paginator(db_products, 24)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_range = self.get_page_range(db_products_page, paginator)
        return render(request, 'price_checker/disabled_prods.html', context={'db_products_page': db_products_page,
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



def check_prod_of_user(id_of_prod, user):
    return user.product_set.filter(pk=id_of_prod).first() 
    


@login_required
def price_history(request, id):
    '''Функция для открытия истории цены конкретного продукта'''
    product_to_watch = check_prod_of_user(id, request.user)
    if not product_to_watch:
        return Http404('??? (нет такого продукта)')
    prices_of_product = product_to_watch.price_set.all().order_by('added_time')
    dates = []
    prices = []
    for elem in prices_of_product:
        dates.append(elem.added_time)
        prices.append(elem.price)
    svg_data = get_sparkline_points(prices)
    svg_data = list(map(lambda x: list(x), svg_data))
    for i in range(len(svg_data)):
        svg_data[i].append(dates[i])
    return render(request, 'price_checker/price_history.html', context={'product_to_watch': product_to_watch, 
                                                                        'prices_of_product': prices_of_product,
                                                                        'svg_data': svg_data})



@login_required
def delete_product(request, id):
    '''Функция представления для удаления конкретного продукта'''
    product_to_delete = check_prod_of_user(id, request.user)
    if not product_to_delete:
        return Http404('??? (нет такого продукта)')
    Product.objects.get(id=id).delete()  
    return HttpResponse()



@login_required
def delete_price(request, id):
    '''Функция представления для удаления цены конкретного продукта'''
    product_to_redirect = Price.objects.get(id=id).product
    product_to_redirect = check_prod_of_user(product_to_redirect.id, request.user)
    if not product_to_redirect:
        return HttpResponse()
    Price.objects.get(id=id).delete()
    prices_of_product = product_to_redirect.price_set.all().order_by('added_time')
    return render(request, 'price_checker/partials/price_table.html', context={'prices_of_product': prices_of_product,
                                                                               'product_to_watch': product_to_redirect})




def price_chart(request, id):
    product_to_watch = check_prod_of_user(id, request.user)
    if not product_to_watch:
        return HttpResponse()
    prices_of_product = product_to_watch.price_set.all().order_by('added_time')
    dates = []
    prices = []
    for elem in prices_of_product:
        dates.append(elem.added_time)
        prices.append(elem.price)
    if prices and prices[0] != product_to_watch.first_price:
        dates.insert(0, product_to_watch.created)
        prices.insert(0, product_to_watch.first_price)
    elif not prices:
        dates.insert(0, product_to_watch.created)
        prices.insert(0, product_to_watch.first_price)
    svg_data = get_sparkline_points(prices)
    svg_data = list(map(lambda x: list(x), svg_data))
    for i in range(len(svg_data)):
        svg_data[i].append(dates[i])
    return render(request, 'price_checker/partials/price_chart.html', context={'svg_data': svg_data})



class ShareProduct(LoginRequiredMixin, FormView):
    form_class = SendMailForm
    template_name = 'price_checker/share_product.html'

    def dispatch(self, request, *args, **kwargs):
        product_to_share = check_prod_of_user(self.kwargs['id'], request.user)
        if not product_to_share: #написать миксин
            return Http404('??? (нет такого продукта)')
        self.product = product_to_share #первое место прокидывания kwargs из url
        return super().dispatch(request, *args, **kwargs)


    def get_success_url(self):
        return reverse('price_checker:share_product', args=[self.product.id])
    

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({'name_of_product':self.product.name})
        return context_data


    def send_html_mail(self, email_to, comment):
        subject = "Смотрите, какую находку прислали!"
        from_email = os.getenv('EMAIL_HOST_USER')

        context = {
            'product_name': self.product.name,
            'product_link':  self.product.ref_url,
            'comment': comment,
            'image_cid': 'product_image'
        }

        html_content = render_to_string('price_checker/share_product_mail.html', context)
        text_content = strip_tags(html_content)  

        msg = EmailMultiAlternatives(subject, text_content, from_email, email_to)
        msg.attach_alternative(html_content, "text/html")

        with open('apps/price_checker/static/price_checker/cat.png', 'rb') as img:
            msg_image = img.read()
            msg.attach('cat.png', msg_image, 'image/png')

        msg.send()


    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            self.send_html_mail([form.cleaned_data['email_to']], form.cleaned_data['comment'])
        return super().post(request, *args, **kwargs)
    
    


class SearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = SearchForm()
        search_products = None
        return render(request, 'price_checker/search.html', context={'form': form,
                                                                     'search_products': search_products})   
    

    def post(self, request, *args, **kwargs):
        search_products = None
        form = SearchForm(request.POST)
        if form.is_valid():
            search_products = request.user.product_set.annotate(search=SearchVector('name', 'url')).filter(search=form.cleaned_data['query'])
        return render(request, 'price_checker/search.html', context={'form': form,
                                                                     'search_products': search_products})
