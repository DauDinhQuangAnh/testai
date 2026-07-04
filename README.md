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

## Chay dev (4 tien trinh)

```
docker compose up -d
python -m celery -A app.jobs.celery_app worker --loglevel=info
python -m uvicorn backend.main:app --port 8000 --reload
cd frontend && npm run dev   # http://localhost:5173
```
