"""FastAPI backend cho UI React (frontend/) - thay the UI Streamlit (giu lai
lam legacy, xem HANDOFF.md quyet dinh 2026-07-03). Chay:

    python -m uvicorn backend.main:app --port 8000 --reload

Can Postgres/Redis (docker compose up -d) + Celery worker chay song song nhu
truoc - backend chi enqueue task, khong tu chay pipeline AI.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.routers import admin, auth, jobs, meta, public, voices  # noqa: E402


def _run_migrations() -> None:
    """Nang schema DB len ban moi nhat bang Alembic luc khoi dong (thay ALTER
    thu cong `_ensure_schema` cu - xem migrations/versions/). Nuot loi co chu
    dich nhu ban cu: khi chay test/khong co Postgres, backend van phai import
    va khoi dong duoc (schema cua test do create_all trong
    make_session_factory lo, khong can Alembic).
    """
    try:
        from alembic import command
        from alembic.config import Config

        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(config, "head")
    except Exception as exc:
        print(f"[backend] Bỏ qua migration lúc khởi động: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()
    yield


app = FastAPI(title="AI Subtitle Studio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Vite dev server (frontend/) - dev dung proxy /api nen thuong khong can
    # CORS, nhung van mo cho truong hop goi thang cong 8000.
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(voices.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
