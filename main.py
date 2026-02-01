import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

pending = {}  # msg_id -> text


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привіт! Напиши повідомлення — я передам його адміну анонімно.\n\n"
        "⚠️ Не вказуй особисті дані (ім'я, номер, місто)."
    )


@dp.message(F.text)
async def handle_text(message: Message):
    if message.from_user.id == ADMIN_ID:
        return

    text = message.text.strip()
    if not text:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опублікувати", callback_data="pub"),
            InlineKeyboardButton(text="❌ Відхилити", callback_data="rej"),
        ]
    ])

    admin_msg = await bot.send_message(
        ADMIN_ID,
        f"📩 АНОНІМНЕ ПОВІДОМЛЕННЯ:\n\n{text}",
        reply_markup=kb
    )

    pending[admin_msg.message_id] = text
    await message.answer("Дякую! Повідомлення відправлено адміну 🙏")


@dp.callback_query(F.data.in_({"pub", "rej"}))
async def callbacks(call):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Недостатньо прав", show_alert=True)
        return

    text = pending.get(call.message.message_id)
    if not text:
        await call.answer("Немає даних", show_alert=True)
        return

    if call.data == "pub":
        await bot.send_message(CHANNEL_ID, f"🕊 Анонімно:\n\n{text}")
        await call.message.edit_text("✅ Опубліковано в канал.")
    else:
        await call.message.edit_text("❌ Відхилено.")

    pending.pop(call.message.message_id, None)
    await call.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
