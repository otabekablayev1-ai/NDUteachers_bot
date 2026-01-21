from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from database.db import search_orders_for_tutor_by_student
from database.db import get_teacher

router = Router()


class TutorOrderFSM(StatesGroup):
    waiting_student_fio = State()


@router.callback_query(F.data == "tutor_orders")
async def tutor_orders_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "✏️ Talabaning ismi va familiyasini to‘liq kiriting:"
    )
    await state.set_state(TutorOrderFSM.waiting_student_fio)
    await call.answer()


@router.message(TutorOrderFSM.waiting_student_fio)
async def tutor_orders_search(message: Message, state: FSMContext):
    fio = message.text.strip()

    tutor = get_teacher(message.from_user.id)
    if not tutor:
        await message.answer("❌ Tyutor topilmadi.")
        await state.clear()
        return

    faculty = tutor.faculty

    rows = search_orders_for_tutor_by_student(
        faculty=faculty,
        student_fio=fio
    )

    if not rows:
        await message.answer("📭 Bu talaba uchun buyruqlar topilmadi.")
        await state.clear()
        return

    text = "📘 <b>Topilgan buyruqlar:</b>\n\n"
    for row in rows:
        data = row._mapping
        text += f"👉 <a href=\"{data['link']}\">{data['title']}</a>\n"

    await message.answer(text, parse_mode="HTML")
    await state.clear()
