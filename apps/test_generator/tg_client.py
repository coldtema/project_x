from pyrogram import filters
import time
import os

import asyncio
from pyrogram import Client
from apps.test_generator import question_digger

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME')


models_dict = {
        '@GPTChatRBot': question_digger.claim_questions_universal,
        '@kun4sun_bot': question_digger.claim_questions_universal,
        '@TypespaceBot': question_digger.claim_questions_universal,
        '@GPT4Telegrambot': question_digger.claim_questions_universal,
        # '@ChatGPT_General_Bot': question_digger.claim_questions_ChatGPT_General_Bot, - хрень
        '@RussiaChatGPTBot': question_digger.claim_questions_universal,
        '@gpt3_unlim_chatbot': question_digger.claim_questions_universal,
        '@chatsgpts_bot': question_digger.claim_questions_universal,
        '@GPT4Tbot': question_digger.claim_questions_universal,
        '@Chat_GPT4_rubot': question_digger.claim_questions_universal,
        '@pro_ai_bot': question_digger.claim_questions_universal, #оочень мало запросов
    }


async def send_and_wait_for_reply(text, model):
    response = asyncio.Future()  # Будет хранить ответ

    async with Client(SESSION_NAME, API_ID, API_HASH) as app:
        sent_message = await app.send_message(model, text)

        # Обработчик ответа
        @app.on_message(filters.chat(model) & filters.text)
        async def handle_reply(client, message):
            if not response.done():  # Проверяем, не получили ли мы уже ответ
                if len(message.text) > 200:
                    response.set_result(message.text)
        try:
            return await asyncio.wait_for(response, timeout=15)  # Ожидаем ответ до 15 секунд
        except asyncio.TimeoutError:
            return "Ответ не получен"

def send_message_and_get_reply(text, test_object, max_questions):
    which_chat = ''
    prompt = f'''Напиши, пожалуйста, тесты по этой теме, чтобы они были очень интересные:
формат - вопрос, и три варианта ответа + пронумеруй вопросы + не делай отступов ТОЛЬКО в начале строки, в остальных моментах ставь пробелы как обычно плюс отступай одну строку между тестами, 
ОБЯЗАТЕЛЬНО пронумеруй вопросы, варианты ответов должны быть под буквами A), B), C) - это английские буквы
в конце обязательно список правильных ответов в виде 1. A)
Вот текст: {text}'''[:4000]
    for model in models_dict.keys():
        print(f'работает {model}')
        which_chat = model
        result = asyncio.run(send_and_wait_for_reply(prompt, model))
        try:
            models_dict[model](result, test_object)
            print(f'{model} завершился корректно')
            if not max_questions:
                break
        except:
            print(f'модель {model} отвалилась')
            continue
    return which_chat