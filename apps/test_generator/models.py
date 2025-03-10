from django.db import models

class Test(models.Model):
    name = models.CharField(max_length=200)
    text = models.TextField()
    added = models.DateTimeField(auto_now_add=True)
    best_result = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.text[:20]}...'


class Question(models.Model):
    text = models.TextField()
    answer1 = models.CharField(max_length=2000, null=True)
    answer2 = models.CharField(max_length=2000, null=True)
    answer3 = models.CharField(max_length=2000, null=True)
    right_answer = models.CharField(max_length=10, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)