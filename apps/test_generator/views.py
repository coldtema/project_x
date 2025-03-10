from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from .forms import AddTest
from .models import Test
from .tg_client import send_message_and_get_reply

def all_tests_list(request):
    all_tests = Test.objects.all()
    if request.method == 'POST':
        form = AddTest(request.POST)
        if form.is_valid():
            new_test = Test(name=request.POST.get('name'), text=request.POST.get('text'))
            send_message_and_get_reply(request.POST.get('text'), new_test)
            return HttpResponseRedirect('/test_generator')
    else:
        return render(request, 'test_generator/all_tests.html', context={'form': AddTest, 'all_tests': all_tests})
    
def pass_test(request, id):
    test_object = Test.objects.get(id=id)
    questions = test_object.question_set.all()
    if request.method == 'POST':
        user_answers = list(map(lambda x: x[0], filter(lambda x: True if len(x) == 1 else False, request.POST.values()))) #filter - чтобы убрать токен
        right_answers = list(map(lambda x: x.right_answer, questions))
        if len(user_answers) != len(right_answers):
            return HttpResponseBadRequest('Ответьте, пожалуйста, на все вопросы')
        best_result_counter = 0
        flag_best_result = False
        for i in range(len(user_answers)):
            if user_answers[i] == right_answers[i]:
                best_result_counter+=1
        if best_result_counter > test_object.best_result:
            flag_best_result = True
            test_object.best_result = best_result_counter
            test_object.save()
        return render(request, 'test_generator/finish_page.html', context={'flag_best_result': flag_best_result, 'best_result_counter': best_result_counter, 'max_result': len(right_answers)})
    return render(request, 'test_generator/pass_test.html', context={'test_object': test_object, 'questions': questions})

def delete_test(request, id):
    Test.objects.get(id=id).delete()
    return HttpResponseRedirect('/test_generator')


