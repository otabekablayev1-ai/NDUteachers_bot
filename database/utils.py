# handlers/utils.py

import os
import re
from io import BytesIO
from data.config import RAHBARLAR, MANAGERS_BY_FACULTY
from database.db import get_teacher
from sqlalchemy import select
from openpyxl import Workbook
from datetime import datetime


from database.session import AsyncSessionLocal
from database.models import UserActivity

async def send_long_message(message, text, chunk=4000):
    for i in range(0, len(text), chunk):
        await message.answer(
            text[i:i + chunk],
            parse_mode="HTML"
        )
def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[‘’ʻʼ`´]", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()



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
        result = await session.execute(
            select(UserActivity)
        )
        rows = result.scalars().all()

    stats = {}

    for r in rows:
        if r.user_id not in stats:
            stats[r.user_id] = {
                "count": 0,
                "last": r.created_at,
                "role": r.role
            }

        stats[r.user_id]["count"] += 1

        if r.created_at > stats[r.user_id]["last"]:
            stats[r.user_id]["last"] = r.created_at

    wb = Workbook()
    ws = wb.active
    ws.title = "Faollik"

    ws.append([
        "User ID",
        "Rol",
        "Foydalanish soni",
        "Oxirgi aktivlik"
    ])

    for uid, data in stats.items():
        ws.append([
            uid,
            data["role"],
            data["count"],
            data["last"].strftime("%Y-%m-%d %H:%M")
        ])

    filename = f"activity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    path = os.path.join(os.getcwd(), filename)

    wb.save(path)

    return path

