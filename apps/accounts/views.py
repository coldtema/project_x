from django.shortcuts import render
from django.views.generic import CreateView
from .forms import SignUpForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

class SignUpView(CreateView):
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    form_class = SignUpForm

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')