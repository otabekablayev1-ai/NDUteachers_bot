from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_send_to_head_panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏫 Fakultet rahbariga yozish", callback_data="ask_faculty")],
            [InlineKeyboardButton(text="🏛 Umumiy rahbarlarga yozish", callback_data="ask_global")]
        ]
    )
