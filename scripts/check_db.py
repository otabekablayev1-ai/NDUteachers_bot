import asyncio
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import OrderLink

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OrderLink.students_raw, OrderLink.students_search)
            .where(OrderLink.students_raw.ilike("%ABDUMURODOVA%"))
            .limit(5)
        )

        rows = result.all()

        for raw, search in rows:
            print("RAW:", raw)
            print("SEARCH:", search)
            print("-----")

asyncio.run(check())