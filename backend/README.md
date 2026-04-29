Backend (Flask + SQLAlchemy + PostgreSQL)

Setup
1) Create a virtual environment and install deps:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Set DATABASE_URL (local example):
   export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/soccerdb

3) Create tables:
   python init_db.py

4) Run the server:
   python app.py

Notes
- In AWS, set DATABASE_URL via environment variables (Elastic Beanstalk/ECS).
- Use PostgreSQL on RDS for the production database.
