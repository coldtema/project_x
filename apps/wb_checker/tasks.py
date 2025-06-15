from celery import Celery

app = Celery(main='task', broker='redis://localhost:6379/0')


@app.task
def add(x, y):
    return x + y


result = add.delay(4, 6)

print('hello')

print(result.get())

print(result.status)