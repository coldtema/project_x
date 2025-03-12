from django.db import models

class Test(models.Model):
    name = models.CharField(max_length=200, verbose_name='Имя теста')
    text = models.TextField(verbose_name='Текст теста')
    added = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    best_result = models.IntegerField(default=0, verbose_name='Лучший результат')

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return f'{self.text[:20]}...'


class Question(models.Model):
    text = models.TextField(verbose_name='Текст вопроса')
    answer1 = models.CharField(max_length=2000, null=True, verbose_name='Ответ 1')
    answer2 = models.CharField(max_length=2000, null=True, verbose_name='Ответ 2')
    answer3 = models.CharField(max_length=2000, null=True, verbose_name='Ответ 3')
    right_answer = models.CharField(max_length=10, null=True, verbose_name='Правильный ответ')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Имя теста')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f'{' '.join(self.text.split()[:3])}...'
    