from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.price_checker.models import Product
from apps.accounts.models import CustomUser


def index(request):
    return render(request, 'core/index.html')


# @login_required
# def menu(request):
#     return render(request, 'core/menu.html')


class MenuView(LoginRequiredMixin, View):
    def get(self, request):
        prods_snippet = request.user.product_set.all()[:3]
        print(prods_snippet)
        return render(request, 'core/menu.html', context={'prods_snippet': prods_snippet})