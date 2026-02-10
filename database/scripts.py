from database.utils import normalize_text
from database.models import OrderLink
from database.session import AsyncSessionLocal
from sqlalchemy import select

async def rebuild_students_search():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderLink))
        rows = result.scalars().all()

        for r in rows:
            if r.students_raw:
                r.students_search = normalize_text(r.students_raw)

        await session.commit()