from sqlalchemy.ext.asyncio import async_sessionmaker
from database.engine import engine
from sqlalchemy.orm import sessionmaker
from database.engine import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

