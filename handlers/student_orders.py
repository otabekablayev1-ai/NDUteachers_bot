from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.utils import send_long_message

router = Router()

from database.db import search_orders_multi, get_student

@router.callback_query(F.data == "student_my_orders")
async def student_my_orders(call: CallbackQuery):
    try:
        student = await get_student(call.from_user.id)
        if not student:
            await call.answer("❌ Talaba topilmadi", show_alert=True)
            return

        rows = await search_orders_multi(
            faculty=student.faculty or None,
            fio=student.fio or None
        )

        if not rows:
            await call.message.answer("📭 Sizga tegishli buyruqlar topilmadi.")
            await call.answer()
            return

        text = "📄 <b>Mening buyruqlarim:</b>\n\n"

        for r in rows:
            data = r._mapping
            link = data.get("link") or "#"
            title = data.get("title") or "Noma’lum"
            text += f"👉 <a href=\"{link}\">{title}</a>\n"

        await send_long_message(call.message, text)
        await call.answer()

    except Exception as e:
        print("STUDENT ORDERS ERROR:", e)
        await call.answer("❌ Ichki xatolik", show_alert=True)
