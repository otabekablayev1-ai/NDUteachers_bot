# database/engine.py
from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base
from data.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)


async def init_db():
    async with engine.begin() as conn:

        await conn.exec_driver_sql(
            "ALTER TABLE managers ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY"
        )

        await conn.exec_driver_sql(
            "ALTER TABLE managers ADD COLUMN IF NOT EXISTS telegram_id BIGINT"
        )

        await conn.exec_driver_sql(
            "ALTER TABLE managers ADD COLUMN IF NOT EXISTS fio VARCHAR"
        )

        await conn.exec_driver_sql(
            "ALTER TABLE managers ADD COLUMN IF NOT EXISTS position VARCHAR"
        )

        await conn.exec_driver_sql(
            "ALTER TABLE managers ADD COLUMN IF NOT EXISTS faculty VARCHAR"
        )

        await conn.run_sync(Base.metadata.create_all)