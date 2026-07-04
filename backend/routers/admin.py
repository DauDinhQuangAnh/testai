"""Trang admin: kiem soat nguoi dung + toan bo job. Chi truy cap duoc bang
tai khoan admin chung (env ADMIN_EMAIL/ADMIN_PASSWORD, xem security.py).
"""

import asyncio
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.db import job_repo, user_repo
from backend.schemas import AdminUserOut, JobOut
from backend.security import AuthUser, require_admin
from subtitle_pipeline.infrastructure.cookie_refresh import (
    DEFAULT_COOKIES_PATH,
    refresh_cookies,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
def list_users(admin: AuthUser = Depends(require_admin)) -> list[AdminUserOut]:
    jobs_repo = job_repo()
    return [
        AdminUserOut(
            id=u.id,
            email=u.email,
            created_at=u.created_at,
            job_count=len(jobs_repo.list_by_user(u.id)),
        )
        for u in user_repo().list_all()
    ]


@router.delete("/users/{user_id}")
def delete_user(user_id: str, admin: AuthUser = Depends(require_admin)) -> dict:
    jobs_repo = job_repo()
    removed_jobs = 0
    for job in jobs_repo.list_by_user(user_id):
        shutil.rmtree(Path(job.output_dir).parent, ignore_errors=True)
        jobs_repo.delete(job.id)
        removed_jobs += 1
    user_repo().delete(user_id)
    return {"deleted": user_id, "removed_jobs": removed_jobs}


@router.get("/jobs", response_model=list[JobOut])
def list_all_jobs(admin: AuthUser = Depends(require_admin)) -> list[JobOut]:
    return [JobOut.from_job(j) for j in job_repo().list_all()]


@router.post("/refresh-cookies")
async def refresh_cookies_endpoint(admin: AuthUser = Depends(require_admin)) -> dict:
    """Chay AN (headless) lai profile trinh duyet da dang nhap tu truoc
    (`python -m subtitle_pipeline.infrastructure.cookie_refresh --setup` -
    phai chay 1 lan thu cong truoc, script nay khong the tu dang nhap).
    Chay trong thread rieng (asyncio.to_thread) vi Playwright sync API chan
    (blocking), tranh treo event loop cua FastAPI. Doi CHUA fix duoc Douyin
    (gioi han cua yt-dlp, khong phai do cookie - xem cookie_refresh.py).
    """
    cookies_path = Path(os.environ.get("YTDLP_COOKIES_FILE", str(DEFAULT_COOKIES_PATH)))
    try:
        count = await asyncio.to_thread(refresh_cookies, cookies_path)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Khong lam moi duoc cookie: {exc}. Neu chua tung chay setup, "
                "hay chay tren may chu (khong qua API): "
                "python -m subtitle_pipeline.infrastructure.cookie_refresh --setup"
            ),
        ) from exc
    return {"cookie_count": count, "path": str(cookies_path)}
