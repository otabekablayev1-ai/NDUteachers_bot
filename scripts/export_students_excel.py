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

    # 🔥 FIO ustunni avtomatik topish
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

        db_map = {}

        # 🔥 DB ni mapga aylantiramiz
        for order in orders:
            students = (order.students_raw or "").split(",")

            for s in students:
                key = normalize_text(s)

                if key not in db_map:
                    db_map[key] = []

                db_map[key].append(order)

        # 🔥 Excel bo‘yicha yuramiz
        for i, row in df.iterrows():

            fio = str(row[FIO_COLUMN]).strip()
            key = normalize_text(fio)

            fio_last, fio_first = split_name(key)

            student_orders = []

            # 🔥 TO‘G‘RI MATCH (familiya + ism)
            for db_key, orders_list in db_map.items():
                db_last, db_first = split_name(db_key)

                if fio_last == db_last and fio_first == db_first:
                    student_orders.extend(orders_list)

            if not student_orders:
                continue

            latest_map = {}

            # 🔥 ustunlarga ajratamiz
            for order in student_orders:
                order_type = normalize_text(order.type or "")

                for k, col in COLUMN_MAP.items():
                    if normalize_text(k) in order_type:

                        latest_map[col] = make_hyperlink(
                            order.link,
                            order.title
                        )

            # 🔥 Excelga yozamiz
            for col, val in latest_map.items():
                df.at[i, col] = val

    # 🔥 agar fayl ochiq bo‘lsa error bermasin
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
if __name__ == "__main__":
    asyncio.run(fill_excel())