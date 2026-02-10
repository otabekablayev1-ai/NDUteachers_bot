from database.utils import normalize_text

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.utils import send_long_message

from data.config import ADMINS
from handlers.constants import YEARS, FACULTIES, ORDER_TYPES
from database.db import (
    add_order_link,
    get_all_order_links,
    search_orders_multi,
)

router = Router()

# ==========================
# 🔗 BUYRUQ HAVOLASI FSM
# ==========================
class OrderLinkState(StatesGroup):
    title = State()
    link = State()
    year = State()
    faculty = State()
    type = State()
    students = State()

# ==========================
# 📘 Buyruqlar menyusi
# ==========================
@router.message(F.text == "📘 Buyruqlar")
async def orders_menu(message: Message):
    if message.from_user.id in ADMINS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📘 Buyruqlar ro‘yxati", callback_data="orders_filter")],
                [InlineKeyboardButton(text="🔗 Buyruq havolasi qo‘shish", callback_data="orders_add_link")],
            ]
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📘 Buyruqlar ro‘yxati", callback_data="orders_filter")],
            ]
        )

    await message.answer("📘 Buyruqlar bo‘limi:", reply_markup=kb)

# ==========================
# 🔎 FILTER FSM
# ==========================
class OrderFilterState(StatesGroup):
    faculty = State()
    type = State()
    lastname = State()

# ==========================
# 📘 FILTR MENYUSI (yonma-yon)
# ==========================
@router.callback_query(F.data == "orders_filter")
async def orders_filter_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏛 Fakultet", callback_data="open_faculties"),
                InlineKeyboardButton(text="📑 Buyruq turi", callback_data="open_types"),
            ],
            [InlineKeyboardButton(text="🔎 Familiya", callback_data="filter_lastname")],
            [InlineKeyboardButton(text="🔍 Izlash", callback_data="filter_search")]
        ]
    )
    await call.message.answer("📘 Buyruqlarni filterlash bo‘limi:", reply_markup=kb)
    await call.answer()


# ==========================
# 📅 YIL DROPDOWN
# ==========================
# @router.callback_query(F.data == "open_years")
# async def dropdown_years(call: CallbackQuery):
    #kb = InlineKeyboardMarkup(
        #inline_keyboard=[
            #[InlineKeyboardButton(text=year, callback_data=f"set_year_{year}")]
            #for year in YEARS
        #] + [[InlineKeyboardButton(text="⬅ Orqaga", callback_data="orders_filter")]]
    #)
    #await call.message.edit_reply_markup(reply_markup=kb)
    #await call.answer()

#@router.callback_query(F.data.startswith("set_year_"))
# async def set_year(call: CallbackQuery, state: FSMContext):
    #await state.update_data(year=call.data.replace("set_year_", ""))
    #await call.answer("✔ Yil tanlandi")


# ==========================
# 🏛 FAKULTET DROPDOWN
# ==========================
@router.callback_query(F.data == "open_faculties")
async def dropdown_faculties(call: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fac, callback_data=f"set_fac_{i}")]
            for i, fac in enumerate(FACULTIES)
        ] + [[InlineKeyboardButton(text="⬅ Orqaga", callback_data="orders_filter")]]
    )
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("set_fac_"))
async def set_fac(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.replace("set_fac_", ""))
    await state.update_data(faculty=FACULTIES[idx])
    await call.answer("✔ Fakultet tanlandi")


# ==========================
# 📑 BUYRUQ TURI DROPDOWN
# ==========================
@router.callback_query(F.data == "open_types")
async def dropdown_types(call: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=f"set_type_{i}")]
            for i, t in enumerate(ORDER_TYPES)
        ] + [[InlineKeyboardButton(text="⬅ Orqaga", callback_data="orders_filter")]]
    )
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("set_type_"))
async def set_type(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.replace("set_type_", ""))
    await state.update_data(type=ORDER_TYPES[idx])
    await call.answer("✔ Buyruq turi tanlandi")


# ==========================
# 🔎 FAMILIYA FILTRI — ASOSIY TUZATISH!
# ==========================
@router.callback_query(F.data == "filter_lastname")
async def filter_lastname_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🔎 Familiyani kiriting:")
    await state.set_state(OrderFilterState.lastname)
    await call.answer()


@router.message(OrderFilterState.lastname)
async def set_lastname(message: Message, state: FSMContext):
    await state.update_data(lastname=message.text.strip())
    await message.answer("✔ Familiya qabul qilindi\n👇 Endi *Izlash* tugmasini bosing.", parse_mode="Markdown")


@router.callback_query(F.data == "filter_search")
async def filter_search(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if not data.get("lastname"):
        await call.message.answer("❗ Avval familiyani kiriting.")
        return await call.answer()

    # 🔴 MUHIM: await BOR
    rows = await search_orders_multi(
        faculty=data.get("faculty"),
        type=data.get("type"),
        fio=data.get("lastname")   # 👈 familiya shu yerda uzatiladi
    )

    if not rows:
        await call.message.answer("❌ Hech narsa topilmadi.")
        return await call.answer()

    text = "📄 <b>Natijalar:</b>\n\n"
    for row in rows:
        r = row._mapping
        text += f"👉 <a href=\"{r['link']}\">{r['title']}</a>\n"

    await send_long_message(call.message, text)
    await call.answer()

# ==========================
# 📄 HAMMA BUYRUQLARNI KO‘RISH
# ==========================
@router.callback_query(F.data == "filter_show_all")
async def show_all_orders(call: CallbackQuery):
    rows = get_all_order_links()
    if not rows:
        await call.message.answer("📭 Saqlangan buyruqlar topilmadi.")
        return await call.answer()

    for row in rows:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📖 O‘qish", url=row["link"])]]
        )
        await call.message.answer(
            f"📘 {row['title']}\n"
            f"📅 {row.get('year', '')}\n"
            f"🏛 {row.get('faculty', '')}\n"
            f"📑 {row.get('type', '')}",
            reply_markup=kb,
        )

    await call.answer()

# ==========================
# 🔗 BUYRUQ HAVOLASI QO‘SHISH
# ==========================
@router.callback_query(F.data == "orders_add_link")
async def add_link_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("📘 Buyruq nomini kiriting:")
    await state.set_state(OrderLinkState.title)
    await call.answer()


@router.message(OrderLinkState.title)
async def set_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("🔗 Buyruq havolasini yuboring (Google Drive link):")
    await state.set_state(OrderLinkState.link)


@router.message(OrderLinkState.link)
async def set_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=year, callback_data=f"year_{year}")]
            for year in YEARS
        ]
    )

    await message.answer("📅 O‘quv yilini tanlang:", reply_markup=kb)
    await state.set_state(OrderLinkState.year)


@router.callback_query(F.data.startswith("year_"))
async def choose_year(call: CallbackQuery, state: FSMContext):
    year = call.data.replace("year_", "")
    await state.update_data(year=year)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fac, callback_data=f"fac_{i}")]
            for i, fac in enumerate(FACULTIES)
        ]
    )

    await call.message.answer("🏛 Fakultetni tanlang:", reply_markup=kb)
    await state.set_state(OrderLinkState.faculty)
    await call.answer()


@router.callback_query(F.data.startswith("fac_"))
async def choose_faculty(call: CallbackQuery, state: FSMContext):
    index = int(call.data.replace("fac_", ""))
    faculty = FACULTIES[index]
    await state.update_data(faculty=faculty)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=f"type_{i}")]
            for i, t in enumerate(ORDER_TYPES)
        ]
    )

    await call.message.answer("📑 Buyruq turini tanlang:", reply_markup=kb)
    await state.set_state(OrderLinkState.type)
    await call.answer()


@router.callback_query(F.data.startswith("type_"))
async def choose_type(call: CallbackQuery, state: FSMContext):
    index = int(call.data.replace("type_", ""))
    type_name = ORDER_TYPES[index]

    await state.update_data(type=type_name)
    await call.message.answer("👥 Talabalar familiyalarini kiriting (vergul bilan):")
    await state.set_state(OrderLinkState.students)
    await call.answer()


@router.message(OrderLinkState.students)
async def set_students(message: Message, state: FSMContext):
    data = await state.get_data()

    students_raw = message.text
    students_search = normalize_text(students_raw)

    await add_order_link(
        title=data["title"],
        link=data["link"],
        year=data["year"],
        faculty=data["faculty"],
        type=data["type"],
        students_raw=students_raw,
        students_search=students_search,
    )

    await message.answer("✅ Buyruq muvaffaqiyatli saqlandi!")
    await state.clear()


