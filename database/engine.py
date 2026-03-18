# database/engine.py

from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base
from data.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)


async def init_db():
    async with engine.begin() as conn:

        # 🔥 COLUMN QO‘SHISH
        await conn.exec_driver_sql(
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS manager_id BIGINT"
        )

        # 🔥 TABLE YARATISH (agar yo‘q bo‘lsa)
        await conn.run_sync(Base.metadata.create_all)