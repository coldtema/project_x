import re

dig_patterns = [
    [r'\d+\.\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+)\n\n', r'\n\d+?\.\s([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'\sA\)\s(.+)\n', r'\sB\)\s(.+)\n', r'\sB\)\s(.+)\n', r'\n\d+?\.\s([ABC])\)'],
    [r'\-\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+)\n\n', r'\-\s([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'\sA\)\s(.+)\n\s\s', r'\sB\)\s(.+)\n\s\s', r'\sC\) (.+)\n\n', r'\n\d+?\.\s+([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+?)\n\n[^\d]', r'\n\d+?\.\s([ABC])\)'],
    [r'\d+\.\s(.+[\:\?])', r'A\)\s(.+)\nB\)', r'B\)\s(.+)\nC\)', r'C\)\s(.+?)\n\n[^\d]', r'\n\d+?\.\s+([ABC])\)']
]

with open('D:/python_projects/django/project_x/apps/test_generator/tests/file1.txt', 'r', encoding='utf-8') as file:
    text = file.read()
    for dig_pattern in dig_patterns:
        list_of_questions = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[0], string=text)))
        list_of_answers1 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[1], string=text)))
        list_of_answers2 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[2], string=text)))
        list_of_answers3 = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[3], string=text)))
        list_of_right_answers = list(filter(lambda x: True if x != ' ' else False, re.findall(pattern=dig_pattern[4], string=text)))
        print(list_of_questions)
        print(list_of_answers1)
        print(list_of_answers2)
        print(list_of_answers3)
        print(list_of_right_answers)
        print(len(list_of_questions))
        print(len(list_of_answers1))
        print(len(list_of_answers2))
        print(len(list_of_answers3))
        print(len(list_of_right_answers))