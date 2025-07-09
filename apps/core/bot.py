import os
import requests



def send_first_telegram_message(chat_id):
    token = os.getenv('BOT_API_KEY')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': ('Привет! Это бот для отправки уведомлений от сайта <a href="https://heavydrop.ru"><b>HeavyDrop</b></a>!.\n',
                 'Усли ты еще не зарегистрирован, то можешь это сделать по ссылке <a href="https://heavydrop.ru/accounts/signup/">Регистрация</a>.\n',
                 'Если ты уже зарегистрирован, то можешь перейти во вкладку <a href="https://heavydrop.ru/accounts/notification_edit/">Уведомления</a> и получить код доступа для отправки уведомлений через Telegram.\n',
                 'Если у тебя есть какие-то вопросы, то можешь написать в <a href=" https://heavydrop.ru/contacts">Тех. поддержку</a>.\n',
),
        'parse_mode': 'HTML'
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)