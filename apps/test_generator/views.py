from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import AddTest
from .models import Test
from .tg_client import send_message_and_get_reply

def all_tests_list(request):
    all_tests = Test.objects.all()
    if request.method == 'POST':
        form = AddTest(request.POST)
        if form.is_valid():
            Test.objects.create(name=request.POST.get('name'), text=request.POST.get('text'))
            print(send_message_and_get_reply(request.POST.get('text')))
            return HttpResponseRedirect('/test_generator')
    else:
        return render(request, 'test_generator/all_tests.html', context={'form': AddTest, 'all_tests': all_tests})

