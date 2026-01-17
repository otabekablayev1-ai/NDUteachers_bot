from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_student, search_orders_multi

router = Router()

@router.callback_query(F.data == "student_my_orders")
async def student_my_orders(call: CallbackQuery):
    student = get_student(call.from_user.id)
    if not student:
        await call.answer("❌ Talaba topilmadi", show_alert=True)
        return

    orders = search_orders_multi(
        faculty=student.faculty,
        lastname=student.fio.split()[0]
    )

    if not orders:
        await call.message.answer("📭 Sizga tegishli buyruqlar topilmadi.")
        return await call.answer()

    text = "📄 <b>Mening buyruqlarim:</b>\n\n"
    for o in orders:
        text += f"👉 <a href=\"{o[2]}\">{o[1]}</a>\n"

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()
