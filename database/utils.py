# handlers/utils.py

import os

from .models import Question  # yoki sizda qayerda bo‘lsa
from io import BytesIO
from data.config import RAHBARLAR, MANAGERS_BY_FACULTY
from database.db import get_student, get_teacher
from openpyxl import Workbook
from loguru import logger
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import UserActivity
from database.models import User
from collections import defaultdict

async def send_long_message(message, text, chunk=4000):
    for i in range(0, len(text), chunk):
        await message.answer(
            text[i:i + chunk],
            parse_mode="HTML"
        )

async def get_sender_info(user_id: int, full_name: str):
    """
    Rahbar yoki menejer lavozimini aniqlaydi
    return: (lavozim, fio)
    """

    # 1️⃣ Global rahbarlar
    for role_name, ids in RAHBARLAR.items():
        if user_id in ids:
            return role_name, full_name

    # 2️⃣ Fakultet menejerlari
    for faculty, roles in MANAGERS_BY_FACULTY.items():
        if user_id in (roles.get("teacher", []) + roles.get("student", [])):
            return f"{faculty} menejeri", full_name

    # 3️⃣ Teachers jadvalidan
    teacher = await get_teacher(user_id)
    if teacher:
        return teacher.role or "Rahbar", teacher.fio or full_name

    return "Rahbar", full_name

# =============================
# 📊 Excel export
# =============================

async def generate_excel(rows, bot):

    wb = Workbook()
    ws = wb.active
    ws.title = "Murojaatlar"

    headers = [
        "№",
        "Sana",
        "Foydalanuvchi",
        "Rol",
        "Fakultet",
        "Savol",
        "Javob",
        "Menejer"
    ]

    ws.append(headers)

    for i, row in enumerate(rows, 1):

        manager_name = ""

        if row.manager_id:
            try:
                chat = await bot.get_chat(row.manager_id)
                manager_name = chat.full_name
            except:
                manager_name = str(row.manager_id)

        ws.append([
            i,
            row.created_at.strftime("%Y-%m-%d %H:%M"),
            row.fio,
            row.sender_role,
            row.faculty,
            row.message_text,
            row.answer_text,
            manager_name
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer

async def log_activity(user_id: int, role: str, command: str):
    async with AsyncSessionLocal() as session:
        try:
            session.add(UserActivity(
                user_id=user_id,
                role=role,
                command=command
            ))
            await session.commit()
        except Exception as e:
            await session.rollback()
            print("LOG ERROR:", e)


async def export_activity_excel():

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserActivity))
        rows = result.scalars().all()

    stats = defaultdict(lambda: {
        "fio": "",
        "role": "",
        "commands": defaultdict(int),
        "last": None
    })

    # 🔥 USER NOMINI OLISH FUNKSIYA
    async def get_user_name(user_id):
        from database.db import get_student, get_teacher
        from database.models import Manager
        from data.config import RAHBARLAR

        # ✅ STUDENT
        student = await get_student(user_id)
        if student:
            return student.fio

        # ✅ TEACHER / TUTOR
        teacher = await get_teacher(user_id)
        if teacher:
            return teacher.fio

        # ✅ MANAGER (DB dan)
        async with AsyncSessionLocal() as s:
            res = await s.execute(
                select(Manager).where(Manager.telegram_id == user_id)
            )
            manager = res.scalar_one_or_none()
            if manager:
                return manager.fio

        # 🔥 ✅ RAHBARLAR (CONFIG dan)
        for role_name, ids in RAHBARLAR.items():
            if user_id in ids:
                return f"{role_name} (Rahbar)"

        # fallback
        return str(user_id)

    # 🔥 DATA YIG‘ISH
    for r in rows:
        user = stats[r.user_id]

        user["role"] = r.role
        user["commands"][r.command] += 1

        if r.created_at and (not user["last"] or r.created_at > user["last"]):
            user["last"] = r.created_at

    # 🔥 EXCEL
    wb = Workbook()
    ws = wb.active
    ws.title = "Faollik"

    ws.append([
        "F.I.O",
        "Rol",
        "Buyruq",
        "Necha marta",
        "Oxirgi aktivlik"
    ])

    # 🔥 HAR BIR USER + COMMAND
    for user_id, data in stats.items():

        fio = await get_user_name(user_id)

        for cmd, count in data["commands"].items():
            ws.append([
                fio,
                data["role"],
                cmd,
                count,
                data["last"].strftime("%Y-%m-%d %H:%M") if data["last"] else ""
            ])

    filename = f"activity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    wb.save(filename)

    return filename

UTC = timezone.utc

from datetime import datetime, timedelta

async def get_users_for_notification(hours=12):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserActivity))
        rows = result.scalars().all()

    last_activity = {}
    last_notified = {}

    for r in rows:
        # oxirgi activity
        if (
            r.user_id not in last_activity
            or last_activity.get(r.user_id) is None
            or (
                r.created_at is not None
                and r.created_at > last_activity[r.user_id]
            )
        ):
            last_activity[r.user_id] = r.created_at

        # oxirgi notify
        last_time = last_notified.get(r.user_id)

        if r.user_id not in last_notified or (
                r.last_notified_at is not None and
                (last_time is None or r.last_notified_at > last_time)
        ):
            last_notified[r.user_id] = r.last_notified_at

    now = datetime.utcnow()
    users = []

    for user_id, last_time in last_activity.items():
        if last_time is None:
            inactive = True
        else:
            inactive = now - last_time > timedelta(hours=hours)

        already_notified = False
        if user_id in last_notified and last_notified[user_id]:
            already_notified = now - last_notified[user_id] < timedelta(hours=hours)

        if inactive and not already_notified:
            users.append(user_id)

    return users

async def send_daily_notifications(bot):
    all_users = await get_all_users()
    inactive_users = await get_users_for_notification(48)

    users = [u for u in all_users if u in inactive_users]

    async with AsyncSessionLocal() as session:
        for uid in users:
            try:
                await bot.send_message(
                    uid,
                    "👋 Assalomu alaykum, NDUteachers_bot foydalanuvchisi!\n\n"
                    "📌 Siz 2 kundan beri bot imkoniyatlaridan foydalanmadingiz.\n"
                    "AI ko'makchisi yaqin kunlarda ishga tushadi!"
                )
                # 🔥 UPDATE
                result = await session.execute(
                    select(UserActivity).where(UserActivity.user_id == uid)
                )
                user = result.scalars().first()

                if user:
                    user.last_notified_at = datetime.utcnow()

            except Exception as e:
                print("ERROR:", e)

        await session.commit()

from database.models import Student, Teacher, Manager
from sqlalchemy import select

async def get_all_users():
    async with AsyncSessionLocal() as session:
        users = set()

        # 🧑‍🎓 studentlar
        result = await session.execute(select(Student.user_id))
        users.update(result.scalars().all())

        # 👨‍🏫 teacherlar
        result = await session.execute(select(Teacher.user_id))
        users.update(result.scalars().all())

        # 🧑‍💼 managerlar
        result = await session.execute(select(Manager.telegram_id))
        users.update(result.scalars().all())

    return list(users)


async def get_unanswered_questions(session):
    time_limit = datetime.utcnow() - timedelta(minutes=10)

    result = await session.execute(
        select(Question).where(
            Question.answered == False,   # ❗ sizga moslab o‘zgartirdim
            Question.created_at <= time_limit
        )
    )

    return result.scalars().all()

import re

def normalize_text(text: str):
    if not text:
        return ""

    text = text.lower()

    # barcha apostroflarni bir xil qilish
    text = text.replace("‘", "'").replace("`", "'").replace("ʼ", "'")

    # o‘ -> o, g‘ -> g
    text = text.replace("o'", "o").replace("g'", "g")

    # ortiqcha belgilarni olib tashlash
    text = re.sub(r"[^a-z0-9\s]", "", text)

    return text.strip()