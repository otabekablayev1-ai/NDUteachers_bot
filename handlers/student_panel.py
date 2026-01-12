# student_panel.py to'liq
import asyncio
from aiogram import Router, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from data.config import MANAGERS_BY_FACULTY, RAHBARLAR
from database.db import get_student, save_question

router = Router()


class StudentSendFSM(StatesGroup):
    faculty = State()
    waiting_message = State()


# ===========================================================
# 1️⃣ TALABA — RAHBARGA YOZISH BOSHLANISHI
# ===========================================================
@router.message(
    F.text == "📨 Rahbarlarga savol va murojaatlar yozish",
    lambda m: get_student(m.from_user.id) is not None
)
async def start_student_send_message(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Prorektor (O‘quv ishlari bo‘yicha)"),
             KeyboardButton(text="Prorektor (Yoshlar masalalari va MMIB)")],

            [KeyboardButton(text="O'quv-uslubiy boshqarma (Departament)"),
             KeyboardButton(text="Registrator ofisi direktori")],

            [KeyboardButton(text="Ariza va shikoyatlar"),
             KeyboardButton(text="Magistratura bo‘limi")],

            [KeyboardButton(text="Buxgalteriya (Talabalar)")],

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
    await state.set_state(StudentSendFSM.faculty)


# ===========================================================
# 2️⃣ FAKULTET TANLANGACH — SAVOL YOZISH
# ===========================================================
@router.message(StudentSendFSM.faculty)
async def ask_question(message: Message, state: FSMContext):
    faculty = message.text.strip()
    await state.update_data(faculty=faculty)

    if "fakulteti" in faculty.lower():
        msg = f"✏️ Iltimos, savolingizni yozing.\n\nXabaringiz {faculty} menejeriga yuboriladi."
    else:
        msg = f"✏️ Iltimos, savolingizni yozing.\n\nXabaringiz “{faculty}” rahbariga yuboriladi."

    await message.answer(msg, reply_markup=ReplyKeyboardRemove())
    await state.set_state(StudentSendFSM.waiting_message)


def normalize_faculty(name: str | None) -> str:
    if not name:
        return "Noma'lum"
    return " ".join(name.strip().split())


def _extract_student_fields(student_obj, fallback_full_name: str):
    """
    get_student() qaytaradigan narsa ORM obyekt ham bo'lishi mumkin,
    tuple/list ham bo'lishi mumkin. Ikkalasiga ham mos ishlaydi.
    """
    fio = None
    phone = None
    faculty = None

    # ORM bo'lsa
    if hasattr(student_obj, "__dict__"):
        fio = getattr(student_obj, "fio", None)
        phone = getattr(student_obj, "phone", None)
        faculty = getattr(student_obj, "faculty", None)

    # tuple/list bo'lsa: (user_id, fio, phone, faculty, ...)
    if (fio is None or phone is None or faculty is None) and isinstance(student_obj, (list, tuple)):
        if len(student_obj) > 1 and fio is None:
            fio = student_obj[1]
        if len(student_obj) > 2 and phone is None:
            phone = student_obj[2]
        if len(student_obj) > 3 and faculty is None:
            faculty = student_obj[3]

    fio = fio or fallback_full_name
    phone = phone or "Noma’lum"
    faculty = faculty or "Noma’lum"
    return fio, phone, faculty


# ===========================================================
# 3️⃣ TALABA — RAHBARGA SAVOL YUBORISH
# ===========================================================
@router.message(StudentSendFSM.waiting_message, F.text | F.photo | F.video | F.document)
async def send_to_head(message: Message, state: FSMContext):
    print("[STUDENT SEND] handler ishladi")

    # 🔴 MUHIM: data ENG BOSHIDA olinadi
    data = await state.get_data()

    faculty_raw = data.get("faculty")
    faculty = normalize_faculty(faculty_raw)

    print("==== SEND TO HEAD DEBUG (STUDENT) ====")
    print("RAW faculty:", faculty_raw)
    print("NORMALIZED faculty:", faculty)
    print("MANAGERS_BY_FACULTY KEYS:", list(MANAGERS_BY_FACULTY.keys()))

    student = get_student(message.from_user.id)
    if not student:
        await message.answer("⚠️ Avval ro‘yxatdan o‘ting.")
        await state.clear()
        return

    fio, phone, student_faculty = _extract_student_fields(student, message.from_user.full_name)

    # ============================
    # RAHBARLARNI ANIQLASH
    # ============================
    recipients = []

    # faculty nomini keys bilan aniq moslab qidiramiz (teacher_panel dagidek)
    for key, value in MANAGERS_BY_FACULTY.items():
        if key.lower().strip() == faculty.lower().strip():
            recipients = value.get("student", []) or []
            break

    # topilmasa umumiy rahbarlar
    if not recipients:
        for ids in RAHBARLAR.values():
            recipients.extend(ids)

    # dublikatni olib tashlash
    recipients = list(set(recipients))
    print("[DEBUG] FINAL RECIPIENTS:", recipients)

    if not recipients:
        await message.answer("❌ Rahbar topilmadi.")
        await state.clear()
        return

    # ============================
    # SAVOLNI DB GA SAQLASH
    # ============================
    msg_text_for_db = message.text if message.text else "[FAYL]"
    question_id = save_question(
        sender_id=message.from_user.id,
        sender_role="student",  # 🔥 MUHIM
        faculty=faculty,
        message_text=msg_text_for_db,
        fio=fio
    )

    if not question_id:
        await message.answer("❌ Savolni saqlashda xatolik. Administrator bilan bog‘laning.")
        await state.clear()
        return

    # ============================
    # RAHBARGA YUBORISH
    # ============================
    info_text = (
        f"📩 <b>Yangi savol (TALABA)</b>\n\n"
        f"👤 <b>{fio}</b>\n"
        f"📞 {phone}\n"
        f"🏫 {faculty}\n\n"
    )

    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Javob yozish", callback_data=f"reply_{question_id}")]
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
            print("[STUDENT SEND ERROR]", e, "HEAD_ID:", head_id)

    # ============================
    # TALABAGA TASDIQ
    # ============================
    if sent > 0:
        await message.answer("✅ Savolingiz rahbarga yuborildi.")
    else:
        await message.answer("⚠️ Savol saqlandi, lekin rahbarga yuborilmadi. Administratorga murojaat qiling.")

    await state.clear()
