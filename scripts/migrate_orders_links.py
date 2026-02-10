import asyncio
from sqlalchemy import text, select
from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text


async def migrate_orders():
    async with AsyncSessionLocal() as session:
        # 1️⃣ Eski jadvaldan hamma buyruqlarni olamiz
        result = await session.execute(
            text("""
                SELECT
                    id,
                    title,
                    link,
                    year,
                    faculty,
                    type,
                    students,
                    created_at
                FROM orders_links
            """)
        )

        rows = result.fetchall()
        print(f"🔄 {len(rows)} ta eski buyruq topildi")

        if not rows:
            print("⚠️ Ko‘chiriladigan buyruq yo‘q")
            return

        inserted = 0

        for r in rows:
            students_raw = r.students or ""
            students_search = normalize_text(students_raw)

            order = OrderLink(
                title=r.title,
                link=r.link,
                year=r.year,
                faculty=r.faculty,
                type=r.type,
                students_raw=students_raw,
                students_search=students_search,
                created_at=r.created_at,
            )

            session.add(order)
            inserted += 1

        await session.commit()
        print(f"✅ {inserted} ta buyruq muvaffaqiyatli ko‘chirildi")


if __name__ == "__main__":
    asyncio.run(migrate_orders())
