from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ✏️ Javob yozish tugmasi (rahbar uchun)
def answer_button(user_id: int, faculty: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Javob yozish",
                    callback_data=f"answer:{user_id}:{faculty}"
                )
            ]
        ]
    )

if q["answered"]:
    reply_btn = InlineKeyboardButton(text="✅ Javob berilgan", callback_data="none")
else:
    reply_btn = InlineKeyboardButton(text="✏️ Javob yozish", callback_data=f"r

    reply_kb = InlineKeyboardMarkup(inline_keyboard=[[reply_btn]])
