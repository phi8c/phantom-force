from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from app.shared.config.settings import (
    settings,
)
print("in ra url", settings.DATABASE_URL)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)
print(" in ra engine", engine)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)