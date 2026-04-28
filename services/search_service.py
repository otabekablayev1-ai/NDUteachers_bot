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
        stmt = select(
            OrderLink.id,
            OrderLink.title,
            OrderLink.link,
            OrderLink.faculty,
            OrderLink.type,
            OrderLink.students_raw,
            OrderLink.students_search,
            OrderLink.created_at,
        )

        if faculty:
            stmt = stmt.where(OrderLink.faculty == faculty)

        if type:
            stmt = stmt.where(OrderLink.type == type)

        if fio:
            search_text = normalize_text(fio)
            parts = search_text.split()

            conditions = []

            for p in parts:
                if len(p) >= 3:
                    conditions.append(
                        OrderLink.students_search.ilike(f"%{p}%")
                    )

            stmt = stmt.where(or_(*conditions))
            
        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                "id": row[0],
                "name": row[1] or f"Buyruq #{row[0]}",
                "link": row[2],
                "faculty": row[3],
                "type": row[4],
                "students_raw": row[5],
                "students_search": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]