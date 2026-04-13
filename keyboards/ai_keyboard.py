from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ai_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤖 AI Manager")]
    ],
    resize_keyboard=True
)