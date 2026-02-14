# handlers/utils.py
import re
import unicodedata

async def send_long_message(message, text, chunk=4000):
    for i in range(0, len(text), chunk):
        await message.answer(
            text[i:i + chunk],
            parse_mode="HTML"
        )

import re

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[‘’ʻʼ`´]", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

from data.config import RAHBARLAR, MANAGERS_BY_FACULTY
from database.db import get_teacher


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

