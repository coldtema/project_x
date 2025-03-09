from pyrogram import filters
import time
import os

import asyncio
from pyrogram import Client

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME')

async def send_and_wait_for_reply(text):
    async with Client(SESSION_NAME, API_ID, API_HASH) as app:
        # Отправляем сообщение боту
        sent_message = await app.send_message('@GPT4Telegrambot', text)
        print(f"Отправлено: {sent_message.text}")

        # Запоминаем время отправки сообщения
        sent_time = time.time()
        time.sleep(2)
        # Ожидаем, пока появится новое сообщение от бота (после отправленного)
        async for message in app.get_chat_history('@GPT4Telegrambot', limit=1000):
            if message.date.timestamp() > sent_time:
                print(f"Ответ бота: {message.text}")
                return message.text

        return "Ответ не получен"

def send_message_and_get_reply(text):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    reply = loop.run_until_complete(send_and_wait_for_reply(text))
    loop.close()
    return reply