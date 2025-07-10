from django.shortcuts import render, redirect
from django.views.generic import CreateView
from .models import CustomUser, SubRequest
from apps.price_checker.models import Shop, Tag
from django.views import View
from .forms import SignUpForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import WBDestForm
from .pickpoints import load_dest_to_author
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, LoginView
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, AuthenticationForm
from django.http import HttpResponseNotAllowed
from django.conf import settings
from apps.core.tasks import admin_sub_notif
import random
from apps.core import bot



class SignUpView(View):
    '''View для регистрации пользователя'''
    def get(self, request):
        form = SignUpForm()
        return render(request, 'registration/signup.html', context={'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            form_errors = []
            for error_list in form.errors.values():
                form_errors.extend(error_list)
            form_errors = self.make_clean_errors(form_errors)
        return render(request, 'registration/signup.html', context={'form': form,
                                                                    'errors': form_errors})
    def make_clean_errors(self, form_errors):
        for i in range(len(form_errors)):
            form_errors[i] = self.customize_error(form_errors[i])
        return form_errors

    def customize_error(self, msg):
        if "too short" in msg:
            return "Пароль слишком короткий. Минимум 8 символов."
        if "too similar" in msg:
            return "Пароль слишком похож на имя пользователя."
        if "too common" in msg:
            return "Пароль слишком простой."
        if "entirely numeric" in msg:
            return "Пароль не должен состоять только из цифр."
        return msg
    

@login_required
def profile(request):
    slots = settings.SLOTS_DICT[request.user.subscription] - request.user.prods
    return render(request, 'accounts/profile.html', context={'slots':slots})



@login_required
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
    if request.user.tg_user is not None:
        return render(request, 'accounts/notification_edit.html', context={'telegram_code': 1})
    return render(request, 'accounts/notification_edit.html', context={'telegram_code': request.user.tg_token})


@login_required
def make_tg_code(request):
    if request.method == 'POST':
        if request.user.tg_token is None and request.user.tg_user is None:
            code = random.randint(100000, 999999)
            request.user.tg_token = code
            request.user.save()
            return render(request, 'accounts/partials/tg_form.html', context={'telegram_code': code})
        else:
            code = request.user.tg_token
            return render(request, 'accounts/partials/tg_form.html', context={'telegram_code': code})
    else:
        return HttpResponseNotAllowed(['POST'])



@login_required
def delete_tg_connection(request):
    if request.method == 'POST':
        chat_id = request.user.tg_user.tg_id
        request.user.tg_user = None
        request.user.save()
        bot.send_message_of_deleting_connection(chat_id)
        return render(request, 'accounts/partials/tg_form.html', context={'telegram_code': None})
    else:
        return HttpResponseNotAllowed(['POST']) 
    



@login_required
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
    




class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        form = PasswordResetForm(request.POST)
        if not CustomUser.objects.filter(email=request.POST.get('email')).first():
            return render(request, 'registration/password_reset_form.html', context={'form': form, 'error': 'Пользователь с таким E-mail не найден.'})
        return super().post(request, *args, **kwargs)
    


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_form_done.html'
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

    def post(self, request, *args, **kwargs):
        form = SetPasswordForm(user=request.user, data=request.POST)
        if not form.is_valid():
            form_errors = []
            for error_list in form.errors.values():
                form_errors.extend(error_list)
            form_errors = self.make_clean_errors(form_errors)
            return render(request, 'registration/password_reset_confirm.html', context={'form': form, 'errors': form_errors})
        return super().post(request, *args, **kwargs)

    def make_clean_errors(self, form_errors):
        for i in range(len(form_errors)):
            form_errors[i] = self.customize_error(form_errors[i])
        return form_errors

    def customize_error(self, msg):
        if "too short" in msg:
            return "Пароль слишком короткий. Минимум 8 символов."
        if "too similar" in msg:
            return "Пароль слишком похож на имя пользователя."
        if "too common" in msg:
            return "Пароль слишком простой."
        if "entirely numeric" in msg:
            return "Пароль не должен состоять только из цифр."
        if "match" in msg:
            return "Пароли не совпадают."
        return msg


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class CustomLoginView(LoginView):
    def form_invalid(self, form):
        form.errors.clear()
        form.add_error(None, "Неправильное имя пользователя или пароль")
        return self.render_to_response(self.get_context_data(form=form))
    

@login_required
def payment(request):
    if request.method == 'POST' and request.POST.get('request_payment'):
        if request.user.subrequest_set.filter(status__in=['PENDING', 'ACCEPTED', 'SENT']).exists():
            messages.error(request, message='У вас уже есть активный запрос на подписку. Пожалуйста, дождитесь его обработки')
            return render(request, 'accounts/payment.html')  
        elif request.user.subscription == 'PLATINUM' or request.user.subscription == 'ULTIMA':
            messages.error(request, message='У вас уже есть активная подписка. Подробная информация доступна в')
            return render(request, 'accounts/payment.html')  
        return render(request, 'accounts/payment.html', context={'plan': request.POST.get('plan'),
                                                                'time': request.POST.get('time'),
                                                                'sum': request.POST.get('sum')})
    else:
        return HttpResponseNotAllowed(['POST'])   

@login_required 
def payment_history(request):
    if request.method == 'POST' and request.POST.get('submit_payment'):
        if request.user.subrequest_set.filter(status__in=['PENDING', 'ACCEPTED', 'SENT']).exists():
            return render(request, 'accounts/payment_history.html', context={'orders': SubRequest.objects.filter(user=request.user).order_by('-created')})
        elif request.user.subscription == 'PLATINUM' or request.user.subscription == 'ULTIMA':
            return render(request, 'accounts/payment_history.html', context={'orders': SubRequest.objects.filter(user=request.user).order_by('-created')})
        SubRequest.objects.create(user=request.user,
                                sub_plan=request.POST.get('plan'),
                                duration=request.POST.get('time'),
                                price=request.POST.get('price'))
        admin_sub_notif.delay()
        return redirect('accounts:payment_history')
    return render(request, 'accounts/payment_history.html', context={'orders': SubRequest.objects.filter(user=request.user).order_by('-created')})


    

