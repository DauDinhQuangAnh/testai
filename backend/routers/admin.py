"""Trang admin: kiem soat nguoi dung + toan bo job. Chi truy cap duoc bang
tai khoan admin chung (env ADMIN_EMAIL/ADMIN_PASSWORD, xem security.py).
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.db import job_repo, user_repo
from backend.schemas import AdminUserOut, JobOut
from backend.security import AuthUser, require_admin

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
