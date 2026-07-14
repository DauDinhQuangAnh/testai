"""FastAPI backend cho UI React (frontend/) - thay the UI Streamlit (giu lai
lam legacy, xem HANDOFF.md quyet dinh 2026-07-03). Chay:

    python -m uvicorn backend.main:app --port 8000 --reload

Can Postgres/Redis (docker compose up -d) + Celery worker chay song song nhu
truoc - backend chi enqueue task, khong tu chay pipeline AI.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

load_dotenv()

from backend.db import get_session_factory  # noqa: E402 (can load_dotenv truoc)
from backend.routers import admin, auth, jobs, meta, public, voices  # noqa: E402


def _ensure_schema() -> None:
    """`create_all()` chi tao BANG con thieu, khong them COT vao bang co san
    - job cu tao truoc khi co Auth thieu cot `user_id`. ALTER truc tiep
    (Postgres ho tro IF NOT EXISTS; SQLite khong ho tro nen bo qua loi -
    SQLite chi dung trong test, schema luon duoc tao moi du cot).
    """
    factory = get_session_factory()
    try:
        with factory() as session:
            session.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
            session.commit()
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_schema()
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
