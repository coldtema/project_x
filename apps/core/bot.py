import os
import requests
import json
import random



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
                 'Если у тебя есть какие-то вопросы, то можешь написать в <a href="https://heavydrop.ru/contacts">Тех. поддержку</a>.\n'
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
        'text': ('Жду код для привязки вашего профиля!\n\n(6 цифр без пробелов и дополнительных знаков)'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_success_of_pasting_code(chat_id):
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
        'text': ('Все прошло отлично! Теперь я буду отправлять все уведомления прямо в этот чат!'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_unsuccess_of_pasting_code(chat_id):
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
        'text': ('Что-то пошло не так... Попробуйте снова или напишите в <a href="https://heavydrop.ru/contacts/">поддержку</a>.'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)



def send_message_unsuccess_paste_code(chat_id):
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
        'text': ('Вы уже получаете уведомления через Telegram. Код больше не понадобится :)'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_message_of_deleting_connection(chat_id):
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
        'text': ('Вы успешно отписались от уведомлений через Telegram.\n\nЕсли Вам не понравилось пользоваться сервисом или у вас есть какие-либо вопросы, то обязательно напишите нам в <a href="https://heavydrop.ru/contacts/">поддержку</a>.'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_support_message(chat_id):
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
        'text': ('Контакты\n\nE-mail: heavydrop.ru@gmail.com\nTelegram of admin: @coldtema\n\nМы ответим в течение 24 часов в рабочие дни.'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_unknown_message(chat_id):
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
        'text': ('Я пока не знаю, что Вам на это ответить...'),
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)



def send_52_message(chat_id):
    token = os.getenv('BOT_API_KEY')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    fifty_two_list = os.getenv('fifty_two_list').split('\n')
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
        'text': fifty_two_list[random.randint(0, len(fifty_two_list)-1)],
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)




def send_notification_message(chat_id, text, photo_url=None):
    token = os.getenv('BOT_API_KEY')
    keyboard = {
        "keyboard": [
            [{"text": "🔔 Вставить код"}],
            [{"text": "💬 Поддержка"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    if not photo_url:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            "reply_markup": json.dumps(keyboard)
        }
    else:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
        'chat_id': chat_id,
        'photo': photo_url,
        'caption': text,
        'parse_mode': 'HTML',
        "reply_markup": json.dumps(keyboard)
        }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)