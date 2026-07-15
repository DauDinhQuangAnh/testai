"""Schema ban dau: users, jobs, custom_voices.

Baseline nay phai chiu duoc 2 diem xuat phat khac nhau:
- DB moi tinh (chua co bang nao): tao du 3 bang.
- DB dev co san, da duoc `Base.metadata.create_all()` tao tu truoc khi du an
  co Alembic: bang nao ton tai roi thi BO QUA (khong "table already exists"),
  chi va them cot `jobs.user_id` neu thieu - thay the ALTER thu cong cu trong
  backend/main.py `_ensure_schema()` (da xoa khi chuyen sang Alembic).
Cac migration TU 0002 tro di khong can guard kieu nay - viet ALTER binh
thuong (autogenerate), vi moi DB deu da di qua baseline nay.
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

# `sqlalchemy.Enum(JobStatus)` luu TEN member (QUEUED, RUNNING...) vao DB chu
# khong phai value ("queued") - khai bao dung nhu vay de khop du lieu cu do
# create_all tao ra.
JOB_STATUS = sa.Enum("QUEUED", "RUNNING", "DONE", "FAILED", name="jobstatus")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    if "custom_voices" not in tables:
        op.create_table(
            "custom_voices",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("ref_audio_path", sa.String(1024), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    if "jobs" not in tables:
        op.create_table(
            "jobs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), nullable=True),
            sa.Column("filename", sa.String(255), nullable=False),
            sa.Column("input_path", sa.String(1024), nullable=False),
            sa.Column("output_dir", sa.String(1024), nullable=False),
            sa.Column("status", JOB_STATUS, nullable=False),
            sa.Column("stage", sa.String(64), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    else:
        columns = {col["name"] for col in inspector.get_columns("jobs")}
        if "user_id" not in columns:
            op.add_column("jobs", sa.Column("user_id", sa.String(36), nullable=True))


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("custom_voices")
    op.drop_table("users")
    JOB_STATUS.drop(op.get_bind(), checkfirst=True)
