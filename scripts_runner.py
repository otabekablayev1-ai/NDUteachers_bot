from database.models import OrderLink
from database.session import AsyncSessionLocal
from database.utils import normalize_text
from sqlalchemy import select

async def rebuild_students_search():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderLink))
        rows = result.scalars().all()

        updated = 0
        for r in rows:
            if r.students_raw:
                new_val = normalize_text(r.students_raw)
                if r.students_search != new_val:
                    r.students_search = new_val
                    updated += 1

        await session.commit()
        return updated
