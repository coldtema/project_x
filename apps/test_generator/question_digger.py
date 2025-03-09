import re
from .models import Question

def claim_questions(text, test_object):
    list_of_questions = re.findall(pattern=r'\d+?\.\s(.+\?)', string=text)
    list_of_answers1 = re.findall(pattern=r'\s\sA\)\s(.+?)\s\n', string=text)
    list_of_answers2 = re.findall(pattern=r'\s\sB\)\s(.+?)\s\n', string=text)
    list_of_answers3 = re.findall(pattern=r'\s\sC\)\s(.+?)\s\n', string=text)
    list_of_right_answers = re.findall(pattern=r'\d+?\.\s(\w)\)', string=text)
    if len(list_of_questions) == len(list_of_answers1) == len(list_of_answers2) == len(list_of_answers3) == len(list_of_right_answers):
        for i in range(len(list_of_questions)):
            Question.objects.create(text=list_of_questions[i].strip(), 
                                    answer1=list_of_answers1[i].strip(), 
                                    answer2=list_of_answers2[i].strip(), 
                                    answer3=list_of_answers3[i].strip(), 
                                    right_answer = list_of_right_answers[i].strip(), 
                                    test=test_object)
