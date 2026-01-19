from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from data.config import ADMINS
from database.db import search_orders_for_delete, delete_order_by_id

router = Router()


class DeleteOrderFSM(StatesGroup):
    waiting_query = State()


@router.message(F.text == "🗑 Buyruqni o‘chirish")
async def start_delete(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    await message.answer("✏️ Buyruq nomi yoki raqamini kiriting:")
    await state.set_state(DeleteOrderFSM.waiting_query)


@router.message(DeleteOrderFSM.waiting_query)
async def search_orders(message: Message, state: FSMContext):
    query = message.text.strip()
    rows = search_orders_for_delete(query)

    if not rows:
        await message.answer("❌ Hech narsa topilmadi.")
        return

    for row in rows:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="❌ O‘chirish",
                    callback_data=f"confirm_delete_{row.id}"
                )]
            ]
        )

        await message.answer(
            f"📘 <b>{row.title}</b>\n🔗 {row.link}",
            parse_mode="HTML",
            reply_markup=kb
        )


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(call: CallbackQuery):
    order_id = int(call.data.replace("confirm_delete_", ""))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"delete_yes_{order_id}"),
                InlineKeyboardButton(text="❌ Yo‘q", callback_data="delete_no")
            ]
        ]
    )

    await call.message.answer("⚠️ Rostdan ham o‘chirasizmi?", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("delete_yes_"))
async def delete_yes(call: CallbackQuery):
    order_id = int(call.data.replace("delete_yes_", ""))
    ok = delete_order_by_id(order_id)

    if ok:
        await call.message.answer("✅ Buyruq o‘chirildi.")
    else:
        await call.message.answer("❌ O‘chirishda xatolik.")

    await call.answer()


@router.callback_query(F.data == "delete_no")
async def delete_no(call: CallbackQuery):
    await call.message.answer("❎ Bekor qilindi.")
    await call.answer()
