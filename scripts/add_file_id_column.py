import asyncio
from sqlalchemy import text
from database.session import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("ALTER TABLE order_links ADD COLUMN file_id TEXT;"))
            print("✅ file_id qo‘shildi")
        except Exception as e:
            print("⚠️ Ehtimol allaqachon mavjud:", e)

        try:
            await session.execute(text("ALTER TABLE order_links ADD CONSTRAINT unique_file_id UNIQUE (file_id);"))
            print("✅ unique constraint qo‘shildi")
        except Exception as e:
            print("⚠️ Constraint mavjud:", e)

        await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate())