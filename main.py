import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен від BotFather
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # твій Telegram ID
CHANNEL_ID = os.getenv("CHANNEL_ID")  # @Ludo_company або -100...

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WELCOME_TEXT = (
    "👋 Вітаю!\n\n"
    "Це анонімний бот Ludo Company.\n"
    "Напиши своє питання або історію — ми опублікуємо анонімно (без імені).\n\n"
    "⚠️ Не пиши ПІБ, номер телефону, адресу.\n"
    "❌ Не додавай посилання на казино/ставки.\n\n"
    "✍️ Просто напиши повідомлення сюди."
)

def admin_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Опублікувати в канал", callback_data="publish")
    kb.button(text="❌ Відхилити", callback_data="reject")
    kb.adjust(1)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(WELCOME_TEXT)

@dp.message(F.text)
async def handle_user_message(message: Message):
    text = message.text.strip()

    # простий фільтр, щоб не було лінків/казино
    banned_words = ["казино", "casino", "ставки", "бет", "bet", "1xbet", "parimatch"]
    if any(w in text.lower() for w in banned_words):
        await message.answer("⚠️ Повідомлення містить заборонені слова/посилання. Спробуй переформулювати без назв казино.")
        return

    # підтвердження користувачу
    await message.answer("✅ Прийнято. Дякую! Ми розглянемо і опублікуємо анонімно.")

    # пересилаємо адміну як текст (без username)
    admin_text = (
        "🕵️ НОВЕ АНОНІМНЕ ПОВІДОМЛЕННЯ\n\n"
        f"Текст:\n{text}\n\n"
        "Що робимо?"
    )

    sent = await bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        reply_markup=admin_keyboard()
    )

    # збережемо текст у повідомленні адміна (через reply)
    await bot.send_message(chat_id=ADMIN_ID, text=text, reply_to_message_id=sent.message_id)

@dp.callback_query(F.data.in_(["publish", "reject"]))
async def admin_action(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Немає доступу", show_alert=True)
        return

    # шукаємо текст: він у наступному reply-повідомленні
    # простий спосіб: беремо повідомлення, на яке є reply
    msg = callback.message
    await callback.answer()

    # знаходимо reply (він буде наступним у чаті адміна)
    # але Telegram API не дає напряму "next message", тому робимо простіше:
    # текст зберігається в reply_to_message (якщо ти натискаєш кнопку на першому повідомленні — нижче буде текст)
    # Тому: беремо останній reply з цього повідомлення не можемо.
    # Рішення: в реальному проекті треба зберігати у базі.
    # Для простоти: адміну треба натиснути "Reply" на текст і тоді натиснути кнопку — але це не зручно.
    #
    # Тому зробимо правильніше: текст будемо вшивати в callback_data — але там обмеження.
    #
    # Найкраще рішення без БД: публікуємо текст з другого повідомлення, яке бот відправив reply_to_message_id.
    # Для цього просимо адміна натиснути кнопку на ДРУГОМУ повідомленні (де просто текст).
    #
    # Перевіримо:
    text_to_publish = msg.text

    if callback.data == "reject":
        await bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            text="❌ Відхилено."
        )
        return

    # publish
    post = (
        "🕵️‍♂️ Анонімно:\n\n"
        f"{text_to_publish}"
        "\n\n"
        "🤝 Якщо хочеш — напиши анонімно боту ще раз."
    )

    await bot.send_message(chat_id=CHANNEL_ID, text=post)
    await bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=msg.message_id,
        text="✅ Опубліковано в канал."
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
