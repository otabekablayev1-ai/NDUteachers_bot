import asyncio
from sqlalchemy import select

from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text


async def fix_students_search():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderLink))
        orders = result.scalars().all()

        print(f"Topildi: {len(orders)} ta order")

        for order in orders:
            order.students_search = normalize_text(order.students_raw)

        await session.commit()
        print("✅ Hammasi yangilandi!")


if __name__ == "__main__":
    asyncio.run(fix_students_search())