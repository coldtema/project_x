from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import AddTest
from .models import Test
from .tg_client import send_message_and_get_reply
from .question_digger import claim_questions

def all_tests_list(request):
    all_tests = Test.objects.all()
    if request.method == 'POST':
        form = AddTest(request.POST)
        if form.is_valid():
            new_test = Test.objects.create(name=request.POST.get('name'), text=request.POST.get('text'))
            response_from_bot = send_message_and_get_reply(request.POST.get('text'))
            claim_questions(test_object = new_test, text=response_from_bot)
            return HttpResponseRedirect('/test_generator')
    else:
        return render(request, 'test_generator/all_tests.html', context={'form': AddTest, 'all_tests': all_tests})

