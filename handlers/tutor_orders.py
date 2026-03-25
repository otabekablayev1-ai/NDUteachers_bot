from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database.utils import send_long_message
from database.db import search_orders_multi, get_teacher
from database.utils import log_activity
router = Router()


class TutorOrderFSM(StatesGroup):
    waiting_student_fio = State()


@router.callback_query(F.data == "tutor_orders")
async def tutor_orders_start(call: CallbackQuery, state: FSMContext):

    # 🔥 LOG
    await log_activity(
        call.from_user.id,
        "tutor",
        "tutor_orders_start"
    )

    await call.message.answer(
        "✏️ Talabaning ism va familiyasini <b>to‘liq</b> kiriting:"
    )
    await state.set_state(TutorOrderFSM.waiting_student_fio)
    await call.answer()

@router.message(TutorOrderFSM.waiting_student_fio)
async def tutor_orders_search(message: Message, state: FSMContext):

    # 🔥 LOG
    await log_activity(
        message.from_user.id,
        "tutor",
        "tutor_orders_search"
    )

    fio = message.text.strip()

    tutor = await get_teacher(message.from_user.id)
    if not tutor:
        await message.answer("❌ Tyutor topilmadi.")
        await state.clear()
        return

    rows = await search_orders_multi(
        faculty=tutor.faculty,
        fio=fio
    )

    if not rows:
        await message.answer("📭 Bu talaba uchun buyruqlar topilmadi.")
        await state.clear()
        return

    text = "📘 <b>Topilgan buyruqlar:</b>\n\n"

    for r in rows:
        data = r._mapping
        link = data.get("link") or "#"
        title = data.get("title") or "Noma’lum"

        text += f"👉 <a href=\"{link}\">{title}</a>\n"

    await send_long_message(message, text)
    await state.clear()

