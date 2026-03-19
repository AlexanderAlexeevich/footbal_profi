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
    "что думаешь про спартак": "Спартак - чемпион!",
    "привет": "Привет, долбаеб!",
    "что думаешь про цска": "Да любой первоклассник скажет, что кони - гавно",
    "что думаешь про локомотив": "Локомотив - Москва",
    "что думаешь про зенит": "Бомжи вонючие",
    "что думаешь про краснодар": "Выскочки с недовинисиусом черножопым",
    "где колян": "Сдуло ветром",
    "что делает макс": "Только в рот берет и в жопу дает",
    "как играет цска": "Они ПЫТАЮТСЯ играть в атакующий футбол, а получается хуйня",
    "что важнее всего в футболе": "Входы в штрафную конечно же, тут даже говорить не о чем",
    "ты умеешь петь": "Да, но я знаю всего одну песню про Максима",
    "спой песню про Максима": "Вот и помер конь Максим \nДа и хуй остался с ним \nПоложили ему в рот \nНачал он сосать в заглооот \nОн бомжеватый был мужик \nОн на хую вертел шашлык",
    "максим как цска сыграл": "Ему не интересно",
    "алло": "Алло, это Володька!",
    "как локомотив сыграл": "Руденка все обосрал, еще этот комличенко по мячу не попадает...",
    "что думаешь про димона": "Мумбарик лысый",
    "что думаешь про макса": "Душный абьюзер, без негатива",
    "что думаешь про саню": "Хороший, добрый человек",
    "что думаешь про коляна": "Великий одноногий Абелардо, с порваным влагалищем",
    "как играет локомотив": "Да похуй, пока Галактионов тренер",
    "как играет спартак": "Как карта ляжет",
    "шансы спартака на чемпионство": "Ноль целых, хуй десятых",
    "шансы цска на чемпионство": "Если купят нападающего хорошего то поборятся",
    "шансы локомотива на чемпионство": "АХААХАХАХАХАХАХАХ, насмешил",
    "шансы цска в следующем матче": "Если забьют голов больше чем соперник то выйграют",
    "шансы локомотива в следующем матче": "Если пропустят не меньше чем соперник и при этом никто не забьет гол, то будет ничья",
    "шансы спартака в следующем матче": "100% победа, ставь хату"
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

def run_bot():
    asyncio.run(main())