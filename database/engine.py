# database/engine.py
from sqlalchemy.ext.asyncio import create_async_engine
from data.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

from database.engine import engine
from database.models import Base

Base.metadata.create_all(bind=engine)