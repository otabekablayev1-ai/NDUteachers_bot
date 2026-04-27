import asyncio
from sqlalchemy import text
from database.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            ALTER TABLE order_links
            ADD COLUMN IF NOT EXISTS course_from INTEGER;
        """))

        await session.execute(text("""
            ALTER TABLE order_links
            ADD COLUMN IF NOT EXISTS course_to INTEGER;
        """))

        await session.commit()

    print("✅ course_from va course_to ustunlari qo‘shildi")


if __name__ == "__main__":
    asyncio.run(main())