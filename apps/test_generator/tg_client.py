from pyrogram import filters
import time
import os

import asyncio
from pyrogram import Client

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME')

async def send_and_wait_for_reply(text):
    response = asyncio.Future()  # Будет хранить ответ

    async with Client(SESSION_NAME, API_ID, API_HASH) as app:
        sent_message = await app.send_message('@GPT4Telegrambot', text)

        # Обработчик ответа
        @app.on_message(filters.chat("@GPT4Telegrambot") & filters.text)
        async def handle_reply(client, message):
            if not response.done():  # Проверяем, не получили ли мы уже ответ
                if len(message.text) > 69:
                    response.set_result(message.text)
        try:
            return await asyncio.wait_for(response, timeout=15)  # Ожидаем ответ до 15 секунд
        except asyncio.TimeoutError:
            return "Ответ не получен"

def send_message_and_get_reply(text):
    return asyncio.run(send_and_wait_for_reply(f'''Напиши, пожалуйста, тесты по этой теме, чтобы они были очень интересные:
формат - вопрос, и три варианта ответа
в конце обязательно список правильных ответов в виде 1. A)
Вот текст: {text}'''))