from django.shortcuts import render


def index(request):
    return render(request, 'core/index.html')



def menu(request):
    return render(request, 'core/menu.html')