from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from data.config import ADMINS
from database.db import add_manager

router = Router()


# =========================
# FSM STATE
# =========================
class AddManagerFSM(StatesGroup):
    telegram_id = State()
    fio = State()
    position = State()
    faculty = State()

# =========================
# ADMIN TEKSHIRISH
# =========================
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# =========================
# /add_manager BOSHLASH
# =========================
@router.message(F.text == "/add_manager")
async def start_add_manager(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    await message.answer("📌 Manager Telegram ID sini yuboring:")
    await state.set_state(AddManagerFSM.telegram_id)


# =========================
# TELEGRAM ID QABUL QILISH
# =========================
@router.message(AddManagerFSM.telegram_id)
async def manager_id_step(message: Message, state: FSMContext):

    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("❌ Telegram ID faqat raqam bo‘lishi kerak.")
        return

    await state.update_data(telegram_id=telegram_id)

    await message.answer("👤 Manager F.I.O ni yuboring:")
    await state.set_state(AddManagerFSM.fio)


# =========================
# FIO QABUL QILISH
# =========================
@router.message(AddManagerFSM.fio)
async def manager_fio_step(message: Message, state: FSMContext):

    await state.update_data(fio=message.text.strip())

    await message.answer("💼 Lavozimini yuboring:")
    await state.set_state(AddManagerFSM.position)


# =========================
# LAVOZIM QABUL QILISH
# =========================
@router.message(AddManagerFSM.position)
async def manager_position_step(message: Message, state: FSMContext):

    await state.update_data(position=message.text.strip())

    await message.answer("🏫 Fakultet yoki bo‘lim nomini yuboring:")
    await state.set_state(AddManagerFSM.faculty)


# =========================
# FAKULTET QABUL QILISH
# =========================
@router.message(AddManagerFSM.faculty)
async def manager_faculty_step(message: Message, state: FSMContext):

    data = await state.get_data()

    try:
        await add_manager(
            telegram_id=data["telegram_id"],
            fio=data["fio"],
            position=data["position"],
            faculty=message.text.strip()
        )

        await message.answer("✅ Manager muvaffaqiyatli qo‘shildi.")

    except Exception as e:
        await message.answer("❌ Manager qo‘shishda xatolik yuz berdi.")
        print("ADD MANAGER ERROR:", e)

    await state.clear()