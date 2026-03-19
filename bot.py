import asyncio
import logging
import os
import pytz
from datetime import datetime
from understatapi import UnderstatClient
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

def get_current_season():
    """Определяет текущий сезон для РПЛ (начинается летом)"""
    now = datetime.now()
    # Если сейчас август или позже - используем текущий год
    # Если январь-июль - прошлый год (сезон ещё не начался)
    if now.month >= 8:
        return str(now.year)
    else:
        return str(now.year - 1)

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
    "спой песню про Максима": """Вот и помер конь Максим 
    Да и хуй остался с ним 
    Положили ему в рот 
    Начал он сосать в заглооот 
    Он бомжеватый был мужик 
    Он на хую вертел шашлык""",
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

# Точные названия команд с сайта Understat
TEAMS = {
    "спартак": {"understat_name": "Spartak Moscow", "display_name": "Спартак"},
    "цска": {"understat_name": "CSKA Moscow", "display_name": "ЦСКА"},
    "локомотив": {"understat_name": "Lokomotiv Moscow", "display_name": "Локомотив"},
    "зенит": {"understat_name": "Zenit St. Petersburg", "display_name": "Зенит"},
    "краснодар": {"understat_name": "FC Krasnodar", "display_name": "Краснодар"},
    "динамо": {"understat_name": "Dinamo Moscow", "display_name": "Динамо"},
    "ростов": {"understat_name": "FC Rostov", "display_name": "Ростов"},
    "рубин": {"understat_name": "Rubin Kazan", "display_name": "Рубин"},
    "крылья советов": {"understat_name": "Krylya Sovetov Samara", "display_name": "Крылья Советов"},
    "ахмат": {"understat_name": "FK Akhmat", "display_name": "Ахмат"},
    "балтика": {"understat_name": "Baltika", "display_name": "Балтика"},
    "пари нн": {"understat_name": "Nizhny Novgorod", "display_name": "Пари НН"},
    "акрон": {"understat_name": "Akron", "display_name": "Акрон"},
    "оренбург": {"understat_name": "FC Orenburg", "display_name": "Оренбург"},
    "динамо махачкала": {"understat_name": "Dynamo Makhachkala", "display_name": "Динамо Махачкала"},
    "сочи": {"understat_name": "PFC Sochi", "display_name": "Сочи"},
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

async def get_next_match(team_key: str):
    team_info = TEAMS.get(team_key)
    if not team_info:
        return f"❌ Команда '{team_key}' не найдена. Доступны: спартак, цска, локомотив"

    understat_name = team_info["understat_name"]
    display_name = team_info["display_name"]

    try:
        with UnderstatClient() as understat:
            # Запрашиваем матчи РФПЛ за сезон 2025 (2025/2026)
            league_matches = understat.league(league="RFPL").get_match_data(season=get_current_season())

            # Отбираем будущие матчи с участием нашей команды
            upcoming = []
            for match in league_matches:
                if not match['isResult']:  # матч ещё не сыгран
                    if match['h']['title'] == understat_name or match['a']['title'] == understat_name:
                        # Добавляем объект datetime для сортировки
                        match['datetime_obj'] = datetime.fromisoformat(match['datetime'])
                        upcoming.append(match)

            if not upcoming:
                return f"⚽ У команды **{display_name}** пока нет запланированных матчей."

            # Самый ближайший матч
            next_match = min(upcoming, key=lambda x: x['datetime_obj'])

            # Определяем соперника и место
            if next_match['h']['title'] == understat_name:
                opponent = next_match['a']['title']
                location = "дома"
            else:
                opponent = next_match['h']['title']
                location = "в гостях"

            # Переводим время в московское
            msk_tz = pytz.timezone('Europe/Moscow')
            match_date_utc = next_match['datetime_obj'].replace(tzinfo=pytz.UTC)
            match_date_msk = match_date_utc.astimezone(msk_tz)
            date_str = match_date_msk.strftime("%d.%m.%Y в %H:%M")

            return (f"⚽ **Ближайший матч {display_name}**\n"
                    f"🏆 Российская Премьер-Лига\n"
                    f"🆚 {next_match['h']['title']} — {next_match['a']['title']}\n"
                    f"📅 {date_str} (мск)\n"
                    f"📍 {location}")

    except Exception as e:
        # Логируем ошибку (можно заменить на logging.error)
        print(f"Ошибка в get_next_match: {e}")
        return "❌ Не удалось получить расписание. Возможно, временные проблемы с сайтом статистики."

async def get_league_table():
    """
    Возвращает список команд с их статистикой, отсортированный по очкам и разнице мячей.
    Каждый элемент: dict с ключами name, played, wins, draws, losses, goals_for, goals_against, goal_diff, points
    """
    season = get_current_season()
    table_data = []
    try:
        with UnderstatClient() as understat:
            league_matches = understat.league(league="RFPL").get_match_data(season=season)
            teams_stats = {}
            for match in league_matches:
                if not match['isResult']:
                    continue
                home = match['h']['title']
                away = match['a']['title']
                goals_h = int(match['goals']['h'])
                goals_a = int(match['goals']['a'])

                # Хозяева
                if home not in teams_stats:
                    teams_stats[home] = {
                        "name": home, "played": 0, "wins": 0, "draws": 0, "losses": 0,
                        "goals_for": 0, "goals_against": 0, "points": 0
                    }
                teams_stats[home]["played"] += 1
                teams_stats[home]["goals_for"] += goals_h
                teams_stats[home]["goals_against"] += goals_a
                if goals_h > goals_a:
                    teams_stats[home]["wins"] += 1
                    teams_stats[home]["points"] += 3
                elif goals_h == goals_a:
                    teams_stats[home]["draws"] += 1
                    teams_stats[home]["points"] += 1
                else:
                    teams_stats[home]["losses"] += 1

                # Гости
                if away not in teams_stats:
                    teams_stats[away] = {
                        "name": away, "played": 0, "wins": 0, "draws": 0, "losses": 0,
                        "goals_for": 0, "goals_against": 0, "points": 0
                    }
                teams_stats[away]["played"] += 1
                teams_stats[away]["goals_for"] += goals_a
                teams_stats[away]["goals_against"] += goals_h
                if goals_a > goals_h:
                    teams_stats[away]["wins"] += 1
                    teams_stats[away]["points"] += 3
                elif goals_a == goals_h:
                    teams_stats[away]["draws"] += 1
                    teams_stats[away]["points"] += 1
                else:
                    teams_stats[away]["losses"] += 1

            for name, st in teams_stats.items():
                st["goal_diff"] = st["goals_for"] - st["goals_against"]
                table_data.append(st)

            table_data.sort(key=lambda x: (x["points"], x["goal_diff"]), reverse=True)
            return table_data
    except Exception as e:
        logging.error(f"Ошибка в get_league_table: {e}")
        return []
    
async def get_team_stats(team_key: str):
    """
    Возвращает статистику команды за текущий сезон (игры, очки, голы, xG и место в таблице)
    """
    team_info = TEAMS.get(team_key)
    if not team_info:
        return None, "❌ Команда не найдена"

    understat_name = team_info["understat_name"]
    display_name = team_info["display_name"]
    season = get_current_season()

    try:
        with UnderstatClient() as understat:
            league_matches = understat.league(league="RFPL").get_match_data(season=season)

            stats = {
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "xG_for": 0.0,
                "xG_against": 0.0,
                "points": 0,
                "team_name": display_name
            }

            for match in league_matches:
                is_home = (match['h']['title'] == understat_name)
                is_away = (match['a']['title'] == understat_name)

                if (is_home or is_away) and match['isResult']:
                    stats["played"] += 1

                    if is_home:
                        goals_for = int(match['goals']['h'])
                        goals_against = int(match['goals']['a'])
                        xG_for = float(match['xG']['h'])
                        xG_against = float(match['xG']['a'])
                    else:
                        goals_for = int(match['goals']['a'])
                        goals_against = int(match['goals']['h'])
                        xG_for = float(match['xG']['a'])
                        xG_against = float(match['xG']['h'])

                    stats["goals_for"] += goals_for
                    stats["goals_against"] += goals_against
                    stats["xG_for"] += xG_for
                    stats["xG_against"] += xG_against

                    if goals_for > goals_against:
                        stats["wins"] += 1
                        stats["points"] += 3
                    elif goals_for == goals_against:
                        stats["draws"] += 1
                        stats["points"] += 1
                    else:
                        stats["losses"] += 1

            stats["goal_diff"] = stats["goals_for"] - stats["goals_against"]
            stats["xG_diff"] = round(stats["xG_for"] - stats["xG_against"], 2)

            # Получаем позицию в таблице
            table = await get_league_table()
            position = None
            for i, t in enumerate(table, 1):
                # Ищем по английскому названию
                if t['name'] == understat_name:
                    position = i
                    break
            stats["position"] = position

            return stats, None

    except Exception as e:
        logging.error(f"Ошибка в get_team_stats для {team_key}: {e}")
        return None, "❌ Не удалось получить статистику"
    
# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Я футбольный эксперт.\n"
        "Я отвечаю на вопросы о футболе.\n\n"
        "📋 **Доступные команды:**\n"
        "/stats спартак — статистика команды\n"
        "/nextmatch спартак — ближайший матч\n"
        "/table — турнирная таблица РПЛ\n\n"
        "Попробуйте спросить моё мнение о своей любимой команде.",
        parse_mode="Markdown"
    )

@dp.message(Command("nextmatch"))
async def cmd_next_match(message: Message):
    # Разбираем аргументы команды
    args = message.text.split()
    if len(args) < 2:
        # Если команда без аргумента, показываем подсказку
        await message.answer(
            "❗ Укажите команду.\n"
            "Пример: /nextmatch спартак\n"
            "Доступные команды: спартак, цска, локомотив"
        )
        return

    team = args[1].lower()  # получаем название команды и приводим к нижнему регистру
    if team not in TEAMS:
        await message.answer(
            f"❌ Команда '{team}' не найдена.\n"
            f"Доступны: {', '.join(TEAMS.keys())}"
        )
        return

    # Отправляем статус "печатает", чтобы пользователь знал, что бот работает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Вызываем функцию получения расписания
    result = await get_next_match(team)
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        teams_list = ", ".join(TEAMS.keys())
        await message.answer(
            f"❗ Укажите команду.\n"
            f"Пример: /stats спартак\n\n"
            f"**Доступные команды:** {teams_list}",
            parse_mode="Markdown"
        )
        return

    team = args[1].lower()
    if team not in TEAMS:
        await message.answer(f"❌ Команда '{team}' не найдена.")
        return

    await message.bot.send_chat_action(message.chat.id, action="typing")

    stats, error = await get_team_stats(team)
    if error:
        await message.answer(error)
        return

    result = f"⚽ **Статистика {stats['team_name']}**\n\n"
    result += f"📅 Сыграно матчей: {stats['played']}\n"
    result += f"⭐ Очки: {stats['points']}\n"
    result += f"✅ Победы: {stats['wins']}\n"
    result += f"🤝 Ничьи: {stats['draws']}\n"
    result += f"❌ Поражения: {stats['losses']}\n"
    result += f"⚽ Забито: {stats['goals_for']}\n"
    result += f"🧤 Пропущено: {stats['goals_against']}\n"
    result += f"📊 Разница: {stats['goal_diff']:+d}\n"
    result += f"🎯 xG (за): {stats['xG_for']:.2f}\n"
    result += f"🎯 xG (против): {stats['xG_against']:.2f}\n"
    result += f"📈 xG разница: {stats['xG_diff']:+0.2f}\n"

    if stats.get('position'):
        result += f"\n🏆 **Место в таблице: {stats['position']}**"

    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("table"))
async def cmd_table(message: Message):
    await message.bot.send_chat_action(message.chat.id, action="typing")

    table = await get_league_table()
    if not table:
        await message.answer("❌ Не удалось получить турнирную таблицу.")
        return

    # Словарь для перевода английских названий в русские
    eng_to_rus = {v["understat_name"]: v["display_name"] for v in TEAMS.values()}

    result = "<b>🏆 Турнирная таблица РПЛ</b>\n\n"
    for i, team in enumerate(table, 1):
        # Определяем медальку для топ-3
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."

        name = eng_to_rus.get(team['name'], team['name'])
        result += f"{medal} <b>{name}</b>\n"
        result += f"   ⭐ {team['points']} очков | {team['played']} игр | {team['wins']}-{team['draws']}-{team['losses']}\n"
        result += f"   ⚽ {team['goals_for']}-{team['goals_against']}  (разница: {team['goal_diff']:+d})\n\n"

    result += "<i>Обновлено: автоматически</i>"

    await message.answer(result, parse_mode="HTML")

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
