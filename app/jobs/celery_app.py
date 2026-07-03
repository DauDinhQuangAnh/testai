"""Cau hinh Celery.

worker_concurrency = 1 vi may dev VRAM han che (6GB), khong the chay 2 job AI
pipeline dong thoi tren GPU - xem docs/memory/dev-machine-rtx4050.md.

Chay worker bang: python -m celery -A app.jobs.celery_app worker --loglevel=info
(dung `python -m celery`, KHONG dung lenh `celery` truc tiep, de dam bao thu muc
goc repo nam trong sys.path va cac import app.*/subtitle_pipeline.* hoat dong
dung khi Celery nap task tu app.jobs.tasks).
"""

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("subtitle_studio", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.worker_concurrency = 1
celery_app.conf.task_track_started = True

celery_app.autodiscover_tasks(["app.jobs"])
