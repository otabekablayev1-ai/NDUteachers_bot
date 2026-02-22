from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import reject_request
from aiogram import Router, types
from aiogram.filters import Command
from database.scripts import rebuild_students_search
from aiogram.types import (Message, KeyboardButton, FSInputFile)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import pandas as pd
import shutil
from database.db import move_request_to_main_tables
from data.config import ADMINS
from database.db import (
    get_pending_requests,
    find_teachers_by_name,
    fetch_answers_range,
    get_teacher,
)
from database.db import search_users_by_fio_or_id, delete_user_by_id

router = Router()

# =====================================================
# 🔐 ADMIN MENYU
# =====================================================
@router.message(F.text == "/admin")
async def admin_menu(message: Message):
    if message.from_user.id not in ADMINS:
        return

    # kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Ro‘yxat so‘rovlari")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏆 Menejerlar reytingi")],
            [KeyboardButton(text="📝 Savol–Javoblar (Excel)")],
            [KeyboardButton(text="🔍 Qidirish"), KeyboardButton(text="❌ Foydalanuvchini o‘chirish")],
            [KeyboardButton(text="📂 Backup (DB)")],
            [KeyboardButton(text="⬅️ Chiqish")],
        ],
        resize_keyboard=True

    await message.answer(
        "🔐 <b>Admin panel</b>:\nKerakli bo‘limni tanlang ⤵️",
        parse_mode="HTML"
    )


# =====================================================
# 📥 RO‘YXAT SO‘ROVLARI (O‘QITUVCHI / TYUTOR / TALABA)
# =====================================================

# ✅ So‘rovlarni ko‘rsatish (admin panel)
@router.message(F.text == "📥 Ro‘yxat so‘rovlari")
async def show_register_requests(message: Message):
    requests = get_pending_requests()

    if not requests:
        await message.answer("📭 Yangi ro‘yxatdan o‘tish so‘rovlari yo‘q.")
        return

    for req in requests:
        text = (
            "🆕 <b>Yangi ro‘yxatdan o‘tish so‘rovi</b>\n\n"
            f"👤 FIO: {req['fio']}\n"
            f"📞 Telefon: {req['phone']}\n"
            f"🏫 Fakultet: {req['faculty']}\n"
            f"🎓 Rol: {req['role']}\n"
            f"🆔 Telegram ID: <code>{req['user_id']}</code>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve_{req['user_id']}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_{req['user_id']}"
                )
            ]
        ])

        await message.answer(text, reply_markup=kb, parse_mode="HTML")

# ✅ TASDIQLASH
@router.callback_query(F.data.startswith("approve_"))
async def approve_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])

    ok = move_request_to_main_tables(user_id)

    if not ok:
        await call.answer(
            "⚠️ So‘rov topilmadi yoki allaqachon tasdiqlangan.",
            show_alert=True
        )
        return

    await call.message.edit_text("✅ Foydalanuvchi tasdiqlandi.")

    try:
        await call.bot.send_message(
            user_id,
            "📢 Assalomu alaykum, hurmatli foydalanuvchi! Navoiy Davlat Universitetining 'NDU_UniFront' botiga xush kelibsiz!\n\n"
            "Ro‘yxatdan o‘tish jarayoni <b>muvaffaqiyatli yakunlandi!</b>\n"
            "Siz Navoiy davlat universitetining rasmiy "
            "<a href='https://t.me/NDUnivers_EDU_bot'>https://t.me/NDUteachers_bot</a> ga a’zo bo‘ldingiz.\n\n"
            "Ushbu bot orqali Siz:\n"
            "• Registrator ofisi menejerlari bilan,\n"
            "• Universitet rahbariyati bilan\n"
            "masofaviy tarzda <b>tezkor va qulay muloqot</b> qilishingiz mumkin.\n\n"
            "📎 Shuningdek, Siz matnli xabar, PDF hujjatlar, JPEG rasmlar, videolar va boshqa turdagi fayllar ko‘rinishidagi "
            "savol va murojaatlaringizni ham yuborishingiz mumkin.\n\n"
            "🏛 Fakultet nomi ko‘rsatilgan tugmalar orqali — "
            "o‘sha fakultetga biriktirilgan menejerga yozishingiz,\n"
            "👤 Rahbarlar tugmalari orqali — fakultet yoki bo‘lim rahbarlariga murojaat qilishingiz mumkin.\n\n"
            "🤖 Ushbu bot Navoiy davlat universiteti Registrator ofisi menejeri "
            "<b>O. Ablayev</b> tomonidan ishlab chiqilgan.\n\n"
            "✅ Ma’lumotlaringiz tasdiqlandi! Endi botdan to‘liq foydalanishingiz mumkin.",
        )
    except:
        pass

    await call.answer()

# ❌ RAD ETISH
@router.callback_query(F.data.startswith("reject_"))
async def reject_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])

    ok = reject_request(user_id)

    if not ok:
        await call.answer("⚠️ So‘rov topilmadi.", show_alert=True)
        return

    await call.message.edit_text("❌ Rad etildi.")
    try:
        await call.bot.send_message(user_id, "❌ Ro‘yxatdan o‘tish so‘rovingiz rad etildi.")
    except:
        pass

    await call.answer("Rad etildi ❌")
# =====================================================
# 🔍 QIDIRISH
# =====================================================
class SearchUserFSM(StatesGroup):
    waiting_query = State()

@router.message(F.text == "🔍 Qidirish")
async def admin_search_user_start(message: Message, state: FSMContext):
    await message.answer("👤 Ism/Familiya yoki Telegram ID ni kiriting:")
    await state.set_state(SearchUserFSM.waiting_query)

@router.message(SearchUserFSM.waiting_query)
async def admin_perform_search(message: Message, state: FSMContext):
    q = message.text.strip()

    # ID bo‘yicha
    if q.isdigit():
        user = get_teacher(int(q))
        if not user:
            await message.answer("❌ Bunday ID topilmadi.")
        else:
            user_id = user[0]
            fio = user[1]
            faculty = user[3]
            await message.answer(
                f"👤 {fio}\n🏛 {faculty}\n🆔 {user_id}"
            )
        await state.clear()
        return

    # FIO bo‘yicha
    results = find_teachers_by_name(q)
    if not results:
        await message.answer("❌ Topilmadi.")
    else:
        text = "<b>Topilganlar:</b>\n\n"
        for u in results:
            text += f"{u['fio']} — {u['faculty']}\n🆔 {u['user_id']}\n\n"
        await message.answer(text, parse_mode="HTML")

    await state.clear()


# =====================================================
# ❌ FOYDALANUVCHINI O‘CHIRISH
# =====================================================
class DeleteUserFSM(StatesGroup):
    waiting_query = State()

@router.message(F.text.contains("Foydalanuvchini o‘chirish"))
async def start_delete_user(message: Message, state: FSMContext):
    await message.answer("🧾 O‘chirmoqchi bo‘lgan FIO yoki Telegram ID ni kiriting:")
    await state.set_state(DeleteUserFSM.waiting_query)


@router.message(DeleteUserFSM.waiting_query)
async def search_user(message: Message, state: FSMContext):
    text = message.text.strip()

    try:
        numeric_id = int(text)
    except ValueError:
        numeric_id = None

    users = search_users_by_fio_or_id(text=text, numeric_id=numeric_id)

    if not users:
        await message.answer("❌ Hech qanday foydalanuvchi topilmadi.")
        await state.clear()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{u['fio']} — {u['category']} — ID:{u['user_id']}",
                    callback_data=f"admindel:{u['user_id']}"
                )
            ]
            for u in users
        ]
    )

    await message.answer("🔍 O‘chirmoqchi bo‘lgan foydalanuvchini tanlang:", reply_markup=kb)
    await state.clear()

@router.callback_query(F.data.startswith("admindel:"))
async def delete_user(call: CallbackQuery):
    user_id = int(call.data.split(":")[1])

    await delete_user_by_id(user_id)

    await call.message.edit_text(f"✅ Foydalanuvchi bazadan o‘chirildi.\n🆔 ID: {user_id}")
    await call.answer("O‘chirildi!")

# =====================================================
# 📝 SAVOL–JAVOB EXCEL EXPORT
# =====================================================
class QAFilterFSM(StatesGroup):
    date_from = State()
    date_to = State()

@router.message(F.text == "📝 Savol–Javoblar (Excel)")
async def qa_filter_start(message: Message, state: FSMContext):
    await message.answer("📅 Boshlanish sana (YYYY-MM-DD):")
    await state.set_state(QAFilterFSM.date_from)

@router.message(QAFilterFSM.date_from)
async def qa_set_from(message: Message, state: FSMContext):
    await state.update_data(date_from=message.text.strip())
    await state.set_state(QAFilterFSM.date_to)
    await message.answer("📅 Tugash sana:")

@router.message(QAFilterFSM.date_to)
async def qa_set_to(message: Message, state: FSMContext):
    data = await state.get_data()
    rows = await fetch_answers_range(data["date_from"], message.text.strip())

    if not rows:
        await message.answer("❌ Maʼlumot yo‘q")
        await state.clear()
        return

    df = pd.DataFrame(rows)
    file = f"answers_{data['date_from']}_{message.text}.xlsx"
    df.to_excel(file, index=False)
    await message.answer_document(FSInputFile(file), caption="✅ Tayyor")
    await state.clear()


# =====================================================
# 📂 BACKUP (DB)
# =====================================================
@router.message(F.text == "📂 Backup (DB)")
async def backup_db(message: Message):
    if message.from_user.id not in ADMINS:
        return

    backup_file = "backup_bot.db"
    shutil.copy(backup_file)

    await message.answer_document(
        FSInputFile(backup_file),
        caption="✅ DB backup tayyor!"
    )

ADMINS = [1017100005]  # <- O'zingizning Telegram ID'ingizni kiriting

@router.message(Command("fix_search"))
async def fix_search_handler(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Sizda ruxsat yo‘q.")
        return

    count = await rebuild_students_search()
    await message.answer(f"✅ {count} ta buyruqda students_search yangilandi.")