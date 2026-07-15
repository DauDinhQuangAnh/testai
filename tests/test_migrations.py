"""Chay THAT `alembic upgrade head` tren SQLite file tam - xac nhan baseline
tao du bang tren DB moi, idempotent khi chay lai, va "nhan nuoi" duoc DB co
san do create_all tao truoc khi du an co Alembic (kich ban may dev that)."""

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.db.models import Base

REPO_ROOT = Path(__file__).resolve().parents[1]


def _upgrade_head(db_url: str, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", db_url)
    command.upgrade(Config(str(REPO_ROOT / "alembic.ini")), "head")


def _table_names(db_url: str) -> set[str]:
    engine = sa.create_engine(db_url)
    try:
        return set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _sqlite_url(tmp_path: Path, name: str) -> str:
    return f"sqlite:///{(tmp_path / name).as_posix()}"


def test_upgrade_creates_all_tables_on_fresh_db(tmp_path, monkeypatch):
    db_url = _sqlite_url(tmp_path, "fresh.db")

    _upgrade_head(db_url, monkeypatch)

    assert {"users", "jobs", "custom_voices", "alembic_version"} <= _table_names(db_url)


def test_upgrade_twice_is_idempotent(tmp_path, monkeypatch):
    db_url = _sqlite_url(tmp_path, "twice.db")

    _upgrade_head(db_url, monkeypatch)
    _upgrade_head(db_url, monkeypatch)  # khong duoc loi "table already exists"

    assert "jobs" in _table_names(db_url)


def test_upgrade_adopts_db_created_by_create_all(tmp_path, monkeypatch):
    db_url = _sqlite_url(tmp_path, "existing.db")
    engine = sa.create_engine(db_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    _upgrade_head(db_url, monkeypatch)

    assert "alembic_version" in _table_names(db_url)


def test_migration_schema_matches_orm_models(tmp_path, monkeypatch):
    """Cot do migration tao phai khop cot ORM khai bao - lech nghia la quen
    cap nhat 1 trong 2 phia khi doi schema."""
    db_url = _sqlite_url(tmp_path, "parity.db")

    _upgrade_head(db_url, monkeypatch)

    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        for table_name, table in Base.metadata.tables.items():
            migrated_columns = {col["name"] for col in inspector.get_columns(table_name)}
            orm_columns = {col.name for col in table.columns}
            assert migrated_columns == orm_columns, f"Lech cot o bang {table_name}"
    finally:
        engine.dispose()
