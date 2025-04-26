from django.shortcuts import render
from django.views.generic import CreateView
from .forms import SignUpForm
from django.urls import reverse_lazy

class SignUpView(CreateView):
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    form_class = SignUpForm
