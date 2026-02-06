from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def answer_button(q: dict, user_id: int, faculty: str):
    if q["answered"]:
        reply_btn = InlineKeyboardButton(
            text="✅ Javob berilgan",
            callback_data="none"
        )
    else:
        reply_btn = InlineKeyboardButton(
            text="✍️ Javob yozish",
            callback_data=f"answer:{user_id}:{faculty}"
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[[reply_btn]]
    )