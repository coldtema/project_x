from django.db import models

class Test(models.Model):
    name = models.CharField(max_length=100)
    text = models.TextField()
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.text[:20]}...'


class Question(models.Model):
    text = models.TextField()
    test = models.ForeignKey(Test, on_delete=models.CASCADE)