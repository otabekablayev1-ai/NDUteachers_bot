from math import ceil

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.db import get_questions_by_manager, get_manager_by_id

router = Router()

PAGE_SIZE = 10


def _short_name(name: str, max_len: int = 18) -> str:
    if not name:
        return "Noma'lum"
    return name if len(name) <= max_len else name[:max_len - 1] + "…"


def _short_pos(pos: str, max_len: int = 10) -> str:
    if not pos:
        return "-"
    return pos if len(pos) <= max_len else pos[:max_len - 1] + "…"


async def build_interactive_table(rows, bot, page: int = 1):
    total = len(rows)
    total_pages = max(1, ceil(total / PAGE_SIZE))
    page = max(1, min(page, total_pages))

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_rows = rows[start:end]

    title = (
        "<b>📊 Menejerlar statistikasi</b>\n"
        f"Jami: {total} ta | Sahifa: {page}/{total_pages}\n\n"
        "Pastdagi ko‘k/qizil sonlarni bosing."
    )

    keyboard = []

    # Header row
    keyboard.append([
        InlineKeyboardButton(text="№", callback_data="noop"),
        InlineKeyboardButton(text="Menejer", callback_data="noop"),
        InlineKeyboardButton(text="Lavozim", callback_data="noop"),
        InlineKeyboardButton(text="🔵", callback_data="noop"),
        InlineKeyboardButton(text="🔴", callback_data="noop"),
    ])

    for idx, r in enumerate(page_rows, start=start + 1):
        manager_id = r["manager_id"]
        answered = int(r.get("answered_count", 0))
        unanswered = int(r.get("unanswered_count", 0))
        position = _short_pos(str(r.get("position", "")))

        try:
            manager = await get_manager_by_id(manager_id)
            if manager and getattr(manager, "fio", None):
                name = manager.fio
            else:
                chat = await bot.get_chat(manager_id)
                name = chat.full_name
        except Exception:
            name = str(manager_id)

        name = _short_name(name)

        keyboard.append([
            InlineKeyboardButton(text=str(idx), callback_data="noop"),
            InlineKeyboardButton(text=name, callback_data=f"manager_info_{manager_id}"),
            InlineKeyboardButton(text=position, callback_data="noop"),
            InlineKeyboardButton(
                text=str(answered),
                callback_data=f"answered_{manager_id}_{page}"
            ),
            InlineKeyboardButton(
                text=str(unanswered),
                callback_data=f"unanswered_{manager_id}_{page}"
            ),
        ])

    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"rating_page_{page - 1}"
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"rating_page_{page + 1}"
            )
        )
    if nav:
        keyboard.append(nav)

    return title, InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "noop")
async def ignore_noop(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith("rating_page_"))
async def change_rating_page(call: CallbackQuery):
    page = int(call.data.split("_")[-1])

    # heads.py dagi shu funksiyadan keladigan data
    rows = call.message.bot.get("interactive_rating_rows")
    if not rows:
        await call.answer("Jadval ma'lumoti topilmadi", show_alert=True)
        return

    text, kb = await build_interactive_table(rows, call.message.bot, page=page)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("answered_"))
async def show_answered(call: CallbackQuery):
    parts = call.data.split("_")
    manager_id = int(parts[1])

    questions = await get_questions_by_manager(manager_id, answered=True)

    if not questions:
        await call.answer("Ko‘rib chiqilgan murojaatlar yo‘q", show_alert=True)
        return

    lines = ["✅ <b>Ko‘rib chiqilgan murojaatlar</b>\n"]
    for i, q in enumerate(questions[:15], 1):
        msg = (q.message_text or "").strip()
        msg = msg[:120] + ("..." if len(msg) > 120 else "")
        lines.append(f"{i}. {q.fio or 'Noma’lum'} — {msg}")

    await call.message.answer("\n".join(lines), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("unanswered_"))
async def show_unanswered(call: CallbackQuery):
    parts = call.data.split("_")
    manager_id = int(parts[1])

    questions = await get_questions_by_manager(manager_id, answered=False)

    if not questions:
        await call.answer("Ko‘rib chiqilmagan murojaatlar yo‘q", show_alert=True)
        return

    lines = ["❌ <b>Ko‘rib chiqilmagan murojaatlar</b>\n"]
    for i, q in enumerate(questions[:15], 1):
        msg = (q.message_text or "").strip()
        msg = msg[:120] + ("..." if len(msg) > 120 else "")
        lines.append(f"{i}. {q.fio or 'Noma’lum'} — {msg}")

    await call.message.answer("\n".join(lines), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("manager_info_"))
async def show_manager_info(call: CallbackQuery):
    manager_id = int(call.data.split("_")[-1])

    manager = await get_manager_by_id(manager_id)
    if manager:
        text = (
            "<b>👤 Menejer haqida</b>\n\n"
            f"F.I.O: {manager.fio or '-'}\n"
            f"Lavozimi: {manager.position or '-'}\n"
            f"Bo‘lim/Fakultet: {manager.faculty or '-'}\n"
            f"Telegram ID: {manager.telegram_id}"
        )
    else:
        text = f"Menejer topilmadi.\nTelegram ID: {manager_id}"

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()