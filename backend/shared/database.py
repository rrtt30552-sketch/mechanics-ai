"""
Database - SQLAlchemy async engine & session
Supports PostgreSQL (production) and SQLite (local dev/testing)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    # Local dev: use SQLite
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'mech_ai.db')
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(DB_PATH)}"
    USE_SQLITE = True
else:
    USE_SQLITE = "sqlite" in DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables and initialize pgvector extension (if available)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize pgvector extension only for PostgreSQL
    if not USE_SQLITE:
        try:
            from shared.rag import init_vector_extension
            await init_vector_extension(engine)
        except Exception:
            pass
