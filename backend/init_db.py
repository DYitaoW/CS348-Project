"""
Initialize the database schema.

Run this once after setting DATABASE_URL to create all tables.
Example:
  export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/soccerdb
  python init_db.py
"""

from db import engine, Base
import models  # noqa: F401  # Ensures model classes are registered with Base


def main() -> None:
    # This issues CREATE TABLE statements for all models in Base metadata.
    Base.metadata.create_all(bind=engine)
    print("Database schema created.")


if __name__ == "__main__":
    main()
