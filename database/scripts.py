from database.models import OrderLink
from database.session import AsyncSessionLocal
from sqlalchemy import select
from database.db import normalize_text  # normalize_text shu faylda bo‘lsa

async def rebuild_students_search():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderLink))
        rows = result.scalars().all()

        updated = 0
        for r in rows:
            if r.students_raw:
                normalized = normalize_text(r.students_raw)
                if not r.students_search or r.students_search != normalized:
                    r.students_search = normalized
                    updated += 1

        await session.commit()
        return updated

