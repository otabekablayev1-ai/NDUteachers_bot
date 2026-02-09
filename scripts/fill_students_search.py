# scripts/fill_students_search.py
import asyncio
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text

async def fill_students_search():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderLink))
        rows = result.scalars().all()

        print(f"🔄 {len(rows)} ta buyruq yangilanmoqda...")

        for order in rows:
            if order.students_raw:
                order.students_search = normalize_text(order.students_raw)

        await session.commit()
        print("✅ Migration tugadi!")

if __name__ == "__main__":
    asyncio.run(fill_students_search())
