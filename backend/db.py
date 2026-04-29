import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Example: "
        "postgresql+psycopg://user:password@localhost:5432/soccerdb"
    )


# Declarative base class for models
class Base(DeclarativeBase):
    pass


# Engine manages the DB connection pool. Echo=True prints SQL for debugging.
# Concurrency note:
# - For PostgreSQL we configure SERIALIZABLE isolation to provide strong
#   correctness guarantees under concurrent users.
# - SERIALIZABLE can raise "serialization failures" (SQLSTATE 40001). The app
#   should catch and retry those transactions.
# - For SQLite (local dev), this setting is not applied.
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs["isolation_level"] = "SERIALIZABLE"

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory. Each request should create its own session.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
