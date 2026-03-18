import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
REMINDER_TEXT = os.getenv("REMINDER_TEXT", "ЦСКА - команда гондонов")  # текст по умолчанию

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN и CHAT_ID должны быть указаны в .env файле")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь ответов на ключевые слова
answers = {
    "кто чемпион": "Спартак, конечно!",
    "спартак": "Спартак - чемпион!",
    "привет": "Привет, болельщик!",
    "цска": "ЦСКА - команда гондонов",
    "локомотив": "Локомотив - Москва",
}

# Функция для отправки напоминания каждый час
async def scheduled_reminder():
    while True:
        now = datetime.now()
        # Вычисляем время до следующего часа
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        seconds_to_wait = (next_hour - now).total_seconds()
        await asyncio.sleep(seconds_to_wait)

        try:
            await bot.send_message(chat_id=CHAT_ID, text=REMINDER_TEXT)
            logging.info(f"Напоминание отправлено в {next_hour}")
        except Exception as e:
            logging.error(f"Ошибка отправки: {e}")

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Я футбольный эксперт.\n"
        "Я отвечаю на вопросы о футболе.\n"
        "Попробуйте спросить мое мнение о своей любимой команде."
    )

# Обработка всех текстовых сообщений (вопросов)
@dp.message()
async def handle_question(message: Message):
    text = message.text.lower()
    for keyword, reply in answers.items():
        if keyword in text:
            await message.reply(reply)
            return

async def main():
    # Запускаем задачу с напоминаниями
    asyncio.create_task(scheduled_reminder())
    # Запускаем приём сообщений
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())