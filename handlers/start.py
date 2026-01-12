from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from data.config import RAHBARLAR, ADMINS
from database.db import (
    get_teacher,
    get_student,  # 🔥 MUHIM — shu qo‘shiladi!
)
from handlers.registration import start_registration

router = Router()

@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):   # 👈 state qo‘shildi
    print("DEBUG USER:", message.from_user.id)
    print("→ STUDENT:", get_student(message.from_user.id))
    print("→ TEACHER:", get_teacher(message.from_user.id))

    # ❗ HAR SAFAR /start bosilganda eski holatlarni tozalaymiz
    await state.clear()

    user_id = message.from_user.id
    full_name = message.from_user.full_name

    # ✅ ADMIN — darhol admin panelga
    if user_id in ADMINS:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📥 Ro‘yxat so‘rovlari")],
                [KeyboardButton(text="🏆 Menejerlar reytingi")],
                [KeyboardButton(text="📊 Statistika")],
                [KeyboardButton(text="📝 Savol–Javoblar (filter)")],
                [KeyboardButton(text="❌ Foydalanuvchini o‘chirish")],
                [KeyboardButton(text="📨 Xabar yuborish")],
                [KeyboardButton(text="📘 Buyruqlar")],
            ],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Assalomu alaykum, hurmatli admin!",
            reply_markup=kb
        )
        return

    # ==========================================
    # RAHBAR
    # ==========================================
    from data.config import MANAGERS_BY_FACULTY

    # 1) Bo‘lim rahbarlari (Prorektor, Registrator ...)
    for role_name, ids in RAHBARLAR.items():
        if user_id in ids:
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📥 Savollarni ko‘rish")],
                    [KeyboardButton(text="🏆 Menejerlar reytingi")],
                    [KeyboardButton(text="📨 Xabar yuborish")],
                    [KeyboardButton(text="📊 Statistika")],
                    [KeyboardButton(text="📘 Buyruqlar")],
                ],
                resize_keyboard=True
            )
            await message.answer(
                f"👋 Assalomu alaykum, <b>{role_name}</b>!",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return

    # 2) Fakultet mas'ullari (teacher manager + student manager)
    for fac_name, roles in MANAGERS_BY_FACULTY.items():
        if user_id in roles.get("teacher", []) or user_id in roles.get("student", []):
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📥 Savollarni ko‘rish")],
                    [KeyboardButton(text="🏆 Menejerlar reytingi")],
                    [KeyboardButton(text="📨 Xabar yuborish")],
                    [KeyboardButton(text="📊 Statistika")],
                    [KeyboardButton(text="📘 Buyruqlar")],
                ],
                resize_keyboard=True
            )
            await message.answer(
                f"👋 Assalomu alaykum, <b>{fac_name} masʼuli</b>!",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return

    # ==========================================
    # TALABA
    # ==========================================
    student = get_student(user_id)
    if student:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📨 Rahbarlarga savol va murojaatlar yozish")]],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Assalomu alaykum, hurmatli talaba <b>{student.fio}</b>!",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    # ==========================================
    # O‘QITUVCHI / TYUTOR
    # ==========================================
    teacher = get_teacher(user_id)
    if teacher:
        fio = teacher.fio or full_name
        role = (teacher.role or "").lower().strip()

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📨 Rahbarlarga savol va murojaatlar yuborish")]
            ],
            resize_keyboard=True
        )

        if role == "teacher":
            title = "o‘qituvchi"
        elif role == "tutor":
            title = "tyutor"
        else:
            title = "xodim"

        await message.answer(
            f"👋 Assalomu alaykum, hurmatli <b>{fio}</b>!\n"
            f"Siz {title} panelidasiz.",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    # YANGI FOYDALANUVCHI
    await start_registration(message, state)
