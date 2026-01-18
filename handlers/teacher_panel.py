# teacher_panel.py TO'LIQ
import asyncio

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
    faculty = message.text.strip()
    await state.update_data(faculty=faculty)

    await message.answer(
        "✏️ Iltimos, savolingizni yozing.\n\n"
        "Xabaringiz fakultet rahbariga yuboriladi.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(TeacherSendFSM.waiting_message)

def normalize_faculty(name: str | None) -> str:
    if not name:
        return "Noma'lum"
    return " ".join(name.strip().split())

# ===========================================================
# 3️⃣ O‘QITUVCHI / TYUTOR — RAHBARGA SAVOL YUBORISH
# ===========================================================
@router.message(TeacherSendFSM.waiting_message, F.text | F.photo | F.video | F.document)
async def send_to_head(message: Message, state: FSMContext):
    print("[TEACHER SEND] handler ishladi")

    # 🔴 MUHIM: data ENG BOSHIDA olinadi
    data = await state.get_data()

    faculty_raw = data.get("faculty")
    faculty = normalize_faculty(faculty_raw)

    print("==== SEND TO HEAD DEBUG ====")
    print("RAW faculty:", faculty_raw)
    print("NORMALIZED faculty:", faculty)
    print("MANAGERS_BY_FACULTY KEYS:", list(MANAGERS_BY_FACULTY.keys()))

    teacher = get_teacher(message.from_user.id)
    if not teacher:
        await message.answer("⚠️ Avval ro‘yxatdan o‘ting.")
        await state.clear()
        return

    fio = teacher.fio or message.from_user.full_name
    phone = getattr(teacher, "phone", "Noma’lum")

    # ============================
    # RAHBARLARNI ANIQLASH
    # ============================
    recipients = []

    for key, value in MANAGERS_BY_FACULTY.items():
        if key.lower().strip() == faculty.lower().strip():
            recipients = value.get("teacher", [])
            break

    if not recipients:
        for ids in RAHBARLAR.values():
            recipients.extend(ids)

    recipients = list(set(recipients))
    print("[DEBUG] FINAL RECIPIENTS:", recipients)

    if not recipients:
        await message.answer("❌ Rahbar topilmadi.")
        await state.clear()
        return

    # ============================
    # SAVOLNI DB GA SAQLASH
    # ============================
    question_id = save_question(
        sender_id=message.from_user.id,
        sender_role="teacher",  # 🔥 MUHIM
        faculty=faculty,
        message_text=message.text if message.text else "[FAYL]",
        fio=fio
    )

    # ============================
    # RAHBARGA YUBORISH
    # ============================
    role_title = "TYUTOR" if teacher.role == "tutor" else "O‘QITUVCHI"

    info_text = (
        f"📩 <b>Yangi savol ({role_title})</b>\n\n"
        f"👤 <b>{teacher.fio}</b>\n"
        f"📞 {teacher.phone}\n"
        f"🏛 Fakultet: {teacher.faculty}\n"
        f"🧑‍💼 Rol: {teacher.role}\n\n"
    )

    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✉️ Javob yozish",
                callback_data=f"reply_{question_id}"
            )]
        ]
    )

    sent = 0

    for head_id in recipients:
        try:
            if message.text:
                await message.bot.send_message(
                    head_id,
                    info_text + f"<b>Savol:</b>\n{message.text}",
                    parse_mode="HTML",
                    reply_markup=reply_kb
                )
            elif message.document:
                await message.bot.send_document(
                    head_id,
                    message.document.file_id,
                    caption=info_text,
                    reply_markup=reply_kb
                )
            elif message.photo:
                await message.bot.send_photo(
                    head_id,
                    message.photo[-1].file_id,
                    caption=info_text,
                    reply_markup=reply_kb
                )
            elif message.video:
                await message.bot.send_video(
                    head_id,
                    message.video.file_id,
                    caption=info_text,
                    reply_markup=reply_kb
                )

            sent += 1
            await asyncio.sleep(0.2)

        except Exception as e:
            print("[SEND ERROR]", e, "HEAD_ID:", head_id)

    # ============================
    # O‘QITUVCHIGA TASDIQ
    # ============================
    if sent > 0:
        await message.answer("✅ Savolingiz rahbarga yuborildi.")
    else:
        await message.answer("⚠️ Savol yuborilmadi. Administratorga murojaat qiling.")

    await state.clear()
