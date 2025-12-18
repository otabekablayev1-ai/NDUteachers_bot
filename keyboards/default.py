from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 📱 Telefon raqamini yuborish uchun
share_phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📲 Kontaktni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# 👩‍🏫 O‘qituvchi paneli
teacher_panel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📨 Rahbarlarga savol va murojaatlar yuborish")],
    ],
    resize_keyboard=True
)

# 👩‍🏫 Talaba paneli
student_panel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📨 Rahbarlarga savol va murojaatlar yozish")],
    ],
    resize_keyboard=True
)

# 👨‍💼 Rahbar (admin) paneli
admin_panel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📨 Xabar yozish")],
        [KeyboardButton(text="🚫 Bekor qilish")]
    ],
    resize_keyboard=True
)
