from django.shortcuts import render, redirect
from django.views.generic import CreateView
from .models import CustomUser
from apps.price_checker.models import Shop, Tag
from django.views import View
from .forms import SignUpForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import WBDestForm
from .pickpoints import load_dest_to_author
from django.db.models import F, IntegerField, ExpressionWrapper
from django.db.models.aggregates import Sum
from django.contrib import messages

class SignUpView(CreateView):
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    form_class = SignUpForm

@login_required
def profile(request):
    sub_dict = {'FREE': 10,
                'PLATINUM':100,
                'ULTIMA':1000}
    used_slots = sub_dict[request.user.subscription] - request.user.slots
    return render(request, 'accounts/profile.html', context={'used_slots':used_slots})


def update_discount_balance(request):
    all_users = CustomUser.objects.all()
    for user in all_users:
        balance_prods = user.product_set.all().annotate(discount_delta=ExpressionWrapper(F('first_price') - F('latest_price'), output_field=IntegerField())).aggregate(Sum('discount_delta'))['discount_delta__sum']
        balance_wb_prods = user.wbdetailedinfo_set.all().annotate(discount_delta=ExpressionWrapper(F('first_price') - F('latest_price'), output_field=IntegerField())).aggregate(Sum('discount_delta'))['discount_delta__sum']
        if balance_prods is None: balance_prods = 0
        if balance_wb_prods is None: balance_wb_prods = 0
        balance = balance_prods + balance_wb_prods
        user.discount_balance = balance
        user.save()
    # all_shops = Shop.objects.all()
    # for shop in all_shops:
    #     tag = shop_to_category.get(shop.regex_name, None)
    #     if tag:
    #         tag, _ = Tag.objects.get_or_create(name=tag)
    #         tag.shop_set.add(shop)
    return redirect('accounts:profile')

def notification_edit(request):
    if request.method == 'POST':
        try:
            request.user.notification_discount = int(request.POST.get('notification_discount', 10))
            request.user.notification_discount_price = int(request.POST.get('notification_discount_price', 300))
            request.user.pricedown_notification = bool(request.POST.get('pricedown_notification', False))
            request.user.priceup_notification = bool(request.POST.get('priceup_notification', False))
            request.user.save()
            messages.success(request, message='Успех!')
        except:
            messages.error(request, message='Ошибка...')
        return render(request, 'accounts/partials/notif_form.html')
    return render(request, 'accounts/notification_edit.html')

def subscription_edit(request):
    if request.GET.get('plan-toggle', None) == 'monthly':
        return render(request, 'accounts/partials/subs_month.html')
    
    if request.GET.get('plan-toggle', None) == 'halfyear':
        return render(request, 'accounts/partials/subs_half_year.html')
    
    return render(request, 'accounts/subscription_edit.html')


class GeolocationEditView(LoginRequiredMixin, View):
    def get(self, request):
        form = WBDestForm(initial={'address': request.user.dest_name})
        return render(request, 'accounts/geolocation_edit.html', context={'form': form,
                                                                          'success': ''})

    def post(self, request):
        if WBDestForm(request.POST).is_valid() and request.user.dest_name != request.POST['address']:
            try:
                load_dest_to_author(request.user.id, request.POST['address'])
            except:
                form = WBDestForm(initial={'address': request.user.dest_name})
                messages.error(request=request, message='Ошибка..')
                return render(request, 'accounts/partials/geo_form.html', context={'form': form})
            
            form = WBDestForm(initial={'address': CustomUser.objects.get(pk=request.user.pk).dest_name})
            messages.success(request=request, message='Успех!')
            return render(request, 'accounts/partials/geo_form.html', context={'form': form})
        
        form = WBDestForm(initial={'address': request.POST['address']})
        messages.success(request=request, message='Успех!')
        return render(request, 'accounts/partials/geo_form.html', context={'form': form})
    

def change_password(request):

    return(render(request, 'accounts/change_password.html'))
