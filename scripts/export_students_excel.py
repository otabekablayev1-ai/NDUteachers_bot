#export_students_excel.py
import pandas as pd
import asyncio
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text
import os
import re

# 🔥 KENGAYTIRILGAN MAPPING
COLUMN_MAP = {
    # Qabul
    "qabul": "talabalar safiga qabul",
    "qo‘shimcha qabul": "talabalari safiga qo‘shimcha qabul",
    "magistr qabul": "magistrlikka tavsiya etilgan talabgorlarni o‘qishga qabul qilish",

    # Ko‘chirish
    "kochirish": "o‘qishini ko‘chirish",
    "ko'chirish": "o‘qishini ko‘chirish",

    # Tiklash
    "tiklash": "o‘qishga tiklash",
    "oqishni tiklash": "o‘qishini tiklashga",
    "o‘qish tiklash": "o‘qish tiklash",

    # ❌ KURS BLOK O‘CHIRILDI

    # Ta'lim shakli
    "sirtqi": "sirtqi ta’lim shakliga o‘tkazish",
    "ta'lim shakli": "ta'lim shakliga o'tkazish",
    "talim kochirish": "ta'lim shakliga ko'chirish",

    # Akademik
    "akademik mobillik": "akademik mobillik",
    "amaliyot": "amaliyot",
    "tatil": "akademik ta'til",

    # Shaxsiy
    "familiya": "familiya o'zgartirish",

    # Chetlashtirish
    "chetlashtirish": "talabalar safidan chetlashtirish",

    # Yakuniy
    "attestatsiya": "yakuniy davlat attestatsiyalarini topshirishga ruxsat",
    "magistr": "magistrlik dissertatsiya",
    "diplom": "diplom berish"
}

# 🔥 KURSNI AJRATISH
def extract_course_transition(text: str):
    if not text:
        return None

    text = text.lower()

    match = re.search(r'(\d)\s*[-]?\s*kursdan.*?(\d)\s*[-]?\s*kursga', text)

    if match:
        return int(match.group(1)), int(match.group(2))

    return None


# 🔥 USTUN NOMI
def get_course_column(from_kurs, to_kurs):
    return f"kurs_{from_kurs}_{to_kurs}"


# 🔥 FIO SPLIT
def split_name(name):
    if not name:
        return "", ""

    parts = name.strip().split()

    if len(parts) >= 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], ""

    return "", ""


# 🔥 EXCEL LINK
def make_hyperlink(link, text):
    return f'=HYPERLINK("{link}", "{text}")'


# 🔥 ASOSIY FUNKSIYA
async def fill_excel():
    file_path = "files/Talabalar 21.04.2026.xlsx"
    output_path = "files/output_filled.xlsx"

    df = pd.read_excel(file_path)
    df = df.astype(str)

    # 🔍 FIO ustunni topish
    FIO_COLUMN = None
    for col in df.columns:
        if "fio" in col.lower() or "ism" in col.lower():
            FIO_COLUMN = col
            break

    if not FIO_COLUMN:
        raise Exception("FIO ustuni topilmadi")

    print("FIO ustuni:", FIO_COLUMN)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderLink))
        orders = result.scalars().all()

    print(f"DB orders: {len(orders)}")

    # 🔥 FAST INDEX
    db_map = {}

    for order in orders:
        students = (order.students_raw or "").split(",")

        for s in students:
            key = normalize_text(s)
            last, first = split_name(key)

            db_map.setdefault(last, {}).setdefault(first, []).append(order)

    # 🔥 Excel bo‘yicha yuramiz
    for i, row in df.iterrows():

        fio = str(row[FIO_COLUMN]).strip()
        key = normalize_text(fio)

        fio_last, fio_first = split_name(key)

        student_orders = db_map.get(fio_last, {}).get(fio_first, [])

        if not student_orders:
            continue

        latest_map = {}

        for order in student_orders:

            # 🔥 1. KURS MAPPING (ENG MUHIM)
            # 🔥 KURS FILTER (ENG MUHIM FIX)
            if (
                    order.course_from
                    and order.course_to
                    and 1 <= order.course_from <= 5
                    and 1 <= order.course_to <= 5
                    and order.course_to == order.course_from + 1
            ):
                col_name = f"kurs_{order.course_from}_{order.course_to}"

                if col_name in df.columns:
                    latest_map[col_name] = make_hyperlink(
                        order.link,
                        order.title
                    )

        # 🔥 Excelga yozish
        for col, val in latest_map.items():
            df.at[i, col] = val

    # 🔥 eski faylni o‘chirish
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except PermissionError:
            print("❌ Excel ochiq, yoping!")
            return

    df.to_excel(output_path, index=False, engine="openpyxl")

    print("✅ FINAL Excel tayyor!")

if __name__ == "__main__":
    asyncio.run(fill_excel())