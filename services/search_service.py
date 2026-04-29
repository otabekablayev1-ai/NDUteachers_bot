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
            stmt = stmt.where(
                OrderLink.students_search.ilike(f"%{search_text}%")
            )

        stmt = stmt.order_by(OrderLink.created_at.desc())

        result = await session.execute(stmt)
        return result.all()
