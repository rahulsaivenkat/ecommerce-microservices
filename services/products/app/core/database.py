from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.core.config import get_settings

engine = create_async_engine(get_settings().DATABASE_URL)
SessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)

Base = declarative_base()

async def get_db() -> Generator:
    async with SessionLocal() as db:
        yield db
