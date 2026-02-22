# admin_message.py
# ============================
#  SUPER-PRO ADMIN / RAHBAR XABAR YUBORISH MODULI
# ============================

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from handlers.heads import SendMSG      # <-- asosiy FSM shu
from handlers.constants import FACULTIES

from database.db import (
    get_filtered_teachers,
    get_filtered_tutors,
    get_filtered_students
)

router = Router()


# =====================================================
#  1. XABAR YUBORISH BOSHLANISHI
# =====================================================
@router.message(F.text == "📨 Xabar yuborish")
async def start_send_msg(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍🏫 O‘qituvchi", callback_data="send_role_teacher"),
                InlineKeyboardButton(text="🧑‍🏫 Tyutor", callback_data="send_role_tutor"),
            ],
            [InlineKeyboardButton(text="🎓 Talaba", callback_data="send_role_student")],
            [InlineKeyboardButton(text="👥 Barchasi", callback_data="send_role_all")],
        ]
    )

    await message.answer("Xabarni kimga yubormoqchisiz?", reply_markup=kb)
    await state.set_state(SendMSG.role)



# =====================================================
# 2. ROLE TANLASH
# =====================================================
@router.callback_query(SendMSG.role, F.data.startswith("send_role_"))
async def set_role(call: CallbackQuery, state: FSMContext):
    role = call.data.replace("send_role_", "")
    await state.update_data(role=role)

    # Talaba → ta’lim turi
    if role == "student":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Bakalavr", callback_data="edu_type_bak")],
                [InlineKeyboardButton(text="Magistr", callback_data="edu_type_mag")],
                [InlineKeyboardButton(text="Barchasi", callback_data="edu_type_all")],
            ]
        )
        await call.message.answer("Ta’lim turini tanlang:", reply_markup=kb)
        await state.set_state(SendMSG.edu_type)
        await call.answer()
        return

    # Barchasi → darhol xabar
    if role == "all":
        await call.message.answer("Endi yubormoqchi bo‘lgan xabar matnini kiriting:")
        await state.set_state(SendMSG.msg)
        await call.answer()
        return

    # O‘qituvchi / Tyutor → fakultet
    faculties = FACULTIES + ["Barchasi"]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f, callback_data=f"send_fac_{f}")]
            for f in faculties
        ]
    )
    await call.message.answer("🏛 Qaysi fakultetga?", reply_markup=kb)
    await state.set_state(SendMSG.faculty)
    await call.answer()



# =====================================================
# 3. O‘QITUVCHI / TYUTOR OQIMI
# =====================================================
KAFEDRALAR = {

    "Aniq fanlar fakulteti": [
        "Fizika va astronomiya kafedrasi",
        "Matematika kafedrasi",
        "Raqamli texnologiyalar kafedrasi",
        "Barchasi"
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
        "Barchasi"
    ],

    "Maktabgacha va boshlang‘ich ta’lim fakulteti": [
        "Maktabgacha ta’lim kafedrasi",
        "Boshlang‘ich ta’lim kafedrasi",
        "Pedagogika kafedrasi",
        "Barchasi"
    ],

    "Tillar fakulteti": [
        "Fakultetlararo chet tillar kafedrasi",
        "Ingliz tili amaliy fanlar kafedrasi",
        "Ingliz tilshunosligi kafedrasi",
        "Qozoq tili va adabiyoti kafedrasi",
        "Rus tili va adabiyoti kafedrasi",
        "Barchasi"
    ],

    "O‘zbek filologiyasi fakulteti": [
        "O‘zbek tili va adabiyoti kafedrasi",
        "O‘zbek tilshunosligi kafedrasi",
        "Barchasi"
    ],

    "San’at va sport fakulteti": [
        "Jismoniy madaniyat kafedrasi",
        "Musiqiy ta’lim kafedrasi",
        "Sport faoliyati turlari kafedrasi",
        "Tasviriy san’at va muhandislik grafikasi kafedrasi",
        "Texnologik ta’lim kafedrasi",
        "Barchasi"
    ],

    "Tarix fakulteti": [
        "Ijtimoiy fanlar kafedrasi",
        "Milliy g‘oya, ma’naviyat asoslari va huquq kafedrasi",
        "Psixologiya kafedrasi",
        "Tarix kafedrasi",
        "Barchasi"
    ],

    "Iqtisodiyot fakulteti": [
        "Iqtisodiyot kafedrasi",
        "Barchasi"
    ],
}

@router.callback_query(SendMSG.faculty, F.data.startswith("send_fac_"))
async def choose_faculty(call: CallbackQuery, state: FSMContext):
    faculty = call.data.replace("send_fac_", "")
    await state.update_data(faculty=faculty)

    data = await state.get_data()
    role = data.get("role")

    # Tyutor → kafedra bosqichi yo‘q
    if role == "tutor":
        await call.message.answer("Tyutorning F.I.O ni kiriting yoki 'Barchasi':")
        await state.set_state(SendMSG.fio)
        await call.answer()
        return

    # Fakultet "Barchasi"
    if faculty == "Barchasi":
        await call.message.answer("O‘qituvchi F.I.O ni kiriting yoki 'Barchasi':")
        await state.set_state(SendMSG.fio)
        await call.answer()
        return

    kaf_list = KAFEDRALAR.get(faculty, ["Barchasi"])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=k, callback_data=f"send_kaf_{k}")]
            for k in kaf_list
        ]
    )

    await call.message.answer("🏢 Kafedrani tanlang:", reply_markup=kb)
    await state.set_state(SendMSG.department)
    await call.answer()


@router.callback_query(SendMSG.department, F.data.startswith("send_kaf_"))
async def choose_kafedra(call: CallbackQuery, state: FSMContext):
    kafedra = call.data.replace("send_kaf_", "")
    await state.update_data(department=kafedra)

    await call.message.answer("O‘qituvchi F.I.O yoki 'Barchasi':")
    await state.set_state(SendMSG.fio)
    await call.answer()

# TYUTOR / O‘QITUVCHI FIO KIRITISH
@router.message(SendMSG.fio)
async def set_teacher_or_tutor_fio(message: Message, state: FSMContext):
    txt = message.text.strip()
    await state.update_data(fio=None if txt.lower() == "barchasi" else txt)

    # 👉 Agar role tutor bo‘lsa — to‘g‘ri XABAR bosqichiga o‘tamiz
    data = await state.get_data()
    if data.get("role") == "tutor":
        await message.answer("Endi yubormoqchi bo‘lgan xabarni yuboring (matn yoki fayl):")
        await state.set_state(SendMSG.msg)
        return

    # 👉 O‘qituvchi bo‘lsa — xuddi shu handler ishlaydi
    await message.answer("Endi yubormoqchi bo‘lgan xabarni yuboring (matn yoki fayl):")
    await state.set_state(SendMSG.msg)


# =====================================================
# 4. TALABA OQIMI
# =====================================================

@router.callback_query(SendMSG.edu_type, F.data.startswith("edu_type_"))
async def choose_edu_type(call: CallbackQuery, state: FSMContext):
    edu_type = call.data.replace("edu_type_", "")
    await state.update_data(edu_type=edu_type)

    if edu_type == "bak":
        forms = ["Kunduzgi", "Kechki", "Sirtqi", "Masofaviy", "Barchasi"]
    elif edu_type == "mag":
        forms = ["Kunduzgi", "Kechki", "Masofaviy", "Barchasi"]
    else:
        forms = ["Barchasi"]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f, callback_data=f"edu_form_{f}")]
            for f in forms
        ]
    )

    await call.message.answer("Ta’lim shaklini tanlang:", reply_markup=kb)
    await state.set_state(SendMSG.edu_form)
    await call.answer()



@router.callback_query(SendMSG.edu_form, F.data.startswith("edu_form_"))
async def choose_edu_form(call: CallbackQuery, state: FSMContext):
    edu_form = call.data.replace("edu_form_", "")
    await state.update_data(edu_form=edu_form)

    faculties = FACULTIES + ["Barchasi"]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f, callback_data=f"stu_fac_{f}")]
            for f in faculties
        ]
    )

    await call.message.answer("Fakultetni tanlang:", reply_markup=kb)
    await state.set_state(SendMSG.stu_faculty)
    await call.answer()



@router.callback_query(SendMSG.stu_faculty, F.data.startswith("stu_fac_"))
async def choose_stu_faculty(call: CallbackQuery, state: FSMContext):
    fac = call.data.replace("stu_fac_", "")
    await state.update_data(stu_faculty=fac)

    data = await state.get_data()
    edu_type = data.get("edu_type")

    # Bakalavr → 1-5 kurs
    if edu_type == "bak":
        courses = [1, 2, 3, 4, 5]

    # Magistratura → 1-2 kurs
    elif edu_type == "mag":
        courses = [1, 2]

    # Barchasi → kurs tanlanmaydi
    else:
        courses = []

    if courses:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{i}-kurs", callback_data=f"course_{i}")]
                for i in courses
            ] + [[InlineKeyboardButton(text="Barchasi", callback_data="course_all")]]
        )
        await call.message.answer("Kursni tanlang:", reply_markup=kb)
        await state.set_state(SendMSG.course)
    else:
        # Agar "Barchasi" bo‘lsa → guruhga o‘tadi
        await call.message.answer("Guruh nomini yozing yoki 'Barchasi':")
        await state.set_state(SendMSG.group)

    await call.answer()


@router.callback_query(SendMSG.course, F.data.startswith("course_"))
async def choose_course(call: CallbackQuery, state: FSMContext):
    course = call.data.replace("course_", "")
    await state.update_data(course=course)

    await call.message.answer("Guruh nomini yozing yoki 'Barchasi':")
    await state.set_state(SendMSG.group)
    await call.answer()



@router.message(SendMSG.group)
async def set_group(message: Message, state: FSMContext):
    txt = message.text.strip()
    await state.update_data(group=None if txt.lower() == "barchasi" else txt)

    await message.answer("Talaba F.I.O yoki 'Barchasi':")
    await state.set_state(SendMSG.student_fio)



@router.message(SendMSG.student_fio)
async def set_student_fio(message: Message, state: FSMContext):
    txt = message.text.strip()
    await state.update_data(student_fio=None if txt.lower() == "barchasi" else txt)

    await message.answer("Endi yubormoqchi bo‘lgan xabarni yuboring (matn/fayl):")
    await state.set_state(SendMSG.msg)

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import F

# =====================================================
# 5. YAKUNIY XABARNI YUBORISH (FIXED)
# =====================================================
from database.utils import get_sender_info


@router.message(SendMSG.msg, F.text | F.photo | F.video | F.document)
async def send_result(message: Message, state: FSMContext):
    data = await state.get_data()

    teacher_count = 0
    tutor_count = 0
    student_count = 0

    teachers = []
    tutors = []
    students = []

    # 🔥 ASYNC FIX
    if data.get("role") in ["teacher", "all"]:
        teachers = await get_filtered_teachers(data)

    if data.get("role") in ["tutor", "all"]:
        tutors = await get_filtered_tutors(data)

    if data.get("role") in ["student", "all"]:
        students = await get_filtered_students(data)

    # 🎯 Sender info
    lavozim, fio = await get_sender_info(
        message.from_user.id,
        message.from_user.full_name
    )

    header = (
        "🏛 <b>Navoiy Davlat Universiteti</b>\n"
        f"📢 <b>{lavozim}: {fio}</b>\n"
        "--------------------------------------\n\n"
    )

    footer = (
        "\n\n--------------------------------------\n"
        "🕒 Xabar avtomatik tarzda yuborildi."
    )

    async def send_to_user(uid: int):
        if message.text:
            await message.bot.send_message(
                uid,
                header + message.text + footer,
                parse_mode="HTML"
            )

        elif message.photo:
            await message.bot.send_photo(
                uid,
                message.photo[-1].file_id,
                caption=header + (message.caption or "") + footer,
                parse_mode="HTML"
            )

        elif message.video:
            await message.bot.send_video(
                uid,
                message.video.file_id,
                caption=header + (message.caption or "") + footer,
                parse_mode="HTML"
            )

        elif message.document:
            await message.bot.send_document(
                uid,
                message.document.file_id,
                caption=header + (message.caption or "") + footer,
                parse_mode="HTML"
            )

    # 🔥 Yuborish
    for t in teachers:
        uid = getattr(t, "user_id", None)
        if uid:
            try:
                await send_to_user(uid)
                teacher_count += 1
            except Exception as e:
                print("[SEND ERROR][TEACHER]", uid, e)

    for t in tutors:
        uid = getattr(t, "user_id", None)
        if uid:
            try:
                await send_to_user(uid)
                tutor_count += 1
            except Exception as e:
                print("[SEND ERROR][TUTOR]", uid, e)

    for s in students:
        uid = getattr(s, "user_id", None)
        if uid:
            try:
                await send_to_user(uid)
                student_count += 1
            except Exception as e:
                print("[SEND ERROR][STUDENT]", uid, e)

    await message.answer(
        "✅ <b>Xabar yuborildi:</b>\n"
        f"👨‍🏫 O‘qituvchilar: {teacher_count}\n"
        f"🧑‍🏫 Tyutorlar: {tutor_count}\n"
        f"🎓 Talabalar: {student_count}",
        parse_mode="HTML"
    )

    await state.clear()
