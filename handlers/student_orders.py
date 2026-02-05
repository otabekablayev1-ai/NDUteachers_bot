from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_student, search_orders_multi
from database.db import search_orders_by_full_fio
from .utils import send_long_message

router = Router()

from database.db import search_orders_by_full_fio, get_student

@router.callback_query(F.data == "student_my_orders")
async def student_my_orders(call: CallbackQuery):
    student = get_student(call.from_user.id)
    if not student:
        await call.answer("❌ Talaba topilmadi", show_alert=True)
        return

    rows = search_orders_by_full_fio(
        faculty=student.faculty,
        fio=student.fio
    )

    if not rows:
        await call.message.answer("📭 Sizga tegishli buyruqlar topilmadi.")
        return await call.answer()

    text = "📄 <b>Mening buyruqlarim:</b>\n\n"
    for r in rows:
        data = r._mapping
        text += f"👉 <a href=\"{data['link']}\">{data['title']}</a>\n"

    await send_long_message(call.message, text)
    await call.answer()


