from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import get_questions_by_manager

router = Router()


# =========================
# 🧱 TABLE BUILDER
# =========================
async def build_interactive_table(rows, bot):
    text = "<b>📊 Menejerlar statistikasi</b>\n\n"
    keyboard = []

    for idx, r in enumerate(rows, 1):
        manager_id = r["manager_id"]

        # 🔥 ISM OLISH
        try:
            chat = await bot.get_chat(manager_id)
            name = chat.full_name
        except:
            name = str(manager_id)

        answered = r.get("answered_count", 0)
        unanswered = r.get("unanswered_count", 0)
        rating = r.get("avg_rating", 0)

        text += (
            f"{idx}. <b>{name}</b>\n"
            f"⭐ {rating} | "
            f"✅ {answered} | "
            f"❌ {unanswered}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                text=f"🔵 {answered}",
                callback_data=f"answered_{manager_id}"
            ),
            InlineKeyboardButton(
                text=f"🔴 {unanswered}",
                callback_data=f"unanswered_{manager_id}"
            )
        ])

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================
# 📥 ANSWERED BOSILGANDA
# =========================
@router.callback_query(F.data.startswith("answered_"))
async def show_answered(call: CallbackQuery):
    manager_id = int(call.data.split("_")[1])

    questions = await get_questions_by_manager(manager_id, answered=True)

    text = "✅ <b>Ko‘rib chiqilgan murojaatlar:</b>\n\n"

    for q in questions:
        text += f"• {q.message_text}\n"

    await call.message.answer(text, parse_mode="HTML")


# =========================
# 📥 UNANSWERED BOSILGANDA
# =========================
@router.callback_query(F.data.startswith("unanswered_"))
async def show_unanswered(call: CallbackQuery):
    manager_id = int(call.data.split("_")[1])

    questions = await get_questions_by_manager(manager_id, answered=False)

    text = "❌ <b>Ko‘rib chiqilmagan murojaatlar:</b>\n\n"

    for q in questions:
        text += f"• {q.message_text}\n"

    await call.message.answer(text, parse_mode="HTML")