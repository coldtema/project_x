import os
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from .forms import ProductForm, SendMailForm, SearchForm
from .models import Product, Price, Shop
from .site_explorer import get_shop_of_product
from apps.blog.models import Author
import time
from functools import wraps
from .chart_builder import plot_price_history
# from .async_shit import process_sites
from django.urls import reverse, reverse_lazy
from apps.price_checker.utils import PriceUpdater
from apps.price_checker.utils import time_count
from django.core.paginator import Paginator
from django.views.generic import FormView
from django.views import View
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.postgres.search import SearchVector



def all_price_list(request):
    '''Функция представления для отображения всех продуктов'''
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            product_data = get_shop_of_product(request.POST.get('url'))
            new_product = Product.objects.create(name=product_data['name'][:150], #оформить с троеточием, если слишком большое имя
                                                 url=request.POST.get('url'),
                                                 latest_price=product_data['price_element'], 
                                                 shop=Shop.objects.get(regex_name=product_data['shop']),  
                                                 ref_url=request.POST.get('url')) #прописать здесь get_or_create и вообще вынести в другое место
            Author.objects.get(id=2).product_set.add(new_product)
            Price.objects.create(product=new_product, price=product_data['price_element'])
            return HttpResponseRedirect(reverse('price_checker:all_price_list'))
        else:
            return HttpResponseBadRequest('Так себе ссылка')
    else:
        product_form = ProductForm()
        db_products = Product.objects.filter(enabled=True)
        paginator = Paginator(db_products, 10)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_number = db_products_page.number #исключение обработано строкой выше, а вот тип может быть строкой итд, поэтому беру номер еще раз уже из готового объекта класса Page
        number_of_pages = paginator.num_pages
        if page_number - 3 < 1:
            lowest_page = 1
        else:
            lowest_page = page_number - 3
        if page_number + 3 > number_of_pages:
            highest_page = number_of_pages
        else:
            highest_page = page_number + 3
        page_range = list(range(lowest_page, highest_page+1))
        return render(request, 'price_checker/index.html', context={'form': product_form, 
                                                                    'db_products_page': db_products_page,
                                                                    'page_range': page_range})




def price_history(request, id):
    '''Функция для открытия истории цены конкретного продукта'''
    product_to_watch = get_object_or_404(Product, id=id)
    prices_of_product = Price.objects.filter(product_id=id)
    dates = []
    prices = []
    for elem in prices_of_product:
        dates.append(elem.added_time)
        prices.append(elem.price)
    plot_price_history(dates, prices)
    return render(request, 'price_checker/price_history.html', context={'product_to_watch': product_to_watch, 
                                                                        'prices_of_product': prices_of_product})


def delete_product(request, id):
    '''Функция представления для удаления конкретного продукта'''
    Product.objects.get(id=id).delete()
    return HttpResponseRedirect(reverse('price_checker:all_price_list'))



def delete_price(request, id):
    '''Функция представления для удаления цены конкретного продукта'''
    product_to_redirect = Price.objects.get(id=id).product
    id_of_product = product_to_redirect.id
    Price.objects.get(id=id).delete()
    return HttpResponseRedirect(reverse('price_checker:price_history', args=[id_of_product]))



@time_count
def update_prices(request):
    '''Функция представления для запуска обновления цен'''
    p_u = PriceUpdater()
    p_u.run()
    del p_u
    return HttpResponseRedirect(reverse('price_checker:all_price_list'))



class ShareProduct(FormView):
    form_class = SendMailForm
    template_name = 'price_checker/share_product.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = Product.enabled_products.get(id=self.kwargs['id']) #перыое место прокидывания kwargs из url
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
    


class SearchView(View):
    def get(self, request, *args, **kwargs):
        form = SearchForm()
        search_products = None
        return render(request, 'price_checker/search.html', context={'form': form,
                                                                     'search_products': search_products})   
    

    def post(self, request, *args, **kwargs):
        search_products = None
        form = SearchForm(request.POST)
        if form.is_valid():
            search_products = Product.enabled_products.annotate(search=SearchVector('name', 'url')).filter(search=form.cleaned_data['query'])
        return render(request, 'price_checker/search.html', context={'form': form,
                                                                     'search_products': search_products})
