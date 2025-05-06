from django.shortcuts import render
from django.views.generic import CreateView
from .models import CustomUser
from django.views import View
from .forms import SignUpForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import WBDestForm
from .pickpoints import load_dest_to_author

class SignUpView(CreateView):
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    form_class = SignUpForm

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


def profile_edit(request):

    return(render(request, 'accounts/profile_edit.html'))

def subscription_edit(request):

    return(render(request, 'accounts/subscription_edit.html'))


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
                return render(request, 'accounts/geolocation_edit.html', context={'form': form,
                                                                          'success': 'Возникла ошибка.'})
            form = WBDestForm(initial={'address': CustomUser.objects.get(pk=request.user.pk).dest_name})
            return render(request, 'accounts/geolocation_edit.html', context={'form': form,
                                                                          'success': 'Успешно изменено!'})
        form = WBDestForm(initial={'address': request.POST['address']})
        return render(request, 'accounts/geolocation_edit.html', context={'form': form,
                                                                          'success': 'Успешно изменено!'})
    

def change_password(request):

    return(render(request, 'accounts/change_password.html'))
