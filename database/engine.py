# database/engine.py

from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base
from data.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)


async def init_db():
    async with engine.begin() as conn:

        # 🔥 1. questions uchun (sizda bor)
        await conn.exec_driver_sql(
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS manager_id BIGINT"
        )

        # 🔥 2. user_activity uchun (YANGI)
        await conn.exec_driver_sql(
            """
            ALTER TABLE user_activity
            ADD COLUMN IF NOT EXISTS last_notified_at TIMESTAMP
            """
        )

        # 🔥 table yaratish
        await conn.run_sync(Base.metadata.create_all)