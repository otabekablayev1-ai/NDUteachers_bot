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
from aiogram.types import CallbackQuery
from data.config import MANAGERS_BY_FACULTY, RAHBARLAR
from database.db import get_student, save_question
from database.db import save_question
from database.utils import mark_user_inactive
router = Router()


class StudentSendFSM(StatesGroup):
    faculty = State()
    waiting_message = State()


# ===========================================================
# 1️⃣ TALABA — RAHBARGA YOZISH BOSHLANISHI
# ===========================================================
@router.message(F.text == "📨 Rahbarlarga savol va murojaatlar yozish")
async def start_student_send_message(message: Message, state: FSMContext):

    student = await get_student(message.from_user.id)
    if not student:
        return  # talaba bo‘lmasa hech narsa qilmaymiz

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Rektorat")],
            [KeyboardButton(text="Prorektor (O‘quv ishlari bo‘yicha)"),
             KeyboardButton(text="Prorektor (Yoshlar masalalari va MMIB)")],

            [KeyboardButton(text="O'quv-uslubiy boshqarma (Departament)"),
             KeyboardButton(text="Registrator ofisi direktori")],

            [KeyboardButton(text="Ariza va shikoyatlar"),
             KeyboardButton(text="Magistratura bo‘limi")],

            [KeyboardButton(text="Stipendiya va Yotoqxona")],

            [KeyboardButton(text="Xalqaro aloqalar va akademik mobillik boʻyicha xizmat koʻrsatish sektori menejeri")],

            #[KeyboardButton(text="Aniq fanlar fakulteti"),
             #KeyboardButton(text="Iqtisodiyot fakulteti")],

            #[KeyboardButton(text="Maktabgacha va boshlang‘ich ta’lim fakulteti"),
             #KeyboardButton(text="San’at va sport fakulteti")],

            #[KeyboardButton(text="Tabiiy fanlar va tibbiyot fakulteti"),
             #KeyboardButton(text="Tarix fakulteti")],

            #[KeyboardButton(text="Tillar fakulteti")],

            #[KeyboardButton(text="O‘zbek filologiyasi fakulteti"),
             #KeyboardButton(text="Tibbiyot fakulteti")],
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

# =========================
# 🔔 REMINDER FUNKSIYA
# =========================
async def remind_manager(bot, manager_id):
    print("⏰ REMINDER STARTED:", manager_id)

    await asyncio.sleep(30)

    print("📩 REMINDER YUBORILYAPTI:", manager_id)

    try:
        await bot.send_message(
            manager_id,
            "⏰ Sizda javob berilmagan savol bor!\n\n"
            "Iltimos tekshiring 👇"
        )
    except Exception as e:
        print("REMINDER ERROR:", e)

# ===========================================================
# 3️⃣ TALABA — RAHBARGA SAVOL YUBORISH
# ===========================================================
@router.message(StudentSendFSM.waiting_message, F.text | F.photo | F.video | F.document)
async def send_to_head(message: Message, state: FSMContext):
    print("[STUDENT SEND] handler ishladi")

    data = await state.get_data()
    selected_manager = data.get("selected_manager")

    student = await get_student(message.from_user.id)
    if not student:
        await message.answer("⚠️ Avval ro‘yxatdan o‘ting.")
        await state.clear()
        return

    # ✅ Fakultetni state dan emas, student jadvalidan olamiz
    faculty = student.faculty

    print("==== SEND TO HEAD DEBUG (STUDENT) ====")
    print("STUDENT FACULTY:", faculty)
    print("MANAGERS_BY_FACULTY KEYS:", list(MANAGERS_BY_FACULTY.keys()))

    fio, phone, student_faculty = _extract_student_fields(
        student,
        message.from_user.full_name
    )

    # ============================
    # RAHBAR / MENEJERNI ANIQLASH
    # ============================

    if selected_manager:
        recipients = [selected_manager]
    else:
        recipients = []

        for key, value in MANAGERS_BY_FACULTY.items():
            if key.lower().strip() == faculty.lower().strip():
                recipients = value.get("student", []) or []
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
    msg_text_for_db = message.text if message.text else "[FAYL]"

    question_id = None

    for head_id in recipients:
        q_id = await save_question(
            sender_id=message.from_user.id,
            sender_role="student",
            faculty=faculty,
            message_text=msg_text_for_db,
            fio=fio,
            manager_id=head_id
        )

        if not question_id:
            question_id = q_id

    if not question_id:
        await message.answer(
            "❌ Savolni saqlashda xatolik. Administrator bilan bog‘laning."
        )
        await state.clear()
        return

    # ============================
    # RAHBARGA YUBORISH
    # ============================

    info_text = (
        f"📩 <b>Yangi savol (TALABA)</b>\n\n"
        f"👤 <b>{student.fio or 'Noma’lum'}</b>\n"
        f"📞 {student.phone or 'Noma’lum'}\n"
        f"🏛 Fakultet: {student.faculty or 'Noma’lum'}\n"
        f"🎓 Ta’lim turi: {student.edu_type or 'Noma’lum'}\n"
        f"🕒 Ta’lim shakli: {student.edu_form or 'Noma’lum'}\n"
        f"📚 Kurs: {student.course or 'Noma’lum'}\n"
        f"👥 Guruh: {student.student_group or 'Noma’lum'}\n"
        f"🪪 Passport: {student.passport or 'Noma’lum'}\n\n"
    )

    sent = 0

    for head_id in recipients:
        try:
            reply_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✉️ Javob yozish",
                            callback_data=f"reply_{question_id}"
                        )
                    ]
                ]
            )

            if message.text:
                sent_msg = await message.bot.send_message(
                    head_id,
                    "🚨 <b>YANGI SAVOL KELDI!</b>\n\n" +
                    info_text +
                    f"<b>Savol:</b>\n{message.text}",
                    parse_mode="HTML",
                    reply_markup=reply_kb,
                    disable_notification=False  # 🔥 MUHIM
                )

                # 🔥 PIN QILAMIZ (KO‘RINISHI UCHUN)
                try:
                    await message.bot.pin_chat_message(
                        chat_id=head_id,
                        message_id=sent_msg.message_id
                    )
                except:
                    pass

                sent_msg = await message.bot.send_document(
                    head_id,
                    message.document.file_id,
                    caption="🚨 <b>YANGI SAVOL!</b>\n\n" + info_text,
                    reply_markup=reply_kb
                )

                try:
                    await message.bot.pin_chat_message(
                        chat_id=head_id,
                        message_id=sent_msg.message_id
                    )
                except:
                    pass

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
            print(f"[STUDENT SEND OK] HEAD_ID: {head_id}")

            # 🔥 REMINDER START
            asyncio.create_task(remind_manager(message.bot, head_id))

            await asyncio.sleep(0.2)

        except Exception as e:
            error_text = str(e)
            if "bot was blocked" in error_text:
                print(f"🚫 USER BLOCKED BOT: {head_id}")

                await mark_user_inactive(head_id)  # 🔥 SHU

            else:
                print(f"❌ SEND ERROR: {e} HEAD_ID: {head_id}")

    if sent > 0:
        await message.answer("✅ Savolingiz yuborildi.")
    else:
        await message.answer("❌ Savol menejerga yuborilmadi.")

@router.callback_query(F.data == "faculty_manager_send")
async def faculty_manager_send(call: CallbackQuery, state: FSMContext):
    print("🔥 BUTTON BOSILDI")  # 👈 TEST

    student = await get_student(call.from_user.id)

    if not student:
        await call.answer("❌ Talaba topilmadi", show_alert=True)
        return

    faculty = student.faculty

    from data.config import MANAGERS_BY_FACULTY

    manager_id = None

    for fac, roles in MANAGERS_BY_FACULTY.items():
        if fac.lower().strip() == faculty.lower().strip():
            manager_ids = roles.get("student", [])
            if manager_ids:
                manager_id = manager_ids[0]
            break

    if not manager_id:
        await call.answer("❌ Menejer topilmadi", show_alert=True)
        return

    await state.update_data(selected_manager=manager_id)

    await call.message.answer("✏️ Savolingizni yozing:")
    await state.set_state(StudentSendFSM.waiting_message)

    await call.answer()