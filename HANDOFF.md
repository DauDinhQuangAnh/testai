# AI Subtitle Studio - Handoff & Sync

Day la FILE DUY NHAT dung de dong bo trang thai du an giua Claude Code va Codex
(vi ca hai deu duoc dung de code song song). Ghi chu boi canh/ly do dang sau cac
quyet dinh (it thay doi hon file nay) nam o `docs/memory/` - xem
`docs/memory/README.md`. Quy uoc:

- Truoc khi bat dau bat ky task nao, doc file nay truoc de biet trang thai moi nhat.
- Sau khi hoan thanh hoac thay doi gi quan trong, cap nhat lai file nay (khong tao
  them file trang thai/markdown khac trung muc dich).
- Ket qua do dac (VRAM/thoi gian) duoc ghi tu dong vao bang o cuoi file boi script
  `phase1_feasibility/summarize_results.py` - khong sua tay bang do, chi sua bang
  cach chay lai script.

## 1. Muc tieu san pham

Website AI tu dong tao/chinh sua phu de tu video/audio (kieu CapCut AI Subtitle,
Veed.io, Descript, WhisperX), tu trien khai toan bo pipeline AI ma nguon mo,
huong toi SaaS thuong mai that.

Pipeline: FFmpeg tach audio -> DeepFilterNet3 khu on -> Silero VAD -> Faster-Whisper
large-v3 (STT) -> WhisperX (align) -> pyannote (diarization) -> chia cau/toi uu
subtitle -> dich da ngon ngu -> export SRT/VTT/ASS/TXT/JSON.

## 2. Quyet dinh kien truc da chot

- **Frontend/Backend UI: Streamlit xuyen suot**, ke ca ban thuong mai sau nay.
  KHONG dung Next.js. Streamlit goi truc tiep ham Python (in-process), KHONG
  dung FastAPI lam lop REST API trung gian.
- **Celery + Redis + Postgres van giu nguyen** - khong phai de lam REST API, ma
  de serialize cac job GPU nang (may dev chi chay duoc concurrency=1 cho GPU) va
  luu trang thai job. Streamlit chi enqueue task roi poll Postgres/Redis.
- **2 ngoai le bat buoc phai co HTTP endpoint that** (khong tranh duoc):
  1. Stripe webhook (Phase billing) - can 1 route nho doc lap (FastAPI/Flask toi gian
     chi 1 endpoint), khong lien quan gi den kien truc frontend-backend chinh.
  2. Deploy multi-user Streamlit co the can nhieu instance + reverse proxy voi
     sticky session (van de nay chi giai quyet o Phase ha tang, chua can lam ngay).
- **Auth**: dung thu vien session/cookie cho Streamlit (vd. `streamlit-authenticator`,
  `extra-streamlit-components`) thay vi JWT+refresh token kieu web framework thuan.
- **Subtitle editor** (timeline/waveform) se can viet **Custom Streamlit Component**
  (widget React nho nhung vao Streamlit qua Component API) - danh gia la phan UI
  rui ro/cong suc cao nhat, lam rieng o Phase 5.

## 3. Rang buoc moi truong quan trong (BAT BUOC DOC)

- **May dev THAT** (noi se chay/test pipeline AI): RTX 4050 Laptop 6GB VRAM,
  Intel i5-13450HX, 24GB RAM DDR5, NVMe SSD, Windows 11.
- **Sandbox cua Claude Code** (moi truong dang ghi code trong cac phien lam viec):
  KHONG co GPU, KHONG co Python that cai san (chi co stub Microsoft Store), KHONG
  co ffmpeg. => **Claude Code CHI VIET CODE, KHONG tu chay/test duoc pipeline AI.**
  Moi lenh chay thu (python, pip install, ffmpeg, nvidia-smi...) phai do NGUOI DUNG
  tu chay thu cong tren may dev that, roi bao ket qua/log lai (hoac chay
  `summarize_results.py` de tu dong cap nhat bang ket qua trong file nay).
- Vi VRAM 6GB khong du de giu dong thoi nhieu model lon tren GPU, kien truc pipeline
  bat buoc phai theo kieu **load model tuan tu -> infer -> giai phong VRAM -> load
  model tiep theo** (khong giu tat ca model resident nhu ly tuong production).
- Faster-Whisper `large-v3` o fp16 can ~10GB VRAM -> tren 6GB phai dung quantization
  (`int8_float16` hoac `int8` qua CTranslate2) hoac dung `medium`/`large-v3-turbo`
  cho dev.
- pyannote diarization can chap nhan license gated model tren HuggingFace
  (`pyannote/speaker-diarization-3.1`, `pyannote/segmentation-3.0`) + access token
  (bien moi truong `HF_TOKEN`).

## 4. Roadmap tom tat (9 phase)

1. Feasibility Spike - AI pipeline tren may dev (**DANG LAM**)
2. AI Pipeline Core (dong goi module hoa, CLI)
3. Streamlit App - Upload + Job Dashboard (Celery/Redis/Postgres phia sau)
4. Subtitle Editor (Custom Streamlit Component - timeline/waveform)
5. Da ngon ngu + toi uu cau subtitle
6. Auth/User Management trong Streamlit
7. Billing/Subscription (co ngoai le Stripe webhook)
8. Bao mat nang cao + Ha tang Production (S3/MinIO, secrets, CI/CD, deploy multi-instance)
9. Monitoring/Scale nang cao - **CHI lam khi co traffic/user that** (Prometheus/Grafana,
   horizontal scaling, autoscaling GPU worker...)

## 5. Trang thai hien tai: Phase 1 - Feasibility Spike

**Muc tieu:** Xac nhan toan bo chuoi model AI chay duoc tren may dev, do VRAM peak
va thoi gian xu ly thuc te cho tung buoc, chon model size phu hop cho dev.

**Code da viet (boi Claude Code, CHUA duoc chay thu tren may that):**
- `phase1_feasibility/00_env_check.py` - kiem tra Python/CUDA/ffmpeg/packages/HF_TOKEN
- `phase1_feasibility/01_extract_audio.py` - FFmpeg tach audio 16kHz mono
- `phase1_feasibility/02_denoise.py` - DeepFilterNet3
- `phase1_feasibility/03_vad.py` - Silero VAD
- `phase1_feasibility/04_transcribe.py` - Faster-Whisper (chon model size + compute type qua tham so)
- `phase1_feasibility/05_align.py` - WhisperX alignment
- `phase1_feasibility/06_diarize.py` - pyannote diarization
- `phase1_feasibility/run_all.py` - chay tuan tu 01->06, MOI BUOC LA 1 SUBPROCESS
  RIENG (de dam bao VRAM duoc giai phong that su giua cac buoc, tranh do sai do
  CUDA memory fragmentation trong cung 1 process)
- `phase1_feasibility/summarize_results.py` - doc `results/phase1_results.jsonl`
  va tu dong ghi de bang ket qua ben duoi vao file HANDOFF.md nay

**Viec nguoi dung can lam tren may dev that (theo thu tu):**

1. Cai Python 3.12 that (khong dung Microsoft Store stub) - kiem tra `python --version`.
2. Cai FFmpeg va them vao PATH (`winget install Gyan.FFmpeg` hoac tai tu ffmpeg.org).
3. Kiem tra driver NVIDIA da cai: `nvidia-smi` phai hien RTX 4050.
4. Tao virtualenv: `python -m venv .venv` roi `.venv\Scripts\activate`.
5. Cai torch ban CUDA phu hop (xem lenh chinh xac tai https://pytorch.org/get-started/locally/
   ung voi driver CUDA dang co, vi du: `pip install torch torchaudio --index-url
   https://download.pytorch.org/whl/cu121`).
6. `pip install -r requirements.txt`.
7. Tao tai khoan HuggingFace, chap nhan license cho `pyannote/speaker-diarization-3.1`
   va `pyannote/segmentation-3.0`, tao access token, copy `.env.example` thanh `.env`
   va dien `HF_TOKEN=...` (hoac set bien moi truong truc tiep).
8. Bo 1 file video/audio mau (5-10 phut, co tieng noi) vao `phase1_feasibility/samples/`.
9. Chay: `python phase1_feasibility/00_env_check.py` - sua loi neu co truoc khi tiep tuc.
10. Chay: `python phase1_feasibility/run_all.py phase1_feasibility/samples/<ten_file>`.
11. Chay: `python phase1_feasibility/summarize_results.py` - lenh nay se TU DONG cap
    nhat bang ket qua o muc 6 ben duoi trong chinh file HANDOFF.md nay.
12. Bao lai (hoac de Codex/Claude Code doc lai file nay) ket qua + bat ky loi/canh
    bao nao gap phai o muc "Van de dang mo" ben duoi.

**Dinh nghia hoan thanh (DoD) cua Phase 1:**
- Chay het duoc pipeline 01->06 tren 1 video mau tren may dev that.
- Co so lieu VRAM peak + thoi gian xu ly thuc te cho tung buoc (bang o muc 6).
- Chot duoc model size dung cho dev (vd. Whisper `medium` hay `large-v3` quantized)
  va ghi lai quyet dinh o muc "Quyet dinh moi" ben duoi.

## 6. Ket qua do dac Phase 1 (TU DONG cap nhat boi summarize_results.py)

<!-- PHASE1_RESULTS_START -->
(chua co ket qua nao, chay `phase1_feasibility/run_all.py` roi
`phase1_feasibility/summarize_results.py` de dien vao day)
<!-- PHASE1_RESULTS_END -->

## 7. Quyet dinh moi / thay doi so voi ban dau

(de trong, dien khi co quyet dinh moi phat sinh trong qua trinh lam Phase 1)

## 8. Van de dang mo / can quyet dinh

(de trong, dien khi gap loi hoac can nguoi dung quyet dinh)

## 9. Nhat ky cap nhat

- 2026-07-01: Tao HANDOFF.md, viet xong code Phase 1 (chua chay thu, cho chay tren
  may dev that co GPU).
