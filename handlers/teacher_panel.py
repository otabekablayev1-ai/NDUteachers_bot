from aiogram import Router, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from data.config import RAHBARLAR
from database.db import get_teacher, save_manager_rating
from database.db import save_question
from keyboards.send_to_head import get_send_to_head_panel
from data.config import MANAGERS_BY_FACULTY

import asyncio


router = Router()


class TeacherSendFSM(StatesGroup):
    faculty = State()
    waiting_message = State()

# ===========================================================
# 1️⃣ RAHBARGA YOZISH BOSHLANISHI
# ===========================================================

@router.message(
    F.text == "📨 Rahbarlarga savol va murojaatlar yuborish",
    lambda m: get_teacher(m.from_user.id) is not None
)
async def start_send_message(message: Message, state: FSMContext):
    print("[TEACHER HANDLER TUSHDI]")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Prorektor (O‘quv ishlari bo‘yicha)"),
             KeyboardButton(text="Prorektor (Yoshlar masalalari va MMIB)")],

            [KeyboardButton(text="O'quv-uslubiy boshqarma (Departament)"),
             KeyboardButton(text="Registrator ofisi direktori")],

            [KeyboardButton(text="Ariza va shikoyatlar"),
             KeyboardButton(text="Magistratura bo‘limi")],

            [KeyboardButton(text="Buxgalteriya (Ustozlar)"),
             KeyboardButton(text="Buxgalteriya (Talabalar)")],

            [KeyboardButton(text="Xalqaro aloqalar va akademik mobillik boʻyicha xizmat koʻrsatish sektori menejeri")],

            [KeyboardButton(text="Aniq fanlar fakulteti"),
             KeyboardButton(text="Iqtisodiyot fakulteti")],

            [KeyboardButton(text="Maktabgacha va boshlang‘ich ta’lim fakulteti"),
             KeyboardButton(text="San’at va sport fakulteti")],

            [KeyboardButton(text="Tabiiy va tibbiyot fakulteti"),
             KeyboardButton(text="Tarix fakulteti")],

            [KeyboardButton(text="Tillar fakulteti")],
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🏫 Qaysi rahbar yoki fakultet menejeriga xabar yubormoqchisiz?",
        reply_markup=kb
    )
    await state.set_state(TeacherSendFSM.faculty)

# ===========================================================
# 2️⃣ FAKULTET TANLANGACH — SAVOL YOZISH
# ===========================================================
@router.message(TeacherSendFSM.faculty)
async def ask_question(message: Message, state: FSMContext):
    print("[TEACHER HANDLER TUSHDI]")
    faculty = message.text.strip()
    await state.update_data(faculty=faculty)

    if "fakulteti" in faculty.lower():
        msg = f"✏️ Iltimos, o‘z savolingizni yozing.\n\nSizning xabaringiz {faculty} menejeriga yuboriladi."
    else:
        msg = f"✏️ Iltimos, o‘z savolingizni yozing.\n\nSizning xabaringiz “{faculty}” ga yuboriladi."

    await message.answer(msg, reply_markup=ReplyKeyboardRemove())
    await state.set_state(TeacherSendFSM.waiting_message)

# ===========================================================
# 3️⃣ O‘QITUVCHI / TYUTOR — RAHBARGA SAVOL YUBORISH
# ===========================================================
@router.message(TeacherSendFSM.waiting_message, F.text | F.photo | F.video | F.document)
async def send_to_head(message: Message, state: FSMContext):
    print("[TEACHER HANDLER TUSHDI]")
    data = await state.get_data()
    faculty = data.get("faculty")

    # 🔹 TALABA ma’lumotini students jadvalidan olamiz
    sender = get_teacher(message.from_user.id)

    if not sender:
        print("[DEBUG] TEACHER topilmadi. ID:", message.from_user.id)
        await message.answer("⚠️ Avval ro‘yxatdan o‘ting.")
        await state.clear()
        return
    else:
        print("[DEBUG] TEACHER topildi:", sender)

    # student tuple tartibi – sizdagi db.py ga moslashgan variant:
    # (user_id, fio, phone, faculty, edu_type, edu_form, course, student_group, passport, created_at)
    fio = sender[1] or message.from_user.full_name
    fakultet = sender[3] or "Noma’lum"
    phone = sender[2] or "Noma’lum"

    # ============================
    #   QABUL QILUVCHI RAHBARLAR
    # ============================
    from data.config import MANAGERS_BY_FACULTY, RAHBARLAR, normalize_faculty

    faculty_raw = data.get("faculty")
    faculty = normalize_faculty(faculty_raw)

    recipients = []

    # 1️⃣ AVVAL — FAKULTET MENEJERI (O‘QITUVCHI / TYUTOR)
    fac = MANAGERS_BY_FACULTY.get(faculty)
    if fac:
        recipients = fac.get("teacher", [])

    # 2️⃣ AGAR YO‘Q BO‘LSA — UMUMIY RAHBARLAR
    if not recipients:
        for ids in RAHBARLAR.values():
            recipients.extend(ids)

    # ============================
    #   RAHBARGA YUBORILADIGAN XABAR
    # ============================
    from database.db import save_question

    # ...
    qid = save_question(
        sender_id=message.from_user.id,
        faculty=faculty,
        message_text=message.text,
        fio=fio
    )

    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✉️ Javob yozish",
            callback_data=f"reply_q_{qid}"
        )]
    ])

    info_text = (
        f"🎓 <b>{faculty}</b>ga yangi savol:\n\n"
        f"<b>F.I.Sh:</b> {fio}\n"
        f"<b>Telefon:</b> {phone}\n"
        f"<b>Fakultet:</b> {fakultet}\n\n"
    )

    sent = 0
    for head_id in recipients:
        try:
            if message.text:
                await message.bot.send_message(
                    head_id,
                    info_text + f"<b>Savol matni:</b>\n{message.text}",
                    parse_mode="HTML",
                    reply_markup=reply_kb
                )
            elif message.document:
                await message.bot.send_document(
                    head_id,
                    message.document.file_id,
                    caption=info_text + f"<b>Fayl:</b> {message.document.file_name}",
                    parse_mode="HTML",
                    reply_markup=reply_kb
                )
            elif message.photo:
                await message.bot.send_photo(
                    head_id,
                    message.photo[-1].file_id,
                    caption=info_text + "<b>Rasm yuborildi.</b>",
                    parse_mode="HTML",
                    reply_markup=reply_kb
                )
            elif message.video:
                await message.bot.send_video(
                    head_id,
                    message.video.file_id,
                    caption=info_text + "<b>Video yuborildi.</b>",
                    parse_mode="HTML",
                    reply_markup=reply_kb
                )
            sent += 1
            await asyncio.sleep(0.2)
        except Exception as e:
            print(f"[TEACHER_PANEL] Xabar yuborishda xatolik: {e}")

    if "fakulteti" in faculty.lower():
        conf_text = f"✅ Savolingiz {faculty} menejeriga yuborildi."
    else:
        conf_text = f"✅ Savolingiz “{faculty}” rahbariga yuborildi."

    await message.answer(conf_text)
    await state.clear()
