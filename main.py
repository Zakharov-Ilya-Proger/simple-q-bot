import json
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")
cred = credentials.Certificate(json.loads(firebase_credentials))
firebase_admin.initialize_app(cred)
db = firestore.client()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_instructions(language: str) -> str:
    instructions = {
        "ru-RU": (
            "Пожалуйста, отвечайте на вопросы, выбирая одну из следующих цифр:\n\n"
            "0 — Никогда\n"
            "1 — Несколько дней\n"
            "2 — Более половины дней\n"
            "3 — Почти каждый день\n\n"
            "Выберите цифру, которая лучше всего описывает ваше состояние за последние 2 недели."
        ),
        "en-US": (
            "Please answer the questions by choosing one of the following numbers:\n\n"
            "0 — Not at all\n"
            "1 — Several days\n"
            "2 — More than half the days\n"
            "3 — Nearly every day\n\n"
            "Choose the number that best describes your condition over the last 2 weeks."
        )
    }
    return instructions.get(language, instructions["ru-RU"])

# Списки вопросов на русском и английском
GAD7_QUESTIONS = {
    "ru-RU": [
        "Чувствовали ли вы нервозность, беспокойство или напряжение за последние 2 недели?",
        "Не могли ли вы остановить или контролировать беспокойство за последние 2 недели?",
        "Как часто за последние 2 недели вы чрезмерно беспокоились о разных вещах?",
        "Как часто за последние 2 недели вам было трудно расслабиться?",
        "Как часто за последние 2 недели вы были настолько беспокойны, что не могли усидеть на месте?",
        "Как часто за последние 2 недели вы легко раздражались или чувствовали раздражение?",
        "Как часто за последние 2 недели вы чувствовали страх, как будто может случиться что-то ужасное?"
    ],
    "en-US": [
        "Over the last 2 weeks, how often have you been bothered by feeling nervous, anxious, or on edge?",
        "Over the last 2 weeks, how often have you been bothered by not being able to stop or control worrying?",
        "Over the last 2 weeks, how often have you been bothered by worrying too much about different things?",
        "Over the last 2 weeks, how often have you been bothered by having trouble relaxing?",
        "Over the last 2 weeks, how often have you been bothered by being so restless that it's hard to sit still?",
        "Over the last 2 weeks, how often have you been bothered by becoming easily annoyed or irritable?",
        "Over the last 2 weeks, how often have you been bothered by feeling afraid as if something awful might happen?"
    ]
}

PHQ9_QUESTIONS = {
    "ru-RU": [
        "Как часто за последние 2 недели вас беспокоило плохое настроение, чувство подавленности или безнадежности?",
        "Как часто за последние 2 недели вас беспокоило снижение интереса или удовольствия от деятельности?",
        "Как часто за последние 2 недели у вас были проблемы со сном (трудности с засыпанием, частые пробуждения или, наоборот, слишком долгий сон)?",
        "Как часто за последние 2 недели вы чувствовали усталость или недостаток энергии?",
        "Как часто за последние 2 недели у вас был плохой аппетит или, наоборот, переедание?",
        "Как часто за последние 2 недели вы чувствовали себя плохим человеком или испытывали чувство вины?",
        "Как часто за последние 2 недели у вас были трудности с концентрацией внимания (например, при чтении или просмотре телевизора)?",
        "Как часто за последние 2 недели вы двигались или говорили так медленно, что это могли заметить другие? Или, наоборот, вы были настолько беспокойны, что постоянно двигались?",
        "Как часто за последние 2 недели у вас возникали мысли о том, что вам лучше умереть или причинить себе вред?"
    ],
    "en-US": [
        "Over the last 2 weeks, how often have you been bothered by little interest or pleasure in doing things?",
        "Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?",
        "Over the last 2 weeks, how often have you been bothered by trouble falling or staying asleep, or sleeping too much?",
        "Over the last 2 weeks, how often have you been bothered by feeling tired or having little energy?",
        "Over the last 2 weeks, how often have you been bothered by poor appetite or overeating?",
        "Over the last 2 weeks, how often have you been bothered by feeling bad about yourself, or that you are a failure, or have let yourself or your family down?",
        "Over the last 2 weeks, how often have you been bothered by trouble concentrating on things, such as reading the newspaper or watching television?",
        "Over the last 2 weeks, how often have you been bothered by moving or speaking so slowly that other people could have noticed? Or the opposite – being so fidgety or restless that you have been moving around a lot more than usual?",
        "Over the last 2 weeks, how often have you been bothered by thoughts that you would be better off dead or of hurting yourself in some way?"
    ]
}

def get_questions(language: str):
    return GAD7_QUESTIONS[language] + PHQ9_QUESTIONS[language]


def create_answer_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="0", callback_data="answer_0"),
        InlineKeyboardButton(text="1", callback_data="answer_1"),
        InlineKeyboardButton(text="2", callback_data="answer_2"),
        InlineKeyboardButton(text="3", callback_data="answer_3"),
    )
    return builder.as_markup()


@router.message(Command("start"))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="English", callback_data="lang_en-US"))
    builder.add(InlineKeyboardButton(text="Русский", callback_data="lang_ru-RU"))

    await message.answer("Выберите язык / Choose language:", reply_markup=builder.as_markup())


@router.callback_query(lambda call: call.data.startswith("lang_"))
async def handle_language(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    language = call.data.split('_')[1]

    db.collection('simple_user_sessions').document(user_id).set({
        "lang": language,
        "answers": [],
        "current_question": 0
    })

    await call.message.edit_text("Язык выбран. Начнем анкету? / Language selected. Start the questionnaire? /session")
    await call.answer()


@router.message(Command("session"))
async def start_session(message: types.Message):
    user_id = str(message.from_user.id)
    user_doc = db.collection('simple_user_sessions').document(user_id).get()

    if user_doc.exists:
        language = user_doc.to_dict().get("lang", "ru-RU")  # По умолчанию русский
        questions = get_questions(language)  # Получаем вопросы на выбранном языке

        # Отправляем пояснение перед началом анкеты
        instructions = get_instructions(language)
        await message.answer(instructions)
        user_data = user_doc.to_dict()


        # Сбрасываем текущие ответы и начинаем с первого вопроса
        db.collection('simple_user_sessions').document(user_id).update({
            "answers": [],
            "current_question": 0
        })
        await ask_next_question(message, user_data['lang'], 0)
    else:
        await message.answer("Пожалуйста, начните с команды /start")


@router.callback_query(lambda call: call.data.startswith("answer_"))
async def handle_answer(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    answer = int(call.data.split("_")[1])


    user_doc = db.collection('simple_user_sessions').document(user_id).get()
    if not user_doc.exists:
        await call.answer("Пожалуйста, начните с команды /start")
        return

    user_data = user_doc.to_dict()
    current_question = user_data.get("current_question", 0)
    answers = user_data.get("answers", [])


    answers.append(answer)
    db.collection('simple_user_sessions').document(user_id).update({
        "answers": answers,
        "current_question": current_question + 1
    })


    if current_question + 1 >= len(get_questions(language=user_data["lang"])):
        await bot.delete_message(chat_id=call.message.chat_id, message_id=call.message.message_id)
        await finish_session(user_id, answers)
    else:
        await bot.delete_message(chat_id=call.message.chat_id, message_id=call.message.message_id)
        await ask_next_question(call.message, user_data['lang'], current_question + 1)

    await call.answer()


async def finish_session(user_id: str, answers: list):

    anx_answers = answers[:7]
    dep_answers = answers[7:]


    anx_total = sum(anx_answers)
    dep_total = sum(dep_answers)


    session_result = {
        "user_id": user_id,
        "anxiety": "/".join(map(str, anx_answers)),
        "depression": "/".join(map(str, dep_answers)),
        "anx_total": anx_total,
        "dep_total": dep_total,
        "timestamp": datetime.now()
    }
    db.collection('sessions_results').add(session_result)


    db.collection('simple_user_sessions').document(user_id).update({
        "answers": [],
        "current_question": 0
    })


    user_doc = db.collection('simple_user_sessions').document(user_id).get()
    language = user_doc.to_dict().get("lang", "ru-RU")
    result_text = await result_anx_dep(anx_total, dep_total, language)
    await bot.send_message(user_id, result_text)


async def ask_next_question(message: types.Message, lang, question_index: int):
    question = get_questions(language=lang)[question_index]
    await message.answer(question, reply_markup=create_answer_keyboard())


async def result_anx_dep(anx_total: int, dep_total: int, language: str) -> str:
    if language == "en-US":
        # Градация для GAD-7 (тревожность)
        if anx_total <= 4:
            anx_level = "Minimal anxiety"
        elif anx_total <= 9:
            anx_level = "Mild anxiety"
        elif anx_total <= 14:
            anx_level = "Moderate anxiety"
        else:
            anx_level = "Severe anxiety"

        # Градация для PHQ-9 (депрессия)
        if dep_total <= 4:
            dep_level = "Minimal depression"
        elif dep_total <= 9:
            dep_level = "Mild depression"
        elif dep_total <= 14:
            dep_level = "Moderate depression"
        elif dep_total <= 19:
            dep_level = "Moderately severe depression"
        else:
            dep_level = "Severe depression"

        return (
            f"Your results:\n"
            f"GAD-7 (Anxiety): {anx_total} — {anx_level}\n"
            f"PHQ-9 (Depression): {dep_total} — {dep_level}"
        )
    else:
        # Градация для GAD-7 (тревожность)
        if anx_total <= 4:
            anx_level = "Минимальный уровень тревожности"
        elif anx_total <= 9:
            anx_level = "Лёгкая тревожность"
        elif anx_total <= 14:
            anx_level = "Умеренная тревожность"
        else:
            anx_level = "Тяжёлая тревожность"

        # Градация для PHQ-9 (депрессия)
        if dep_total <= 4:
            dep_level = "Минимальный уровень депрессии"
        elif dep_total <= 9:
            dep_level = "Лёгкая депрессия"
        elif dep_total <= 14:
            dep_level = "Умеренная депрессия"
        elif dep_total <= 19:
            dep_level = "Умеренно тяжёлая депрессия"
        else:
            dep_level = "Тяжёлая депрессия"

        return (
            f"Ваши результаты:\n"
            f"GAD-7 (Тревожность): {anx_total} — {anx_level}\n"
            f"PHQ-9 (Депрессия): {dep_total} — {dep_level}"
        )

if __name__ == "__main__":
    dp.run_polling(bot, skip_updates=True)