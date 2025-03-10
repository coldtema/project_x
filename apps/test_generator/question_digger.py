import re
from .models import Question

def claim_questions_GPT4Telegrambot(text, test_object):
    list_of_questions = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\d+\.\s(.+\?)', string=text)))
    list_of_answers1 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'A\)\s(.+)\nB\)', string=text)))
    list_of_answers2 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'B\)\s(.+)\nC\)', string=text)))
    list_of_answers3 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'C\)\s(.+)\n\n', string=text)))
    list_of_right_answers = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\n\d+?\.\s([ABC])\)', string=text)))
    if len(list_of_questions) == len(list_of_answers1) == len(list_of_answers2) == len(list_of_answers3) == len(list_of_right_answers) and len(list_of_right_answers) != 0:
        test_object.save()
        for i in range(len(list_of_questions)):
            Question.objects.create(text=list_of_questions[i].strip(), 
                                    answer1=list_of_answers1[i].strip(), 
                                    answer2=list_of_answers2[i].strip(), 
                                    answer3=list_of_answers3[i].strip(), 
                                    right_answer = list_of_right_answers[i].strip(), 
                                    test=test_object)
    else:
        raise Exception

def claim_questions_chatsgpts_bot(text, test_object):
    list_of_questions = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\d+\.\s(.+\?)', string=text)))
    list_of_answers1 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\sA\)\s(.+)\n', string=text)))
    list_of_answers2 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\sB\)\s(.+)\n', string=text)))
    list_of_answers3 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\sC\)\s(.+)\n\n', string=text)))
    list_of_right_answers = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\n\d+?\.\s([ABC])\)', string=text)))
    if len(list_of_questions) == len(list_of_answers1) == len(list_of_answers2) == len(list_of_answers3) == len(list_of_right_answers):
        test_object.save()
        for i in range(len(list_of_questions)):
            Question.objects.create(text=list_of_questions[i].strip(), 
                                    answer1=list_of_answers1[i].strip(), 
                                    answer2=list_of_answers2[i].strip(), 
                                    answer3=list_of_answers3[i].strip(), 
                                    right_answer = list_of_right_answers[i].strip(), 
                                    test=test_object)
    else:
        raise Exception

def claim_questions_TypespaceBot(text, test_object):
    list_of_questions = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\-\s(.+\?)', string=text)))
    list_of_answers1 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'A\)\s(.+)\nB\)', string=text)))
    list_of_answers2 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'B\)\s(.+)\nC\)', string=text)))
    list_of_answers3 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'C\)\s(.+)\n\n', string=text)))
    list_of_right_answers = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\-\s([ABC])\)', string=text)))
    if len(list_of_questions) == len(list_of_answers1) == len(list_of_answers2) == len(list_of_answers3) == len(list_of_right_answers):
        test_object.save()
        for i in range(len(list_of_questions)):
            Question.objects.create(text=list_of_questions[i].strip(), 
                                    answer1=list_of_answers1[i].strip(), 
                                    answer2=list_of_answers2[i].strip(), 
                                    answer3=list_of_answers3[i].strip(), 
                                    right_answer = list_of_right_answers[i].strip(), 
                                    test=test_object)

def claim_questions_GPTChatRBot(text, test_object):
    list_of_questions = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\d+\.\s(.+\?)', string=text)))
    list_of_answers1 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\sA\)\s(.+)\n\s\s', string=text)))
    list_of_answers2 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\sB\)\s(.+)\n\s\s', string=text)))
    list_of_answers3 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\sC\) (.+)\n\n', string=text)))
    list_of_right_answers = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=r'\n\d+?\.\s+([ABC])\)', string=text)))
    if len(list_of_questions) == len(list_of_answers1) == len(list_of_answers2) == len(list_of_answers3) == len(list_of_right_answers):
        test_object.save()
        for i in range(len(list_of_questions)):
            Question.objects.create(text=list_of_questions[i].strip(), 
                                    answer1=list_of_answers1[i].strip(), 
                                    answer2=list_of_answers2[i].strip(), 
                                    answer3=list_of_answers3[i].strip(), 
                                    right_answer = list_of_right_answers[i].strip(), 
                                    test=test_object)