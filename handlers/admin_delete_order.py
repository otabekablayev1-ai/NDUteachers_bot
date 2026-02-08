from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from data.config import ADMINS
from database.db import search_order_links_for_delete, delete_order_link_by_id

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
    if message.from_user.id not in ADMINS:
        return

    query = message.text.strip()

    # 🔴 MUHIM: await
    rows = await search_order_links_for_delete(query)

    if not rows:
        await message.answer("❌ Hech narsa topilmadi.")
        return

    for row in rows:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="❌ O‘chirish",
                    callback_data=f"orderlink_confirm_delete:{row.id}"
                )]
            ]
        )

        await message.answer(
            f"📘 <b>{row.title}</b>\n"
            f"🔗 {row.link}\n"
            f"🆔 ID: <b>{row.id}</b>",
            parse_mode="HTML",
            reply_markup=kb
        )

    await state.clear()


@router.callback_query(F.data.startswith("orderlink_confirm_delete:"))
async def confirm_delete(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return await call.answer("Ruxsat yo‘q", show_alert=True)

    order_id = int(call.data.split(":")[1])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data=f"orderlink_delete_yes:{order_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Yo‘q",
                    callback_data="orderlink_delete_no"
                )
            ]
        ]
    )

    await call.message.answer("⚠️ Rostdan ham o‘chirasizmi?", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("orderlink_delete_yes:"))
async def delete_yes(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return await call.answer("Ruxsat yo‘q", show_alert=True)

    order_id = int(call.data.split(":")[1])

    # 🔴 MUHIM: await
    ok = await delete_order_link_by_id(order_id)

    if ok:
        await call.message.answer("✅ Buyruq o‘chirildi.")
    else:
        await call.message.answer("❌ O‘chirishda xatolik yoki buyruq topilmadi.")

    await call.answer()


@router.callback_query(F.data == "orderlink_delete_no")
async def delete_no(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return await call.answer("Ruxsat yo‘q", show_alert=True)

    await call.message.answer("❎ Bekor qilindi.")
    await call.answer()
