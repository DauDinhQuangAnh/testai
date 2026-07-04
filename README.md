# AI Subtitle Studio (VietDub Studio)

Tool ca nhan tu dong tao/chinh sua phu de + long tieng tu video/audio, tu trien
khai toan bo pipeline AI ma nguon mo: FFmpeg -> DeepFilterNet3 -> Faster-Whisper
-> WhisperX -> pyannote -> dich NLLB -> long tieng edge-tts -> xuat
SRT/VTT/ASS/TXT/JSON + video da long tieng. Giao dien la web app React +
FastAPI backend (khong con Streamlit).

**Bat dau tu day:** doc [HANDOFF.md](HANDOFF.md) truoc tien - do la nguon trang
thai/tien do/quyet dinh kien truc duy nhat va moi nhat cua du an (dung chung giua
Claude Code va Codex). Boi canh/ly do dang sau cac quyet dinh nam o
[docs/memory/](docs/memory/README.md).

## Chay dev

```powershell
powershell -ExecutionPolicy Bypass -File .\start_project.ps1
```

Script nay khoi dong Docker Compose (Postgres + Redis), Celery worker, FastAPI
backend va React/Vite frontend. Sau khi chay xong mo: http://localhost:5173

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_project.ps1
```

Lenh stop tat cac tien trinh dev cua du an, dung Docker Compose services va xoa
log `*.log` o root.

## Chay dev thu cong (4 tien trinh)

```powershell
docker compose up -d
python -m celery -A app.jobs.celery_app worker --loglevel=info --pool=solo
python -m uvicorn backend.main:app --host localhost --port 8000 --reload
cd frontend; npm run dev -- --host localhost --port 5173
```
