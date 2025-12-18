from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_teacher
from database.db import move_request_to_main_tables

router = Router()

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])

    # 1) register_requests → teachers (UPSERT) + status=approved
    move_request_to_main_tables(user_id)

    # 2) endi teachers dan O‘QIYMIZ (to‘g‘ri indekslar bilan)
    teacher = get_teacher(user_id)
    #              0        1      2         3           4      5
    # teachers: (user_id,  fio,  faculty, department,  phone, role, created_at)

    if teacher:
        faculty = teacher[2] or "Noma’lum fakultet"
        department = teacher[3] or "Noma’lum kafedra"
    else:
        faculty = "Noma’lum fakultet"
        department = "Noma’lum kafedra"

    welcome_text = (
        f"Assalomu alaykum, hurmatli ustoz!\n\n"
        f"Ro‘yxatdan o‘tish yakunlandi!\n"
        f"Siz <b>{faculty}</b> tarkibidagi <b>{department}</b> a’zosisiz.\n\n"
        f"Siz Navoiy davlat universitetining rasmiy <b>@NDUteachers_bot</b> ga muvaffaqiyatli a’zo bo‘ldingiz.\n\n"
        f"Ushbu bot orqali Siz:\n"
        f"• Registrator ofisi menejerlari,\n"
        f"• Universitet rahbariyati\n"
        f"bilan masofaviy tarzda tezkor va qulay muloqotda bo‘lishingiz mumkin.\n\n"
        f"📌 Savol yoki murojaat yuborish uchun menyudan kerakli tugmani tanlang.\n"
        f"Ushbu bot Navoiy davlat universiteti Registrator ofisi menejeri O.Ablayev tomonidan ishlab chiqilgan.\n"
    )

    try:
        await call.message.bot.send_message(user_id, welcome_text, parse_mode="HTML")
        await call.message.edit_text("✅ Foydalanuvchi tasdiqlandi va xabar yuborildi.")
        await call.answer("✅ Tasdiq yuborildi.")
    except Exception as e:
        await call.message.answer(f"⚠️ Xato yuz berdi:\n{e}")
        print(e)

from database.db import delete_teacher

@router.callback_query(F.data.startswith("delete_"))
async def delete_teacher_callback(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    delete_teacher(user_id)
    await callback.message.edit_text(f"🗑️ Foydalanuvchi ID {user_id} o‘chirildi.")

    try:
        await call.message.bot.send_message(
            user_id,
            "❌ Kechirasiz, ma’lumotlaringiz HEMIS tizimida topilmadi.\n"
            "Iltimos, qayta tekshirib, to‘g‘ri ma’lumot kiriting."
        )
        await call.message.edit_text("❌ Foydalanuvchi bekor qilindi va bazadan o‘chirildi.")
        await call.answer("❌ Bekor qilindi")
    except Exception as e:
        await call.message.answer(f"⚠️ Xato:\n{e}")
