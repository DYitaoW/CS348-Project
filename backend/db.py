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

# Railway's Postgres template sets DATABASE_URL with the generic
# "postgresql://" scheme, which causes SQLAlchemy to default to the
# psycopg2 driver. Rewrite it to the explicit psycopg (v3) driver
# scheme so SQLAlchemy uses the psycopg package in requirements.txt.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


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
