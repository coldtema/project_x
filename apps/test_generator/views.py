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
            send_message_and_get_reply(request.POST.get('text'), new_test, request.POST.get('max_questions'))
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
        questions_user_answers = zip(questions, user_answers)
        return render(request, 'test_generator/finish_page.html', 
                      context={'flag_best_result': flag_best_result, #переключатель лучшего результата (для показывания фразы в шаблоне)
                               'best_result_counter': best_result_counter, #результат пользователя
                               'max_result': len(right_answers), #максимальный результат по тесту - берется из БД
                               'answers_page': f'{id}/answers/', #ссылка для вызова action из формы для перехода на страницу ответов
                               'questions_user_answers': questions_user_answers, #зипка для итерации внутри шаблона
                               'user_answers': user_answers, #для передачи по последующий шаблон (answers) и склейки с вопросами для интерации внутри шаблона + невозможно посмотреть ответ по прямой ссылке))
                               'test_object': test_object, #объект теста, вопросы которого выводим
                               })
    return render(request, 'test_generator/pass_test.html', context={'test_object': test_object, 'questions': questions})


def answers_on_test(request, id):
    test_object = Test.objects.get(id=id)
    questions = test_object.question_set.all()
    try:
        user_answers = eval(request.POST['user_answers']) #из формы возвращается str - можно ли это поменять?
    except:
        return HttpResponseBadRequest('Не смотри ответики, пока не ответишь на вопросы!!')
    questions_user_answers = zip(questions, user_answers)
    return render(request, 'test_generator/answers.html', context={'questions_user_answers': questions_user_answers, 
                                                                   'test_object': test_object, 
                                                                   'test_url': f'/test_generator/pass_test/{id}',
                                                                   'main_url': f'/test_generator'})

def delete_test(request, id):
    Test.objects.get(id=id).delete()
    return HttpResponseRedirect('/test_generator')



