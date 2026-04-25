#export_students_excel.py
import pandas as pd
import asyncio
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text
import os
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

    # Kurs
    "kurs": "kursdan-kursga o‘tkazish",
    "kursdan kursga": "kursdan-kursga ko'chirish",
    "qayta o‘qish": "qayta o‘qish uchun kursda qoldirilgan",
    "qayta kurs": "qayta o‘qish uchun kursdan-kursga qoldirish",

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

def split_name(name):
    if not name:
        return "", ""

    parts = name.strip().split()

    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    else:
        return parts[0], parts[1]

def make_hyperlink(link, text):
    # Excel formula (ENG TO‘G‘RI USUL)
    return f'=HYPERLINK("{link}", "{text}")'


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

    # 🔥 FAST INDEX (familiya → ism → orders)
    db_map = {}

    for order in orders:
        students = (order.students_raw or "").split(",")

        for s in students:
            key = normalize_text(s)
            last, first = split_name(key)

            if last not in db_map:
                db_map[last] = {}

            if first not in db_map[last]:
                db_map[last][first] = []

            db_map[last][first].append(order)

    # 🔥 COLUMN MAP normalize
    normalized_column_map = {
        normalize_text(k): v for k, v in COLUMN_MAP.items()
    }

    # 🔥 Excel bo‘yicha yuramiz
    for i, row in df.iterrows():

        fio = str(row[FIO_COLUMN]).strip()
        key = normalize_text(fio)

        fio_last, fio_first = split_name(key)

        # ⚡ O(1) lookup
        student_orders = db_map.get(fio_last, {}).get(fio_first, [])

        if not student_orders:
            continue

        latest_map = {}

        for order in student_orders:
            order_type = normalize_text(order.type or "")

            for k, col in normalized_column_map.items():
                if k in order_type:
                    latest_map.setdefault(
                        col,
                        make_hyperlink(order.link, order.title)
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
