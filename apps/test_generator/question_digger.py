import re
from .models import Question


dig_patterns = [
    [r'\d+\.\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+)\n\n', r'\n\d+?\.\s([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'\sA\)\s(.+)\n', r'\sB\)\s(.+)\n', r'\sB\)\s(.+)\n', r'\n\d+?\.\s([ABC])\)'],
    [r'\-\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+)\n\n', r'\-\s([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'\sA\)\s(.+)\n\s\s', r'\sB\)\s(.+)\n\s\s', r'\sC\) (.+)\n\n', r'\n\d+?\.\s+([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+?)\n\n[^\d]', r'\n\d+?\.\s([ABC])\)'],
]


def claim_questions_universal(text, test_object):
    for dig_pattern in dig_patterns:
        list_of_questions = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[0], string=text)))
        list_of_answers1 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[1], string=text)))
        list_of_answers2 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[2], string=text)))
        list_of_answers3 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[3], string=text)))
        list_of_right_answers = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[4], string=text)))
        if len(list_of_questions) == len(list_of_answers1) == len(list_of_answers2) == len(list_of_answers3) == len(list_of_right_answers) and len(list_of_right_answers) != 0:
            test_object.save()
            for i in range(len(list_of_questions)):
                Question.objects.create(text=list_of_questions[i].strip(), 
                                        answer1=list_of_answers1[i].strip(), 
                                        answer2=list_of_answers2[i].strip(), 
                                        answer3=list_of_answers3[i].strip(), 
                                        right_answer = list_of_right_answers[i].strip(), 
                                        test=test_object)
            return None
    raise Exception
    
