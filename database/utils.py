# handlers/utils.py

import os

from io import BytesIO
from data.config import RAHBARLAR, MANAGERS_BY_FACULTY
from database.db import get_student, get_teacher
from sqlalchemy import select
from openpyxl import Workbook
from datetime import datetime

from datetime import datetime, timedelta
from database.session import AsyncSessionLocal
from database.models import UserActivity

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


from collections import defaultdict

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

        if not user["last"] or r.created_at > user["last"]:
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


async def get_users_for_notification(hours=24):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserActivity))
        rows = result.scalars().all()

    users = {}

    for r in rows:
        if r.user_id not in users:
            users[r.user_id] = r
        else:
            if r.created_at > users[r.user_id].created_at:
                users[r.user_id] = r

    now = datetime.utcnow()
    result_users = []

    for user_id, r in users.items():
        inactive = now - r.created_at > timedelta(hours=hours)

        # ❗ faqat 1 marta yuborish (24h ichida qayta yubormaydi)
        already_notified = (
            r.last_notified_at and
            now - r.last_notified_at < timedelta(hours=24)
        )

        if inactive and not already_notified:
            result_users.append(user_id)

    return result_users

async def send_daily_notifications(bot):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserActivity))
        rows = result.scalars().all()

    users = await get_users_for_notification()

    for uid in users:
        try:
            await bot.send_message(
                uid,
                "👋 Assalomu alaykum!\n\n"
                "📌 Siz bugun botdan foydalanmadingiz.\n"
                "Yangi buyruqlarni tekshirib ko‘ring!"
            )

            # 🔥 notified vaqtini update qilish
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UserActivity).where(UserActivity.user_id == uid)
                )
                user = result.scalars().first()

                if user:
                    user.last_notified_at = datetime.utcnow()
                    await session.commit()

        except Exception as e:
            print("NOTIFY ERROR:", uid, e)

