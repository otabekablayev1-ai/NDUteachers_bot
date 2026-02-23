from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from data.config import ADMINS, RAHBARLAR
from database.db import save_register_request, get_teacher

router = Router()


# ============================================================
# STATES
# ============================================================
class RegState(StatesGroup):
    phone = State()
    role = State()

    # Teacher
    teacher_faculty = State()
    teacher_department = State()
    teacher_fio = State()
    teacher_hemis = State()
    teacher_passport = State()

    # Tyutor
    tyutor_faculty = State()
    tyutor_fio = State()
    tyutor_hemis = State()
    tyutor_passport = State()

    # Student
    edu_type = State()
    edu_form = State()
    student_faculty = State()
    student_course = State()
    student_group = State()
    student_fio = State()
    student_hemis = State()
    student_passport = State()


# ============================================================
# START (Yangi foydalanuvchi uchun)
# ============================================================
@router.message(F.text == "/start")
async def start_reg(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in ADMINS:
        return

    for ids in RAHBARLAR.values():
        if user_id in ids:
            return

    row = await get_teacher(user_id)  # 🔥 await qo‘shildi

    if row:
        fio = row.fio or message.from_user.full_name
        role_db = (row.role or "").strip()

        if role_db == "O‘qituvchi":
            role_label = "Ustoz"
        elif role_db == "Tyutor":
            role_label = "Tyutor"
        elif role_db == "Talaba":
            role_label = "Talaba"
        else:
            role_label = "foydalanuvchi"

        await message.answer(
            f"Assalomu alaykum. Hurmatli {role_label}, siz ro‘yxatdan o‘tgan ekansiz.\n"
            f"Murojaat va savollaringizni bot orqali yuborishingiz mumkin."
        )
        await state.clear()
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Kontaktni ulashish", request_contact=True)]],
        resize_keyboard=True
    )

    await message.answer("📲 Telefon raqamingizni yuboring:", reply_markup=kb)
    await state.set_state(RegState.phone)

# ============================================================
# PHONE → ROLE
# ============================================================
@router.message(F.contact)
async def get_phone(message: Message, state: FSMContext):
    await state.set_state(RegState.phone)
    await state.update_data(phone=message.contact.phone_number)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="O‘qituvchi"),
                KeyboardButton(text="Dekan, Tyutor, Dispetcher"),
                KeyboardButton(text="Talaba"),
            ]
        ],
        resize_keyboard=True,
    )
    await message.answer("👤 Rolingizni tanlang:", reply_markup=kb)
    await state.set_state(RegState.role)


# ================================
# ROLE TANLASH
# ================================
@router.message(RegState.role)
async def choose_role(message: Message, state: FSMContext):
    text = message.text.strip()

    text = (
        text.replace("'", "‘")
        .replace("`", "‘")
        .replace("’", "‘")
        .replace("ʼ", "‘")
    )

    #roles = ["O‘qituvchi", "Dekan, Tyutor, Dispetcher", "Talaba"]
    ROLE_MAP = {
        "O‘qituvchi": "teacher",
        "Dekan, Tyutor, Dispetcher": "tutor",
        "Talaba": "student",
    }

    if text not in ROLE_MAP:
        return await message.answer(
            "❗ Iltimos, pastdagi tugmalardan birini tanlang."
        )

    role = ROLE_MAP[text]
    await state.update_data(role=role)

    # ============================
    # O‘QITUVCHI
    # ============================
    if text == "O‘qituvchi":
        faculties = [
            "Aniq fanlar fakulteti",
            "Iqtisodiyot fakulteti",
            "Maktabgacha va boshlang‘ich ta’lim fakulteti",
            "San’at va sport fakulteti",
            "Tabiiy fanlar va tibbiyot fakulteti",
            "Tarix fakulteti",
            "Tillar fakulteti",
            "O‘zbek filologiyasi fakulteti",
            "Tibbiyot fakulteti",
        ]
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f)] for f in faculties],
            resize_keyboard=True,
        )
        await message.answer("🏛 Fakultetni tanlang:", reply_markup=kb)
        return await state.set_state(RegState.teacher_faculty)

    # ============================
    # TYUTOR
    # ============================
    if text == "Dekan, Tyutor, Dispetcher":
        faculties = [
            "Aniq fanlar fakulteti",
            "Iqtisodiyot fakulteti",
            "Maktabgacha va boshlang‘ich ta’lim fakulteti",
            "San’at va sport fakulteti",
            "Tabiiy fanlar va tibbiyot fakulteti",
            "Tarix fakulteti",
            "Tillar fakulteti",
            "O‘zbek filologiyasi fakulteti",
            "Tibbiyot fakulteti",
        ]
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f)] for f in faculties],
            resize_keyboard=True,
        )
        await message.answer("🏛 Fakultetni tanlang:", reply_markup=kb)
        return await state.set_state(RegState.tyutor_faculty)

    # ============================
    # TALABA
    # ============================
    if text == "Talaba":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎓 Bakalavr", callback_data="edu_bak")],
                [InlineKeyboardButton(text="🎓 Magistratura", callback_data="edu_mag")],
            ]
        )

        await message.answer("🎓 Ta’lim turini tanlang:", reply_markup=kb)
        return await state.set_state(RegState.edu_type)


# ============================================================
# =====================  TEACHER FLOW  =======================
# ============================================================

TEACHER_DEPARTMENTS = {
     "Aniq fanlar fakulteti": [
        "Fizika va astronomiya kafedrasi",
        "Matematika kafedrasi",
        "Raqamli texnologiyalar kafedrasi",
     ],

    "Tabiiy fanlar va tibbiyot fakulteti": [
        "Biologiya kafedrasi",
        "Geografiya kafedrasi",
        "Kimyo kafedrasi",
        "Barchasi"
    ],

    "Tibbiyot fakulteti": [
        "Klinik fanlar kafedrasi",
        "Umumiy tibbiy fanlar kafedrasi",
    ],

    "Maktabgacha va boshlang‘ich ta’lim fakulteti": [
        "Maktabgacha ta’lim kafedrasi",
        "Boshlang‘ich ta’lim kafedrasi",
        "Pedagogika kafedrasi",
    ],

    "Tillar fakulteti": [
        "Fakultetlararo chet tillar kafedrasi",
        "Ingliz tili amaliy fanlar kafedrasi",
        "Ingliz tilshunosligi kafedrasi",
        "Qozoq tili va adabiyoti kafedrasi",
        "Rus tili va adabiyoti kafedrasi",
    ],

    "O‘zbek filologiyasi fakulteti": [
        "O‘zbek tili va adabiyoti kafedrasi",
        "O‘zbek tilshunosligi kafedrasi",
    ],

    "San’at va sport fakulteti": [
        "Jismoniy madaniyat kafedrasi",
        "Musiqiy ta’lim kafedrasi",
        "Sport faoliyati turlari kafedrasi",
        "Tasviriy san’at va muhandislik grafikasi kafedrasi",
        "Texnologik ta’lim kafedrasi",
    ],

    "Tarix fakulteti": [
        "Ijtimoiy fanlar kafedrasi",
        "Milliy g‘oya, ma’naviyat asoslari va huquq kafedrasi",
        "Psixologiya kafedrasi",
        "Tarix kafedrasi",
    ],

    "Iqtisodiyot fakulteti": [
        "Iqtisodiyot kafedrasi",
    ],
}

@router.message(RegState.teacher_faculty)
async def teacher_faculty(message: Message, state: FSMContext):
    faculty = message.text.strip()
    await state.update_data(teacher_faculty=faculty)

    departments = TEACHER_DEPARTMENTS.get(faculty)
    if not departments:
        await message.answer("❗ Iltimos, fakultet tugmasini tanlang.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d, callback_data=f"tdept_{i}")]
            for i, d in enumerate(departments)
        ]
    )

    await message.answer("🏢 Kafedrangizni tanlang:", reply_markup=kb)
    await state.set_state(RegState.teacher_department)


@router.callback_query(RegState.teacher_department, F.data.startswith("tdept_"))
async def teacher_department_cb(call: CallbackQuery, state: FSMContext):
    index = int(call.data.split("_")[1])

    data = await state.get_data()
    faculty = data.get("teacher_faculty")
    departments = TEACHER_DEPARTMENTS.get(faculty, [])

    chosen_dep = departments[index]
    await state.update_data(teacher_department=chosen_dep)

    await call.message.answer("👤 To‘liq F.I.Sh kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegState.teacher_fio)
    await call.answer()

@router.message(RegState.teacher_fio)
async def teacher_fio(message: Message, state: FSMContext):
    await state.update_data(teacher_fio=message.text)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="t_hemis_yes")],
            [InlineKeyboardButton(text="Yo‘q", callback_data="t_hemis_no")],
        ]
    )
    await message.answer("📋 HEMISda ma’lumotlaringiz bormi?", reply_markup=kb)
    await state.set_state(RegState.teacher_hemis)

@router.callback_query(RegState.teacher_hemis, F.data == "t_hemis_no")
async def teacher_hemis_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("❌ Siz HEMISda topilmadingiz.")
    await state.clear()
    await call.answer()

@router.callback_query(RegState.teacher_hemis, F.data == "t_hemis_yes")
async def teacher_hemis_yes(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🪪 Pasport seriya va raqamini kiriting (AB1234567):")
    await state.set_state(RegState.teacher_passport)
    await call.answer()

@router.message(RegState.teacher_passport)
async def teacher_finish(message: Message, state: FSMContext):
    await state.update_data(teacher_passport=message.text.strip())
    data = await state.get_data()

    # 🔵 BIRINCHI: so‘rovni register_requests ga yozamiz
    await save_register_request(
        user_id=message.from_user.id,
        fio=data.get("teacher_fio"),
        phone=data.get("phone"),
        faculty=data.get("teacher_faculty"),
        department=data.get("teacher_department"),
        passport=data.get("teacher_passport"),
        role="O‘qituvchi",
    )

    # 🔵 IKINCHI: adminga tugmalar bilan yuboramiz
    for admin in ADMINS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✔ Tasdiqlash",
                                      callback_data=f"approve_{message.from_user.id}")],
                [InlineKeyboardButton(text="❌ Rad etish",
                                      callback_data=f"reject_{message.from_user.id}")]
            ]
        )

        await message.bot.send_message(
            admin,
            (
                "📥 <b>Yangi O‘qituvchi so‘rovi:</b>\n"
                f"👤 {data['teacher_fio']}\n"
                f"📞 {data['phone']}\n"
                f"🏛 {data['teacher_faculty']}\n"
                f"🏢 {data['teacher_department']}\n"
                f"🪪 Pasport: {data['teacher_passport']}"
            ),
            parse_mode="HTML",
            reply_markup=kb
        )

    await message.answer("✅ So‘rovingiz yuborildi. Admin tasdiqlashini kuting.")
    await state.clear()

# ============================================================
# ======================  TYUTOR FLOW  =======================
# ============================================================
@router.message(RegState.tyutor_faculty)
async def tyutor_faculty(message: Message, state: FSMContext):
    await state.update_data(tyutor_faculty=message.text)
    await message.answer("👤 To‘liq F.I.Sh kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegState.tyutor_fio)


@router.message(RegState.tyutor_fio)
async def tyutor_fio(message: Message, state: FSMContext):
    await state.update_data(tyutor_fio=message.text)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="y_hemis_yes")],
            [InlineKeyboardButton(text="Yo‘q", callback_data="y_hemis_no")],
        ]
    )
    await message.answer("📋 HEMISda ma’lumotlaringiz bormi?", reply_markup=kb)
    await state.set_state(RegState.tyutor_hemis)


@router.callback_query(RegState.tyutor_hemis, F.data == "y_hemis_no")
async def tyutor_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("❌ Siz HEMISda topilmadingiz.")
    await call.answer()
    await state.clear()


@router.callback_query(RegState.tyutor_hemis, F.data == "y_hemis_yes")
async def tyutor_yes(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🪪 Pasport seriya va raqamini kiriting (AB1234567):")
    await state.set_state(RegState.tyutor_passport)
    await call.answer()

@router.message(RegState.tyutor_passport)
async def tyutor_finish(message: Message, state: FSMContext):
    await state.update_data(tyutor_passport=message.text.strip())
    data = await state.get_data()

    await save_register_request(
        user_id=message.from_user.id,
        fio=data.get("tyutor_fio"),
        phone=data.get("phone"),
        faculty=data.get("tyutor_faculty"),
        department=None,
        passport=data.get("tyutor_passport"),
        role="Tyutor",
    )

    for admin in ADMINS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✔ Tasdiqlash",
                                      callback_data=f"approve_{message.from_user.id}")],
                [InlineKeyboardButton(text="❌ Rad etish",
                                      callback_data=f"reject_{message.from_user.id}")]
            ]
        )

        await message.bot.send_message(
            admin,
            (
                "📥 <b>Yangi Tyutor so‘rovi:</b>\n"
                f"👤 {data['tyutor_fio']}\n"
                f"📞 {data['phone']}\n"
                f"🏛 {data['tyutor_faculty']}\n"
                f"🪪 Pasport: {data['tyutor_passport']}"
            ),
            parse_mode="HTML",
            reply_markup=kb
        )

    await message.answer("✅ So‘rovingiz yuborildi. Admin tasdiqlashini kuting.")
    await state.clear()

# ============================================================
# ======================  STUDENT FLOW  ======================
# ============================================================

# 1) Ta’lim turi (Bakalavr / Magistratura)
@router.callback_query(RegState.edu_type, F.data.startswith("edu_"))
async def student_edu_type(call: CallbackQuery, state: FSMContext):
    if call.data == "edu_bak":
        edu_type = "Bakalavr"
    else:
        edu_type = "Magistratura"

    await state.update_data(edu_type=edu_type)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Kunduzgi", callback_data="form_kunduzgi")],
            [InlineKeyboardButton(text="Kechki", callback_data="form_kechki")],
            [InlineKeyboardButton(text="Sirtqi", callback_data="form_sirtqi")],
            [InlineKeyboardButton(text="Masofaviy", callback_data="form_masofaviy")],
        ]
    )

    await call.message.answer("🏫 Ta’lim shaklini tanlang:", reply_markup=kb)
    await state.set_state(RegState.edu_form)
    await call.answer()


# 2) Ta’lim shakli → fakultet
@router.callback_query(RegState.edu_form, F.data.startswith("form_"))
async def student_edu_form(call: CallbackQuery, state: FSMContext):
    form = call.data.replace("form_", "")
    await state.update_data(edu_form=form.capitalize())

    faculties = [
        "Aniq fanlar fakulteti",
        "Iqtisodiyot fakulteti",
        "Maktabgacha va boshlang‘ich ta’lim fakulteti",
        "San’at va sport fakulteti",
        "Tabiiy fanlar va tibbiyot fakulteti",
        "Tarix fakulteti",
        "Tillar fakulteti",
        "O‘zbek filologiyasi fakulteti",
        "Tibbiyot fakulteti",
    ]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f,
                    callback_data=f"studfac_{i}",
                )
            ]
            for i, f in enumerate(faculties)
        ]
    )

    await call.message.answer("🏛 Fakultetni tanlang:", reply_markup=kb)
    await state.set_state(RegState.student_faculty)
    await call.answer()


# 3) Fakultet → kurs
@router.callback_query(RegState.student_faculty, F.data.startswith("studfac_"))
async def student_faculty(call: CallbackQuery, state: FSMContext):
    index = int(call.data.split("_")[1])

    faculties = [
        "Aniq fanlar fakulteti",
        "Iqtisodiyot fakulteti",
        "Maktabgacha va boshlang‘ich ta’lim fakulteti",
        "San’at va sport fakulteti",
        "Tabiiy fanlar va tibbiyot fakulteti",
        "Tarix fakulteti",
        "Tillar fakulteti",
        "O‘zbek filologiyasi fakulteti",
        "Tibbiyot fakulteti"
    ]

    chosen = faculties[index]
    await state.update_data(student_faculty=chosen)

    data = await state.get_data()
    edu_type = data.get("edu_type")

    max_kurs = 5 if edu_type == "Bakalavr" else 2

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{i}-kurs",
                    callback_data=f"kurs_{i}",
                )
            ]
            for i in range(1, max_kurs + 1)
        ]
    )

    await call.message.answer("📚 Kursingizni tanlang:", reply_markup=kb)
    await state.set_state(RegState.student_course)
    await call.answer()


# 4) Kurs → guruh
@router.callback_query(RegState.student_course, F.data.startswith("kurs_"))
async def student_course(call: CallbackQuery, state: FSMContext):
    kurs = call.data.replace("kurs_", "")
    await state.update_data(student_course=kurs)

    await call.message.answer("✏️ Guruh nomini kiriting:")
    await state.set_state(RegState.student_group)
    await call.answer()


# 5) Guruh → FIO
@router.message(RegState.student_group)
async def student_group(message: Message, state: FSMContext):
    await state.update_data(student_group=message.text.strip())

    await message.answer("👤 To‘liq F.I.Sh kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegState.student_fio)


# 6) FIO → HEMIS
@router.message(RegState.student_fio)
async def student_fio(message: Message, state: FSMContext):
    await state.update_data(student_fio=message.text.strip())

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha", callback_data="s_hemis_yes")],
            [InlineKeyboardButton(text="Yo‘q", callback_data="s_hemis_no")],
        ]
    )
    await message.answer("📋 HEMISda ma’lumotlaringiz bormi?", reply_markup=kb)
    await state.set_state(RegState.student_hemis)


# 7) HEMIS — Yo‘q
@router.callback_query(RegState.student_hemis, F.data == "s_hemis_no")
async def student_hemis_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("❌ Siz HEMISda topilmadingiz.")
    await state.clear()
    await call.answer()


@router.callback_query(RegState.student_hemis, F.data == "s_hemis_yes")
async def student_hemis_yes(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🪪 Pasport seriya va raqamini kiriting (AB1234567):")
    await state.set_state(RegState.student_passport)
    await call.answer()

# 9) Pasport → Adminlarga yuboriladi
@router.message(RegState.student_passport)
async def student_finish(message: Message, state: FSMContext):
    await state.update_data(student_passport=message.text.strip())
    data = await state.get_data()

    await save_register_request(
        user_id=message.from_user.id,
        fio=data["student_fio"],
        phone=data["phone"],
        faculty=data["student_faculty"],
        department=None,
        passport=data["student_passport"],
        role="Talaba",
        edu_type=data["edu_type"],
        edu_form=data["edu_form"],
        course=data["student_course"],
        student_group=data["student_group"]
    )

    for admin in ADMINS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✔ Tasdiqlash",
                                      callback_data=f"approve_{message.from_user.id}")],
                [InlineKeyboardButton(text="❌ Rad etish",
                                      callback_data=f"reject_{message.from_user.id}")]
            ]
        )

        await message.bot.send_message(
            admin,
            (
                "📥 <b>Yangi Talaba so‘rovi:</b>\n"
                f"👤 {data['student_fio']}\n"
                f"📞 {data['phone']}\n"
                f"🎓 {data['edu_type']} | {data['edu_form']}\n"
                f"🏛 {data['student_faculty']}\n"
                f"📚 {data['student_course']}-kurs | Guruh: {data['student_group']}\n"
                f"🪪 Pasport: {data['student_passport']}"
            ),
            parse_mode="HTML",
            reply_markup=kb
        )

    await message.answer("✅ So‘rovingiz yuborildi. Admin tasdiqlashini kuting.")
    await state.clear()


async def start_registration(message: Message, state: FSMContext):
    await state.set_state(RegState.phone)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Kontaktni ulashish", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("📲 Telefon raqamingizni yuboring:", reply_markup=kb)
