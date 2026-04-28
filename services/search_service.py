import os
import psycopg2
from sqlalchemy import select

from database.models import OrderLink
from database.session import AsyncSessionLocal
from sqlalchemy import or_

def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL topilmadi")
    return psycopg2.connect(database_url)


def normalize_text(text: str) -> str:
    return (text or "").lower().strip()


def search_orders(first_name, last_name):
    conn = get_connection()
    try:
        cur = conn.cursor()

        search_text = f"{first_name} {last_name}".lower()

        cur.execute(
            """
            SELECT id, link
            FROM order_links
            WHERE students_search ILIKE %s
            LIMIT 10
            """,
            (f"%{search_text}%",)
        )

        rows = cur.fetchall()

        return [{"name": f"Buyruq #{r[0]}", "link": r[1]} for r in rows]

    finally:
        conn.close()


async def search_orders_multi(
    faculty: str | None = None,
    type: str | None = None,
    fio: str | None = None,
):
    async with AsyncSessionLocal() as session:
        stmt = select(OrderLink)

        if faculty:
            stmt = stmt.where(OrderLink.faculty == faculty)

        if type:
            stmt = stmt.where(OrderLink.type == type)

        if fio:
            search_text = normalize_text(fio)
            parts = [p for p in search_text.split() if len(p) >= 3]

            stmt = stmt.where(
                or_(*[
                    OrderLink.students_search.ilike(f"%{p}%")
                    for p in parts
                ])
            )

        result = await session.execute(stmt)
        rows = result.scalars().all()

        # 🔥 Python tarafda filter qilamiz
        filtered = []

        for row in rows:
            text = row.students_search or ""
            count = sum(1 for p in parts if p in text)

            if count >= max(2, len(parts) - 1):  # kamida 2 yoki deyarli hammasi
                filtered.append(row)

        rows = filtered