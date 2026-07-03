"""Tao session factory cho SQLAlchemy.

KHONG tao engine/session o module-level (khong co bien global ket noi san) de
tranh ket noi DB that ngay khi module nay duoc import - quan trong cho test
(tests/test_job_repository.py dung SQLite in-memory qua make_session_factory,
khong dung DEFAULT_DATABASE_URL/Postgres that).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

load_dotenv()

# Port 15432 (khong phai 5432 mac dinh) de khop docker-compose.yml - may dev co
# san Postgres native chiem 5432 (xem HANDOFF.md nhat ky 2026-07-03 lan 7).
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://subtitle_studio:subtitle_studio@localhost:15432/subtitle_studio"
)


def make_session_factory(database_url: str | None = None) -> sessionmaker:
    database_url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
