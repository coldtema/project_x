import os
import requests
import json



def send_first_telegram_message(chat_id):
    token = os.getenv('BOT_API_KEY')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    keyboard = {
        "keyboard": [
            [{"text": "🔔 Вставить код"}],
            [{"text": "💬 Поддержка"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    payload = {
        'chat_id': chat_id,
        'text': ('Привет! Это бот для отправки уведомлений от сайта <a href="https://heavydrop.ru"><b>HeavyDrop</b></a>!\n\n'
                 'Если ты еще не зарегистрирован, то можешь это сделать по ссылке <a href="https://heavydrop.ru/accounts/signup/">Регистрация</a>.\n\n'
                 'Если ты уже зарегистрирован, то можешь перейти во вкладку <a href="https://heavydrop.ru/accounts/notification_edit/">Уведомления</a> и получить код доступа для отправки уведомлений через Telegram.\n\n'
                 'Если у тебя есть какие-то вопросы, то можешь написать в <a href=" https://heavydrop.ru/contacts">Тех. поддержку</a>.\n'
),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_message_to_paste_code(chat_id):
    token = os.getenv('BOT_API_KEY')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    keyboard = {
        "keyboard": [
            [{"text": "🔔 Вставить код"}],
            [{"text": "💬 Поддержка"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    payload = {
        'chat_id': chat_id,
        'text': ('Жду код для привязки вашего профиля! \n\n (6 цифр без пробелов и дополнительных знаков)'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)