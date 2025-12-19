#heads.py to'liq
from aiogram import Router, F

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    Message, CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from data.config import MANAGERS_BY_FACULTY, RAHBARLAR
from database.db import (
    get_latest_questions,
    save_answer,
    mark_question_answered,
    save_manager_rating,
    user_already_rated,
    get_all_teachers,
    get_manager_rating_table,   # 🆕 shu qator
)
from database.db import get_filtered_students
from openpyxl import Workbook
from aiogram.types import FSInputFile
import os

from handlers.constants import FACULTIES  # talabalar uchun fakultetlar ro‘yxati
from database.db import get_question_by_id
from database.db import get_manager_rating_table as get_manager_rating
from database.db import get_teacher
router = Router()

# =========================
#   FSM HOLATLARI
# =========================
class ReplyFSM(StatesGroup):
    waiting = State()


class ReplyQuestionFSM(StatesGroup):  # DB orqali savol
    waiting = State()


class ReplyDirectFSM(StatesGroup):    # bevosita userga javob
    waiting = State()


class SendMSG(StatesGroup):
    # umumiy
    role = State()         # teacher / tutor / student / all
    faculty = State()
    department = State()
    fio = State()

    # talabalar uchun
    edu_type = State()     # bak / mag / all
    edu_form = State()     # Kunduzgi / Kechki / Sirtqi / ...
    stu_faculty = State()
    course = State()       # 1..5 / all
    group = State()
    student_fio = State()

    msg = State()          # yakuniy xabar


def is_faculty_manager(manager_id: int) -> bool:
    for fac in MANAGERS_BY_FACULTY.values():
        if manager_id in fac["teacher"] or manager_id in fac["student"]:
            return True
    return False

# =========================
#  Rahbar paneli klaviaturasi
# =========================
# def get_rahbar_panel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Savollarni ko‘rish")],
            [KeyboardButton(text="📨 Xabar yuborish")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🏆 Menejerlar reytingi")],
            [KeyboardButton(text="📘 Buyruqlar")],
        ],
        resize_keyboard=True
    )
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
#   /rahbar – faqat rahbarlar
# =========================
def get_global_managers():
    ids = []
    for lst in RAHBARLAR.values():
        ids.extend(lst)
    return list(set(ids))  # dublikatlar bo‘lmasin

def get_faculty_manager(role: str, faculty: str):
    """
    Talaba → student manager
    O‘qituvchi yoki Tyutor → teacher manager
    """
    fac = MANAGERS_BY_FACULTY.get(faculty)
    if not fac:
        return []

    if role == "Talaba":
        return fac.get("student", [])
    else:
        return fac.get("teacher", [])

# =========================
#   1) SAVOLLARNI KO‘RISH
# =========================
@router.message(F.text == "📥 Savollarni ko‘rish")
async def view_questions(message: Message):
    questions = get_latest_questions(limit=10)
    if not questions:
        await message.answer("📭 Hozircha yangi savollar mavjud emas.")
        return

    for q in questions:
        answered = q.get("answered")
        status = "✅ <b>Javob berilgan</b>" if answered else "⚠️ <b>Javob kutilmoqda</b>"

        text = (
            f"📩 <b>Yangi savol</b>\n\n"
            f"👤 <b>F.I.Sh:</b> {q.get('fio')}\n"
            f"🏫 <b>Fakultet:</b> {q.get('faculty')}\n"
            f"🕓 <b>Vaqt:</b> {q.get('created_at')}\n\n"
            f"❓ <b>Savol matni:</b>\n{q.get('message_text')}\n\n"
            f"{status}"
        )

        if not answered:
            reply_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✉️ Javob yozish",
                            callback_data=f"reply_{q['id']}"
                        )
                    ]
                ]
            )

        else:
            reply_kb = None

        await message.answer(text, parse_mode="HTML", reply_markup=reply_kb)

# =========================
#   JAVOB YOZISH
# =========================
@router.callback_query(F.data.startswith("reply_"))
async def start_reply(call: CallbackQuery, state: FSMContext):

    qid = int(call.data.split("_")[-1])

    q = get_question_by_id(qid)
    if not q:
        await call.answer("❗ Savol topilmadi.", show_alert=True)
        return

    # 🔑 STATE TO‘LDIRILADI (HAMMASI SHU YERDA)
    await state.update_data(
        question_id = qid,
        sender_id   = q["sender_id"],
    )

    await call.message.answer(
        f"✏️ <b>{q['fio']}</b> ga javob yozing:",
        parse_mode="HTML"
    )

    await state.set_state(ReplyFSM.waiting)
    await call.answer()

@router.message(ReplyFSM.waiting, F.text | F.document | F.photo | F.video)
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()

    question_id = data.get("question_id")
    sender_id = data.get("sender_id")
    manager_id = message.from_user.id

    from database.db import save_manager_name
    save_manager_name(manager_id, message.from_user.full_name)

    if not question_id or not sender_id:
        await message.answer("❗ Xatolik: savol topilmadi.")
        return

    # --- LOG ---
    print(f"[DEBUG] send_reply() manager_id={manager_id}")

    # 1️⃣ Javobni userga yuborish
    header = f"💬 <b>Rahbar javobi</b>\n👤 {message.from_user.full_name}\n\n"

    if message.text:
        await message.bot.send_message(sender_id, header + message.text, parse_mode="HTML")
        answer_text = message.text
    elif message.document:
        await message.bot.send_document(sender_id, message.document.file_id, caption=header)
        answer_text = "Hujjat"
    elif message.photo:
        await message.bot.send_photo(sender_id, message.photo[-1].file_id, caption=header)
        answer_text = "Rasm"
    elif message.video:
        await message.bot.send_video(sender_id, message.video.file_id, caption=header)
        answer_text = "Video"
    else:
        await message.answer("❗ Noma’lum format.")
        return

    # 2️⃣ DB ga yozish
    save_answer(question_id, manager_id, answer_text)
    mark_question_answered(question_id)
    from database.db import save_manager_name

    save_manager_name(
        user_id=manager_id,
        full_name=message.from_user.full_name
    )

    # 3️⃣ FAQAT FAKULTET MENEJERI BO‘LSA — BAHOLASH
    from data.config import is_manager_id

    if is_manager_id(manager_id):
        stars_kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="⭐", callback_data=f"rate_{question_id}_{manager_id}_1"),
                InlineKeyboardButton(text="⭐⭐", callback_data=f"rate_{question_id}_{manager_id}_2"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate_{question_id}_{manager_id}_3"),
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate_{question_id}_{manager_id}_4"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate_{question_id}_{manager_id}_5"),
            ]]
        )

        await message.bot.send_message(
            sender_id,
            "⭐ Iltimos, javobni baholang:",
            reply_markup=stars_kb
        )

    # 4️⃣ Rahbarga tasdiq
    await message.answer("✅ Javob foydalanuvchiga yuborildi.")

    await state.clear()

## =========================
#   JAVOBGA BAHO QO‘YISH
# =========================
@router.callback_query(F.data.startswith("rate_"))
async def handle_rating(call: CallbackQuery):
    _, qid, manager_id, rating = call.data.split("_")

    question_id = int(qid)
    manager_id = int(manager_id)
    rating = int(rating)
    user_id = call.from_user.id

    print(f"[DEBUG] Rating: manager={manager_id}, rating={rating}")

    # ✅ FAQAT HAQIQIY MENEJERLARNI TEKSHIRAMIZ
    is_real_manager = False
    for fac in MANAGERS_BY_FACULTY.values():
        if manager_id in fac.get("teacher", []) or manager_id in fac.get("student", []):
            is_real_manager = True
            break
    if not is_manager_id(manager_id):
        await call.answer("❌ Bu rahbar baholanmaydi", show_alert=True)
        return

    # ❌ 1 martadan ortiq baholashni bloklaymiz
    if user_already_rated(user_id, manager_id, question_id):
        await call.answer("✅ Siz allaqachon baho qo‘ygan ekansiz.", show_alert=True)
        return

    # ✅ Bahoni saqlaymiz
    save_manager_rating(user_id, manager_id, question_id, rating)

    # ✅ Foydalanuvchiga tasdiq
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("⭐ Bahoyingiz qabul qilindi!", show_alert=True)

    # ✅ FAQAT MENEJERGA XABAR BORADI
    await call.bot.send_message(
        manager_id,
        f"📊 Javobingizga berilgan reyting — ⭐ {rating} ball"
    )

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile
from aiogram import F
from aiogram.types import Message, CallbackQuery
import openpyxl
from openpyxl.utils import get_column_letter

@router.message(F.text == "🏆 Menejerlar reytingi")
async def show_managers_rating(message: Message):
    from database.db import get_manager_rating_table

    rows = get_manager_rating_table()
    if not rows:
        await message.answer("📭 Hozircha menejerlar reytingi mavjud emas.")
        return

    text = (
        "🏆 <b>Menejerlar reytingi</b>\n\n"
        "<pre>"
        "№  Menejer            Reyt  ✔️  ❌  Fakultet\n"
        "---------------------------------------------\n"
    )

    for i, r in enumerate(rows, 1):
        try:
            chat = await message.bot.get_chat(r["manager_id"])
            name = chat.full_name
        except:
            name = str(r["manager_id"])

        text += (
            f"{i:<2} "
            f"{name[:16]:<16} "
            f"{r['avg_rating']:<5} "
            f"{r['answered_count']:<3} "
            f"{r['unanswered_count']:<3} "
            f"{r['faculty']}\n"
        )

    text += "</pre>"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📤 Excelga eksport",
                callback_data="export_manager_rating_excel"
            )]
        ]
    )

    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "export_manager_rating_excel")
async def export_manager_rating_excel(call: CallbackQuery):
    from database.db import get_manager_rating_table
    import openpyxl

    rows = get_manager_rating_table()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Menejerlar reytingi"

    ws.append([
        "T/r", "Menejer", "Reyting", "Javob berilgan", "Javob berilmagan", "Fakultet"
    ])

    for i, r in enumerate(rows, 1):
        try:
            chat = await call.bot.get_chat(r["manager_id"])
            name = chat.full_name
        except:
            name = str(r["manager_id"])

        ws.append([
            i,
            name,
            r["avg_rating"],
            r["answered_count"],
            r["unanswered_count"],
            r["faculty"]
        ])

    path = "menejerlar_reytingi.xlsx"
    wb.save(path)

    await call.message.answer_document(
        FSInputFile(path),
        caption="📊 Menejerlar reytingi (Excel)"
    )
    await call.answer()

# ==============================
#   📊 UNIVERSITET SUPER STATISTIKASI
# ==============================
@router.message(F.text == "📊 Statistika")
async def full_stat(message: Message):

    # Semua ustoz va tyutorlar
    teachers = get_all_teachers()

    # Semua talabalar
    students = get_filtered_students({})  # barcha ma'lumotlarni olish
    # ============ 1) ROLLAR BO‘YICHA SANASH ============
    total_users = len(teachers) + len(students)

    teacher_count = sum(1 for t in teachers if t["role"] == "O‘qituvchi")
    tutor_count   = sum(1 for t in teachers if t["role"] == "Tyutor")
    student_count = len(students)

    # ============ 2) FAKULTETLAR BO‘YICHA SANASH ============
    faculty_stat = {}

    # O‘qituvchi + tyutorlar
    for t in teachers:
        faculty = t["faculty"] or "Noma’lum"
        faculty_stat[faculty] = faculty_stat.get(faculty, 0) + 1

    # Talabalar
    for s in students:
        faculty = s["faculty"] or "Noma’lum"
        faculty_stat[faculty] = faculty_stat.get(faculty, 0) + 1

    # ============ 3) MATN KO‘RINISHIDA YUBORISH ============
    text = (
        "<b>📊 UNIVERSITET UMUMIY STATISTIKASI</b>\n\n"
        f"👥 <b>Umumiy foydalanuvchilar:</b> {total_users} ta\n"
        f"👨‍🏫 O‘qituvchilar: {teacher_count} ta\n"
        f"🧑‍🏫 Tyutorlar: {tutor_count} ta\n"
        f"🎓 Talabalar: {student_count} ta\n\n"
        "<b>🏫 Fakultetlar bo‘yicha:</b>\n"
    )

    for fac, cnt in faculty_stat.items():
        text += f"• {fac}: {cnt} ta\n"

    await message.answer(text, parse_mode="HTML")

