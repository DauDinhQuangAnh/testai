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

## 0. Setup nhanh tren may dev that (RTX 4050) - lam theo thu tu

Checklist gop tu cac phase, de bat dau tu 1 may Windows 11 sach:

1. **Cai dat he thong (1 lan):**
   - Python 3.12 that tu python.org (KHONG dung stub Microsoft Store; tick
     "Add python.exe to PATH" khi cai). Kiem tra: `python --version`.
   - FFmpeg: `winget install Gyan.FFmpeg` (mo terminal moi sau khi cai).
     Kiem tra: `ffmpeg -version`.
   - Driver NVIDIA moi nhat. Kiem tra: `nvidia-smi` phai hien RTX 4050.
   - Docker Desktop (cho Postgres + Redis). Kiem tra: `docker --version`.
   - Git. Kiem tra: `git --version`.
2. **Lay code:** `git clone https://github.com/DauDinhQuangAnh/testai.git`
   roi `cd testai`.
3. **Virtualenv:** `python -m venv .venv` roi `.venv\Scripts\activate`.
4. **Torch ban CUDA (TRUOC khi cai requirements):** xem lenh dung tai
   https://pytorch.org/get-started/locally/ ung voi driver dang co, vi du:
   `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121`
5. **Dependencies:** `pip install -r requirements-dev.txt` (bao gom ca
   requirements.txt + ruff/pytest/pre-commit).
6. **File .env:** copy `.env.example` thanh `.env`, dien:
   - `HF_TOKEN`: tao tai khoan HuggingFace, accept license
     `pyannote/speaker-diarization-3.1` va `pyannote/segmentation-3.0`
     (bam "Agree" tren trang model), roi tao token tai
     https://huggingface.co/settings/tokens
   - Cac bien S3 de trong cung duoc (chi can khi test Phase 8 voi S3 that).
   - (SESSION_SECRET_KEY da bi xoa cung voi Auth 2026-07-03 - khong con can.)
7. **Postgres + Redis:** `docker compose up -d`. Kiem tra: `docker ps` thay
   2 container.
8. **Pre-commit hook (1 lan):** `pre-commit install`.
9. **Chay kiem tra theo dung thu tu o muc 8 ("Uu tien thu tu kiem thu")** -
   bat dau bang `python phase1_feasibility/check_env.py`, roi `pytest`, roi
   cac phase tu thap len cao. Gap loi thi ghi vao muc 8 (hoac bao AI dang lam
   viec cung cap nhat).

Luu y dung luong: lan chay dau se tai model tu HuggingFace (~3-6GB tuy model:
Whisper medium ~1.5GB, large-v3 ~3GB, pyannote ~vai tram MB, NLLB ~2.4GB neu
test dich) - can mang on dinh va o dia trong.

## 1. Muc tieu san pham

**Tool CA NHAN** (khong con huong toi SaaS thuong mai - quyet dinh 2026-07-03,
xem muc 7) tu dong tao/chinh sua phu de + long tieng tu video/audio, tu trien
khai toan bo pipeline AI ma nguon mo.

Pipeline: FFmpeg tach audio -> DeepFilterNet3 khu on -> Faster-Whisper (STT,
tich hop san Silero VAD) -> WhisperX (align) -> pyannote (diarization) -> toi uu
subtitle -> dich da ngon ngu (NLLB) -> long tieng (edge-tts) -> export
SRT/VTT/ASS/TXT/JSON + video da long tieng.

## 2. Quyet dinh kien truc da chot

**LUU Y: 2 gach dau dong dau tien duoi day la quyet dinh CU (2026-07-03,
buoi sang), DA BI DAO NGUOC cung ngay boi quyet dinh o muc 6k (UI React +
FastAPI) - giu lai de hieu boi canh/ly do, xem trang thai THAT HIEN TAI ngay
sau do.**

- ~~Tool ca nhan, khong da nguoi dung/Auth/Billing~~ - **DA DAO NGUOC**: gio
  co Auth (dang ky/dang nhap) + admin (tai khoan chung tu env), xem muc 6k.
  Van KHONG gioi han usage/goi cuoc (nguoi dung xac nhan giu nguyen phan nay).
- ~~Frontend/Backend UI: Streamlit xuyen suot~~ - **DA DAO NGUOC + XOA HOAN
  TOAN Streamlit (2026-07-04)**: UI gio la `frontend/` (React + TypeScript +
  Tailwind, Vite) goi `backend/` (FastAPI REST API) qua HTTP. Celery worker
  + Postgres/Redis giu nguyen vai tro cu (backend enqueue task, worker xu ly
  ngam, khong doi gi ve pipeline/Celery). Xem muc 6k de biet kien truc day
  du + cach chay 4 tien trinh.
- **Subtitle editor** (chinh sua text/timing/speaker) hien CHUA duoc port
  sang UI React (Editor.py cu la Streamlit `st.data_editor`, da xoa cung
  Streamlit) - CAN LAM LAI o `frontend/` neu van can tinh nang nay (ghi nhan
  o muc 8 "Van de dang mo").
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

1. Feasibility Spike - AI pipeline tren may dev (code xong, **CHUA chay tren may that**)
2. AI Pipeline Core (dong goi module hoa, CLI) (code xong, **CHUA chay tren may that**)
3. Streamlit App - Upload + Job Dashboard (code xong, **CHUA chay tren may that**)
4. Subtitle Editor (`st.data_editor` - xem "Quyet dinh moi") (code xong, **CHUA chay**)
5. Da ngon ngu + toi uu cau subtitle (code xong, **CHUA chay, rui ro cao nhat**)
5b. Long tieng (Dubbing/TTS) - edge-tts (da thay MMS-TTS vi chat luong giong,
    xem muc 6i) + ghep audio vao video (da chay duoc tren may that, dang tinh
    chinh chat luong dong bo)
6. Auth/User Management - **DA XOA HOAN TOAN (2026-07-03)**, du an la tool
   ca nhan, khong con da nguoi dung, xem "Quyet dinh moi"
7. Goi cuoc + gioi han usage - **DA XOA HOAN TOAN (2026-07-03)** cung luc voi
   Auth, khong con thuong mai/SaaS, xem "Quyet dinh moi"
8. Bao mat nang cao + Ha tang Production - MOT PHAN: storage S3 abstraction + CI
   da co code, **CHUA lam**: secrets manager that, deploy multi-instance
9. Monitoring/Scale nang cao - **CO CHU DICH CHUA LAM** (Prometheus/Grafana,
   horizontal scaling, autoscaling GPU worker...) - chi lam khi co traffic/user
   that, tranh xay du thua qua som (quyet dinh tu roadmap ban dau, van giu nguyen)

## 5. Phase 1 - Feasibility Spike

**Muc tieu:** Xac nhan toan bo chuoi model AI chay duoc tren may dev, do VRAM peak
va thoi gian xu ly thuc te cho tung buoc, chon model size phu hop cho dev.

**Code da viet (boi Claude Code, CHUA duoc chay thu tren may that):**
- `phase1_feasibility/check_env.py` - kiem tra Python/CUDA/ffmpeg/packages/HF_TOKEN
- `phase1_feasibility/step01_extract_audio.py` - FFmpeg tach audio 16kHz mono
- `phase1_feasibility/step02_denoise.py` - DeepFilterNet3
- `phase1_feasibility/step03_vad.py` - Silero VAD (chi de do hieu nang tham khao,
  khong co adapter tuong duong trong subtitle_pipeline - xem muc 7)
- `phase1_feasibility/step04_transcribe.py` - Faster-Whisper (chon model size +
  compute type qua tham so)
- `phase1_feasibility/step05_align.py` - WhisperX alignment
- `phase1_feasibility/step06_diarize.py` - pyannote diarization
- `phase1_feasibility/measure.py` - helper do thoi gian/VRAM peak, dung chung
  boi tat ca script step0X (khong con nam trong subpackage `utils/` rieng - da
  lam phang thu muc de tranh 1 package chi co dung 1 file)
- Cac script `step01`, `step02`, `step04`, `step05`, `step06` goi TRUC TIEP cac
  adapter trong `subtitle_pipeline/infrastructure/` (Phase 2) thay vi tu viet
  lai logic goi thu vien AI - vua tranh trung lap code, vua dam bao so lieu do
  duoc chinh la hieu nang cua code se chay that trong production. Rieng
  `step03_vad.py` khong co adapter tuong duong nen van la ban doc lap.
- `phase1_feasibility/run_all.py` - chay tuan tu step01->step06, MOI BUOC LA 1
  SUBPROCESS RIENG (de dam bao VRAM duoc giai phong that su giua cac buoc,
  tranh do sai do CUDA memory fragmentation trong cung 1 process)
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
9. Chay: `python phase1_feasibility/check_env.py` - sua loi neu co truoc khi tiep tuc.
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

## 6b. Phase 2 - AI Pipeline Core (dong goi module hoa)

**Muc tieu:** Bien pipeline tu script roi rac (Phase 1) thanh module Python sach,
tai su dung duoc, chay qua CLI (input video -> output SRT/VTT/ASS/TXT/JSON).

**Trang thai:** Code da viet xong (2026-07-01), **CHUA duoc chay thu tren may dev
that** - nguoi dung chon lam Phase 2 truoc khi co ket qua do Phase 1 (xem muc 7).

**Kien truc (Clean Architecture):**
- `subtitle_pipeline/domain/` - kieu du lieu thuan (`models.py`) + interface
  (`ports.py`, dung `typing.Protocol`) - khong phu thuoc thu vien AI nao.
- `subtitle_pipeline/infrastructure/` - adapter that cho tung buoc: `audio.py`
  (FFmpeg), `denoiser_deepfilternet.py`, `transcriber_faster_whisper.py`,
  `aligner_whisperx.py`, `diarizer_pyannote.py`, `gpu.py` (giai phong VRAM). Moi
  adapter la context manager (load model o `__enter__`, giai phong o `__exit__`)
  va CHI import thu vien AI ben trong ham/method (khong o top-level module) - nho
  vay cac layer khac khong bi buoc phai cai torch/whisper/pyannote/deepfilternet.
- `subtitle_pipeline/application/pipeline.py` - `TranscriptionPipeline` dieu phoi
  tuan tu cac buoc, chi phu thuoc `domain/ports.py` (khong import truc tiep AI
  libs), nhan adapter qua factory (co the inject fake khi test).
  `application/merge.py` - gan speaker vao subtitle segment theo overlap lon nhat
  voi ket qua diarization.
- `subtitle_pipeline/export/formats.py` - ham thuan (khong AI deps) xuat
  SRT/VTT/ASS/TXT/JSON.
- `subtitle_pipeline/cli.py` - entry point: `python -m subtitle_pipeline.cli
  input.mp4 --out-dir output --formats srt,vtt,ass,txt,json`.
- `tests/` - `fakes.py` (fake adapter) + `test_pipeline.py`, `test_merge.py`,
  `test_export_formats.py`. Vi cac layer domain/application/export khong import
  AI libs o top-level, cac test nay chay duoc **ma khong can cai
  torch/faster-whisper/whisperx/pyannote/deepfilternet** - chi can `pytest`
  (xem `requirements-dev.txt`, `pyproject.toml`).

**Viec nguoi dung can lam tren may dev that:**
1. `pip install -r requirements-dev.txt` (hoac it nhat `pip install pytest` neu
   chi muon chay unit test nhanh ma chua can AI libs).
2. Chay `pytest` tu goc repo - xac nhan toan bo test pass (logic dieu phoi +
   export dinh dang, khong dung GPU that).
3. Chay thu CLI that voi video mau: `python -m subtitle_pipeline.cli
   phase1_feasibility/samples/<file> --out-dir output`. Day la lan dau kiem tra
   viec giai phong VRAM trong CUNG 1 process (gc.collect + torch.cuda.empty_cache,
   khac voi Phase 1 dung subprocess rieng) co du de tranh OOM khi chay het 5
   buoc lien tiep hay khong.
4. Bao lai ket qua/loi (dac biet neu OOM o buoc nao) vao muc 8 ben duoi.

**Dinh nghia hoan thanh (DoD) cua Phase 2:**
- `pytest` pass toan bo tren may dev that.
- CLI chay het duoc 1 video mau, sinh dung 5 dinh dang file, khong OOM.
- Neu OOM: can quay lai dieu chinh chien luoc giai phong VRAM (vd. quay ve
  subprocess-per-stage nhu Phase 1, hoac giam model size mac dinh).

## 6c. Phase 3 - Streamlit App (Upload + Job Dashboard)

**Muc tieu:** Nguoi dung thao tac qua web UI: upload video -> job chay async
(Celery) -> theo doi tien do -> tai file ket qua khi xong.

**Trang thai:** Code da viet xong (2026-07-01), **CHUA duoc chay thu tren may dev
that** - chua co Postgres/Redis/Celery worker nao duoc khoi dong de kiem tra.

**Kien truc:**
- `app/db/models.py` - ORM `Job` (SQLAlchemy 2.0 `Mapped`/`mapped_column`):
  id, filename, input_path, output_dir, status (queued/running/done/failed),
  stage (buoc hien tai, cap nhat qua callback `on_stage` cua
  `TranscriptionPipeline.run` - xem Phase 2), error_message, created_at, updated_at.
- `app/db/session.py` - `make_session_factory(database_url=None)`, KHONG tao
  engine o module-level (chi tao khi goi ham) de test duoc bang SQLite in-memory
  ma khong dung toi Postgres that.
- `app/jobs/repository.py` - `JobRepository` nhan `session_factory` qua
  constructor (mac dinh dung Postgres that qua `make_session_factory()`), cac
  Streamlit page/Celery task khong tu viet SQL/session truc tiep.
- `app/jobs/celery_app.py` - Celery app, `worker_concurrency = 1` (may dev VRAM
  han che, xem docs/memory/dev-machine-rtx4050.md).
- `app/jobs/tasks.py` - task `process_video_job(job_id)`: chay
  `TranscriptionPipeline` (Phase 2) voi `on_stage` callback cap nhat
  `Job.stage` vao DB, export 5 dinh dang, cap nhat `Job.status` DONE/FAILED.
- `app/Home.py`, `app/pages/1_Upload.py`, `app/pages/2_Dashboard.py` - Streamlit
  multipage app. Moi file co doan them thu muc goc repo vao `sys.path` o dau
  (Streamlit khong tu them, chi them thu muc chua file dang chay - can de import
  `app.*`/`subtitle_pipeline.*` hoat dong dung).
- `docker-compose.yml` - Postgres 16 + Redis 7 cho dev (`docker compose up -d`).
- `tests/test_job_repository.py` - test `JobRepository` bang SQLite in-memory,
  khong can Postgres chay.

**Viec nguoi dung can lam tren may dev that:**
1. `docker compose up -d` (can Docker Desktop) de chay Postgres + Redis. Neu
   khong dung Docker, tu cai Postgres/Redis va sua `DATABASE_URL`/`REDIS_URL`
   trong `.env` cho phu hop.
2. Copy `.env.example` thanh `.env` neu chua co, kiem tra `DATABASE_URL`,
   `REDIS_URL`, `STORAGE_DIR`.
3. `pip install -r requirements.txt` (them streamlit/sqlalchemy/psycopg2-binary/
   celery/redis so voi Phase 1-2).
4. Chay Celery worker (terminal rieng): `python -m celery -A app.jobs.celery_app
   worker --loglevel=info` (dung `python -m celery`, KHONG dung lenh `celery`
   truc tiep - xem comment trong `app/jobs/celery_app.py`).
5. Chay Streamlit (terminal khac): `streamlit run app/Home.py`.
6. Vao trang Upload, tai 1 file mau len, bam "Tao job xu ly".
7. Vao trang Dashboard, bam "Lam moi", theo doi `stage` thay doi, cho toi khi
   `status = done` roi tai file ket qua.
8. Bao lai loi (dac biet loi import sys.path, loi ket noi DB/Redis, hoac OOM o
   Celery worker) vao muc 8 ben duoi.

**Dinh nghia hoan thanh (DoD) cua Phase 3:**
- Luong end-to-end qua web UI hoat dong: upload -> job chay -> dashboard cap
  nhat tien do -> tai duoc file SRT/VTT/ASS/TXT/JSON.
- `pytest` (bao gom `test_job_repository.py`) pass tren may dev that.

## 6d. Phase 4 - Subtitle Editor

**Muc tieu:** Chinh sua text/timing/speaker cua 1 job da xong, xuat lai file.

**Trang thai:** Code xong (2026-07-02), **CHUA chay thu**. Dung `st.data_editor`
thay vi Custom Streamlit Component (xem "Quyet dinh moi" o muc 2).

**Kien truc:** `app/pages/3_Editor.py` - chon job DONE, doc file `.json` ket
qua, hien thi bang co the sua (`st.data_editor`), nut "Luu va xuat lai file"
ghi de ca 5 dinh dang qua `FORMAT_WRITERS` (tai su dung Phase 2).

**Viec can lam:** Mo trang Editor sau khi co it nhat 1 job DONE (tu Phase 3),
thu sua 1 dong, luu, kiem tra file `.srt`/`.json`... trong thu muc output da
duoc cap nhat dung.

## 6e. Phase 5 - Da ngon ngu + toi uu subtitle

**Muc tieu:** Dich subtitle sang ngon ngu khac, toi uu do dai dong theo chuan
CPL/so dong.

**Trang thai:** Code xong (2026-07-02), **CHUA chay thu - RUI RO CAO NHAT
trong toan bo cac adapter da viet.**

**Kien truc:**
- `subtitle_pipeline/application/optimize.py` - `optimize_segments()`, ham
  thuan (khong AI deps), gioi han 42 ky tu/dong, toi da 2 dong, khong lam mat
  noi dung (don phan du vao dong cuoi thay vi cat bo). Co test
  (`tests/test_optimize.py`).
- `subtitle_pipeline/infrastructure/translator_nllb.py` - `NLLBTranslator`,
  dung model `facebook/nllb-200-distilled-600M` qua `transformers`
  (`AutoModelForSeq2SeqLM` + `AutoTokenizer`, `forced_bos_token_id`). **CANH
  BAO: day la adapter DUY NHAT chua tung chay/kiem thu du 1 lan, viet hoan toan
  dua theo tai lieu HuggingFace. Cach goi API co the sai lech giua cac phien
  ban `transformers`** (xem docstring trong file de biet chi tiet diem nghi
  ngo).
- `subtitle_pipeline/application/translate.py` - `translate_and_export()`:
  dich + toi uu + xuat file voi hau to ngon ngu (vd. `video.en.srt`).
- `app/jobs/tasks.py` - Celery task `translate_job(job_id, target_language)`.
- `app/pages/3_Editor.py` - muc "Dich sang ngon ngu khac" o cuoi trang, enqueue
  `translate_job`.

**Viec can lam:** Sau khi co job DONE, vao Editor, chon ngon ngu dich, bam
"Dich va xuat file moi", theo doi log Celery worker de biet loi cu the neu co
(rat co the co loi o lan chay dau vi API `transformers` chua duoc xac minh).

## 6f. Phase 6 - Auth/User Management (DA XOA)

**Da xoa hoan toan ngay 2026-07-03** theo yeu cau nguoi dung: du an la tool ca
nhan, khong can dang ky/dang nhap/phan quyen theo user. Da xoa `app/auth/`
(`security.py`, `repository.py`, `streamlit_helpers.py`), model `User`, cot
`Job.user_id`, dependency `bcrypt`/`pyjwt`/`extra-streamlit-components`, bien
env `SESSION_SECRET_KEY`. Xem "Quyet dinh moi" de biet chi tiet + anh huong
schema DB (can reset DB, xem muc 8).

## 6g. Phase 7 - Goi cuoc + gioi han usage (DA XOA)

**Da xoa hoan toan ngay 2026-07-03** cung luc voi Auth (khong con Auth thi
khong con khai niem "usage cua 1 user" de gioi han) - du an khong con huong
toi SaaS thuong mai. Da xoa `app/billing/` (`plans.py`, `usage.py`,
`repository.py`), `app/pages/4_Billing.py`, model `PlanTier`/`Subscription`.
Xem "Quyet dinh moi" de biet chi tiet.

## 6h. Phase 8 - Bao mat + Ha tang Production (mot phan)

**Muc tieu:** San sang trien khai production o muc co ban.

**Trang thai:** Mot phan da co code (2026-07-02), **CHUA chay thu**. Con thieu
nhieu so voi "production-ready" that su (xem "Van de dang mo").

**Da lam:**
- `.github/workflows/ci.yml` - chay `ruff check` + `ruff format --check` +
  `pytest` tren moi push/PR len `main`.
- Hardening Upload: gioi han kich thuoc file (500MB) + kiem tra dinh dang phia
  server trong `backend/routers/jobs.py` (khong chi dua vao content-type nguoi
  dung gui len).

**CHUA lam (ghi nhan de lam sau, khong xay truoc khi can - tranh du thua):**
- Secrets management that (Vault, AWS Secrets Manager...) - hien dang dung
  `.env`/bien moi truong, du cho dev/MVP nhung khong phai chuan production.
- Deploy multi-instance backend FastAPI + reverse proxy.

**Viec can lam:** Xem CI chay pass tren GitHub sau khi push.

**Cap nhat 2026-07-13 - XOA S3 storage abstraction:** theo yeu cau nguoi dung
("s3 storage đi ko cần đâu clean phần đó luôn") - du an la tool ca nhan chay
local, khong can S3/MinIO. Da xoa `app/storage.py` (`Storage`
Protocol/`LocalStorage`/`S3Storage`) + `tests/test_storage.py`, bo dependency
`boto3` khoi `requirements.txt`, bo `STORAGE_BACKEND`/`S3_BUCKET`/`S3_PREFIX`
khoi `.env`/`.env.example`. Module nay tu truoc gio KHONG duoc noi vao
Upload/Editor/Celery task nao (toan bo van dung `Path` filesystem truc tiep),
nen xoa khong anh huong hanh vi hien co - chi bot dead code. 113/113 pytest
pass (giam 3 test so voi truoc, dung bang so test cua `test_storage.py` da
xoa), ruff sach.

## 6i. Phase 5b - Long tieng (Dubbing / Text-to-Speech)

**Muc tieu:** Tu file ket qua da dich (Phase 5), sinh giong doc bang TTS,
co-gian khop khung thoi gian tung cau, ghep thanh 1 track audio day du va mux
(ghep) vao video goc -> ra 1 file video hoan chinh da long tieng, khong chi
con la phu de text.

**Trang thai:** Code xong (2026-07-03), **CHUA chay thu - RUI RO CAO NHAT
trong toan bo du an** (adapter TTS hoan toan moi, chua tung duoc goi thu).

**Boi canh quyet dinh (xem muc 7 de biet chi tiet):** nguoi dung chon ngon ngu
dich chinh la **tieng Viet**, **khong can voice cloning** o ban v1 (chap nhan
giong doc chuan), va du an la **ca nhan/phi thuong mai** nen khong bi rang
buoc license commercial.

**Vi sao chon MMS-TTS (`facebook/mms-tts-vie`) thay vi Coqui XTTS-v2 (quyet
dinh ban dau, DA BI THAY THE - xem "Cap nhat 2026-07-03 lan 2" ben duoi):**
XTTS-v2 (model voice-cloning tot nhat hien co) KHONG co tieng Viet trong 17
ngon ngu ho tro. MMS-TTS (Meta) co checkpoint rieng cho ~1100 ngon ngu bao gom
tieng Viet, chay qua `transformers.VitsModel`/`VitsTokenizer` - dung chung thu
vien `transformers` da co san tu Phase 5 (khong them framework ML moi), VRAM
rat nhe (<1GB, phu hop ngan sach 6GB VRAM dang chia se voi Whisper/pyannote/
NLLB). Doi lai KHONG ho tro voice cloning (dung yeu cau v1) va license
CC-BY-NC (chap nhan duoc vi du an khong con thuong mai). **Sau khi chay thu
tren may dev that, chat luong giong MMS-TTS qua te (VITS robot, phat am sai
nhieu) - da thay bang `edge-tts`, xem chi tiet o "Cap nhat 2026-07-03 lan 2".**

**Kien truc (noi tiep dung Clean Architecture cua `subtitle_pipeline/`):**
- `subtitle_pipeline/domain/ports.py` - them Protocol `VoiceSynthesizer`.
- `subtitle_pipeline/infrastructure/tts_edge.py` - `EdgeTTSSynthesizer` (thay
  the `tts_mms.py` da xoa - xem "Cap nhat 2026-07-03 lan 2" ben duoi).
- `subtitle_pipeline/infrastructure/audio_timing.py` - `probe_duration_seconds`
  (ffprobe) + `time_stretch_to_duration` (ffmpeg `atempo`, tu chia nho factor
  ngoai khoang [0.5, 2.0] thanh chuoi filter - ham thuan `_clamp_atempo_factors`
  co test rieng).
- `subtitle_pipeline/infrastructure/audio_mux.py` - `build_dub_track` (dung
  track audio day du bang numpy, dat tung clip TTS vao dung offset theo
  timeline goc, khoang trong la im lang) + `mux_audio_into_video` (ffmpeg,
  giu nguyen video stream `-c:v copy`, chi thay audio stream).
- `subtitle_pipeline/application/dub.py` - `dub_and_export()` dieu phoi:
  synthesize tung segment -> stretch khop `end-start` -> dung track theo
  tong thoi luong (doc tu `_work/audio_denoised.wav` con luu tu Phase 2, hoac
  ffprobe video goc neu file khong con) -> mux vao video -> tra ve duong dan
  `<stem>.<lang>.dubbed.mp4`.
- `app/jobs/tasks.py` - Celery task `dub_job(job_id, target_language)` va
  helper `_load_or_translate_segments()` (dung chung logic voi `translate_job`
  nhung tu dong dich truoc neu chua co file `.{lang}.json`, dung de `dub_job`
  khong bat buoc nguoi dung phai bam "Dich" rieng truoc).
- `app/pages/3_Editor.py` - **theo yeu cau nguoi dung, gop lam 1 nut duy nhat**
  "Dich + Long tieng" (khong bat bam dich xong roi moi bam long tieng rieng)
  o khoi moi ben duoi khoi "Dich sang ngon ngu khac" (khoi cu van giu nguyen,
  van huu ich neu chi can phu de dich, khong can audio). Sau khi co file
  `.dubbed.mp4`, trang hien `st.video()` + nut tai xuong.

**Cap nhat 2026-07-03 (sau khi nguoi dung dung thu tren may dev that va yeu
cau don gian hoa flow) - gop toan bo vao 1 buoc upload duy nhat:**
- `app/pages/1_Upload.py` - them o chon "Ngon ngu long tieng" (dung chung
  `SUPPORTED_LANGUAGES`, xem duoi) ngay tai trang Upload, mac dinh `vi`.
  `process_video_job.delay(job.id, target_language)` truyen thang ngon ngu
  vao job chinh - nguoi dung KHONG can vao Editor bam gi nua, chi upload 1
  lan la ra video hoan chinh.
- `app/jobs/tasks.py` - `process_video_job(job_id, target_language=None)`:
  neu co `target_language`, sau khi transcribe xong se **goi tiep luon trong
  cung 1 task** `translate_and_export()` (stage "translate") roi
  `dub_and_export()` (stage "dub"), cap nhat `Job.stage` xuyen suot ca 2 giai
  doan de Dashboard hien tien do dung. Khong dung Celery chain/task rieng -
  chi la goi ham Python tuan tu trong cung 1 task, don gian va de debug hon.
  Trang Editor (`dub_job`/`translate_job`) van giu nguyen, dung de **lam lai
  hoac doi ngon ngu khac sau nay** (khong phai buoc bat buoc trong flow
  chinh nua).
- `subtitle_pipeline/infrastructure/translator_nllb.py` - them hang so
  `SUPPORTED_LANGUAGES = list(NLLB_LANGUAGE_CODES.keys())`, dung chung boi ca
  `1_Upload.py` va `3_Editor.py` (truoc do moi noi tu hardcode 1 list rieng,
  de lech nhau).
- `app/jobs/repository.py` - them `JobRepository.delete(job_id)`. Co test
  (`tests/test_job_repository.py`).
- `app/pages/2_Dashboard.py` - them checkbox "Xac nhan xoa" + nut "Xoa job"
  cho tung job: xoa ca record DB (`repo.delete`) LAN toan bo file tren dia
  (`shutil.rmtree(Path(job.output_dir).parent)` - xoa ca video goc va thu
  muc output, vi ca hai deu nam chung trong `storage/<job_id>/`). Xoa vinh
  vien, khong co thung rac/soft-delete (du an ca nhan, uu tien don gian va
  giai phong dung luong dia).
- `requirements.txt` - them `soundfile>=0.12.1`.
- `tests/test_audio_timing.py`, `tests/test_audio_mux.py` - test logic thuan
  (`_clamp_atempo_factors`, dat clip dung offset trong track) bang du lieu
  gia lap qua `soundfile`/`numpy`, KHONG can model TTS/ffmpeg that.

**Cap nhat 2026-07-03 lan 2 (sau khi nguoi dung chay thu tren may dev that va
danh gia chat luong giong doc "qua te") - doi TTS backend + tu don file:**
- **Doi tu MMS-TTS sang `edge-tts`:** xoa
  `subtitle_pipeline/infrastructure/tts_mms.py`, them
  `subtitle_pipeline/infrastructure/tts_edge.py` (`EdgeTTSSynthesizer`). Da
  research (xem chi tiet trong docstring dau file `tts_edge.py`): MMS-TTS la
  VITS chat luong thap, phat am nhieu loi; `edge-tts` goi giong Azure Neural
  TTS THAT cua Microsoft (mien phi, khong can API key, qua tinh nang "Doc to"
  cua trinh duyet Edge) - chat luong tu nhien hon han. Giong tieng Viet dung:
  `vi-VN-HoaiMyNeural` (nu, mac dinh). **DANH DOI: day la adapter DUY NHAT
  trong toan bo pipeline can INTERNET** (goi qua giao thuc noi bo cua Edge,
  khong phai API chinh thuc duoc Microsoft cong bo/dam bao - co the bi gian
  doan neu Microsoft thay doi, luc do thu `pip install -U edge-tts` truoc).
  Neu sau nay can bo hoan toan phu thuoc internet, tham khao **VieNeu-TTS**
  (github.com/pnnbao97/VieNeu-TTS - TTS tieng Viet local/GPU, co voice
  cloning, MOI CHUA duoc dua vao du an nay, can research/test lai tu dau).
  `dub_and_export()` khong con nhan tham so `device` (edge-tts khong dung
  GPU/local model).
- **Tu dong xoa file trung gian sau khi long tieng xong:** `dub_and_export()`
  (`subtitle_pipeline/application/dub.py`) gio goi `shutil.rmtree(work_dir)`
  ngay sau khi mux video thanh cong - xoa toan bo `_work/` (audio trung gian
  cua buoc transcribe: `audio_16k.wav`, `audio_denoised.wav`, cac clip TTS
  tam trong `dub_<lang>_segments/`, track am thanh tam `dub_track_<lang>.wav`).
  Chi giu lai file trong `out_dir`: cac dinh dang phu de goc + phu de da dich
  + video `.dubbed.mp4` cuoi cung. Ap dung cho ca 2 duong goi
  `dub_and_export()` (auto-flow tu Upload va nut thu cong o Editor).
- `requirements.txt` - them `edge-tts>=6.1.9`.

**Han che da biet (chua giai quyet trong ban nay):**
- Khong co voice cloning - moi nguoi noi duoc gan 1 giong CO SAN khac nhau
  (xem quyet dinh 2026-07-03 lan 10 - `_build_speaker_voice_map` trong
  `dub.py`), khong phai giong that cua nguoi noi goc.
- Dong bo audio-video chi o muc "khop khung thoi gian [start, end]" bang
  time-stretch (`atempo`), KHONG phai lip-sync that (khong co model dong bo
  mieng).
- ~~Neu cau TTS qua dai/qua ngan so voi khung thoi gian goc, `atempo` co the
  lam giong nghe khong tu nhien (nhanh/cham bat thuong)~~ - **DA GIAI QUYET
  (2026-07-15, xem muc 6q)**: chi tang toc khi clip THUC SU tran sang cau ke
  tiep, toi da 1.3x; phan tran con lai duoc tron cong thay vi ghi de.
- **`edge-tts` can INTERNET on dinh cho MOI segment** - video dai nhieu cau se
  goi API nhieu lan. **DA SUA (2026-07-03 lan 3, sau khi gap loi that tren may
  dev)**: `dub_and_export()` gio bo qua segment co text rong/chi khoang trang
  (nguyen nhan thuc te gay loi edge-tts "No audio was received. Please verify
  that your parameters are correct." - segment rong khong the TTS), va tu
  retry toi da 3 lan (cach nhau 2s) cho loi mang/API thoang qua truoc khi bo
  qua han 1 segment (de lai khoang lang trong video, khong lam fail ca job).
- **2026-07-03 lan 4 - SUA loi giong doc bi ngat quang/loi giua chung** (nguoi
  dung phat hien qua file `.vi.json` thuc te): `optimize_segments()`
  (`application/optimize.py`) chen ky tu xuong dong vao `text` de ngat dong
  HIEN THI tren phu de (toi da 42 ky tu/dong) - nhung `dub_and_export()`
  truoc do dua thang chuoi co xuong dong nay vao TTS, lam giong doc bi
  ngat/loi. Them ham thuan `_clean_text_for_speech()` de gop text ve 1 dong
  lien tuc TRUOC KHI dua vao TTS - CHI anh huong dau vao TTS, khong dung toi
  file phu de xuat ra (van giu nguyen dinh dang xuong dong dung chuan). Co
  test (`tests/test_dub.py`).

**Viec can lam tren may dev that:**
1. `pip install -r requirements.txt` (cai `edge-tts`/`soundfile` moi them).
2. Dam bao da co internet on dinh (edge-tts can goi mang), Celery worker +
   Streamlit dang chay.
3. Cach 1 (khuyen nghi, tu dong): trang Upload, chon ngon ngu long tieng roi
   tao job - job tu chay het khong can thao tac them (xem "Cap nhat
   2026-07-03" phia tren). Cach 2 (lam lai/doi ngon ngu): vao Editor, chon
   job, o khoi "Long tieng" bam "Dich + Long tieng".
4. Theo doi log Celery worker - van co the loi o lan chay dau (adapter
   `tts_edge.py`/`audio_mux.py` moi doi, chua test full end-to-end that).
5. Khi xong, video `<file>.<lang>.dubbed.mp4` xuat hien trong Dashboard/Editor
   - phat thu kiem tra giong doc + audio khop timeline, xac nhan `_work/` da
   duoc xoa sach (chi con file ket qua trong thu muc output).
6. Bao lai loi/log cu the (dac biet loi ket noi edge-tts, hoac loi filter
   `atempo` chain) de sua tiep.

## 6j. Wizard "Tao video" 6 buoc (nang cap lon 2026-07-03, tham chieu UI VietDub)

**CAP NHAT 2026-07-05 (lan 1): da BO HOAN TOAN tinh nang dan URL
YouTube/Douyin/TikTok o Buoc 1 (theo yeu cau nguoi dung "chi cho phep upload
thoi") - xem muc 9 nhat ky cung ngay.

**CAP NHAT 2026-07-05 (lan 2, DAO NGUOC MOT PHAN quyet dinh tren): Codex (lam
song song tren cung repo, xem quy uoc HANDOFF.md o dau file) da TU VIET LAI
tinh nang tai video tu link trong 1 phien khac, KHONG biet quyet dinh xoa o
tren - nguoi dung xac nhan MUON GIU LAI ban moi nay (khac ban cu da xoa: y
khong con dung yt-dlp+cookie/Playwright nua, chi con yt-dlp thuan +
endpoint `/api/jobs/source/analyze` xem truoc metadata/chon chat luong truoc
khi tai). Da xac nhan qua boi canh cheo (git log + git grep) ban CU
(`cookie_refresh.py`, dependency `playwright`, `YTDLP_COOKIES_FILE`,
`storage/browser_profile/`) KHONG con sot lai gi - chi co dung 1 ban tai
video DUY NHAT (ban moi cua Codex) trong repo, khong bi lan giua 2 cach.
Phat hien + sua 1 bug that do merge 2 nhanh khong dong bo:
`frontend/src/lib/constants.ts` (`PIPELINE_STEPS`) thieu stage `"download"`
ma backend (`app/jobs/stages.py` `PIPELINE_STAGES`, do Codex viet lai) da co
- hau qua: thanh tien do chi tiet hien SAI ten buoc ("Tach audio" thay vi
"Tai video") luc job dang tai. Da them lai entry `download` vao
`PIPELINE_STEPS` cho khop 1:1 voi backend (11 buoc ca 2 phia). Cung sua 1
test cua Claude Code (`tests/test_pronunciation.py`) bi fail sau khi nguoi
dung tu bo sung ~500 tu vao `pronunciation_glossary.json` (trong do co tu
"Server" trung voi chuoi test mau "SQL server") - doi test dung glossary co
dinh cuc bo thay vi doc file JSON that, tranh vo lai khi nguoi dung sua file.
96/96 pytest pass, `npm run build` pass sau khi sua. Phan "Buoc 1 - Nguon" mo
ta lich su ben duoi (viet luc tinh nang con dung yt-dlp+cookie cu) GIU LAI de
hieu boi canh nhung CHI TIET KY THUAT co the KHONG con khop voi
`downloader_ytdlp.py` hien tai (ban Codex viet lai hoan toan tu dau, khong
dung cookie/Playwright) - xem code that trong repo de biet chinh xac.

**Trang thai:** Code xong, `pytest` 76/76 pass + `ruff` sach (chay that tren
may dev). **CHUA chay thu end-to-end qua UI** - can restart Celery worker +
Streamlit roi thu theo muc "Viec can lam" ben duoi.

Nguoi dung dua screenshot app "VietDub" lam tham chieu, yeu cau nang cap
Upload thanh wizard 6 buoc voi tinh nang tuong ung. Da viet lai
`app/pages/1_Upload.py` thanh 6 tab (`st.tabs` - ben hon fake-stepper khi
Streamlit rerun); TOAN BO lua chon gom vao 1 dict `options` truyen cho
`process_video_job(job_id, options)` va luu `job_config.json` vao thu muc
job (trace + nut "Tao lai voi cau hinh nay" o Dashboard).

**Buoc 1 - Nguon:**
- Dan URL YouTube/Douyin/TikTok... thay vi phai upload file: adapter moi
  `subtitle_pipeline/infrastructure/downloader_ytdlp.py` (goi
  `sys.executable -m yt_dlp` de chac dung venv; `--restrict-filenames`;
  chat luong "720p"/"best"). Tai trong WORKER (stage moi "download", them
  vao `PIPELINE_STAGES`); job tao voi `filename=URL` placeholder, worker
  cap nhat ten/duong dan that qua `JobRepository.update_source()` moi.
- Kiem thu doan ngan: chon 60s/120s dau -> worker cat bang ffmpeg
  (`trim_media`/`_build_trim_command` moi trong `infrastructure/audio.py`,
  `-c copy` khong re-encode).
- Ep cung ngon ngu nguon (mac dinh van auto-detect):
  `FasterWhisperTranscriber` nhan them `language=` (None = auto), tasks
  override `transcriber_factory` khi user ep.

**Buoc 2 - Giong doc:**
- `voice_catalog(language)` moi trong `tts_edge.py`: moi giong co gender/
  style tag (`VOICE_STYLES`)/co `recommended` (giong ban dia len dau, badge
  sao o UI).
- Toc do noi (-50%..+50%) + cao do (-20Hz..+20Hz): `EdgeTTSSynthesizer`
  nhan `rate_percent`/`pitch_hz`, truyen vao `edge_tts.Communicate(rate=,
  pitch=)`.
- Nut "Nghe thu giong nay": `synthesize_sample()` moi - sinh mp3 cau mau
  ngay trong Streamlit (can internet), cache theo (giong, rate, pitch)
  trong session_state.

**Buoc 3 - Dich:**
- Bang thuat ngu: module moi `application/glossary.py` -
  `parse_glossary`/`mask_terms`/`restore_terms` (thay term nguon bang token
  `<<T0>>` truoc khi NLLB dich, thay token bang term dich sau) - cach kha
  thi duy nhat ep NLLB giu dung thuat ngu. **RUI RO chua verify: NLLB co
  the "dich" ca token** - restore da dung regex chiu khoang trang chen
  giua de giam rui ro, can test that.
- Preset trinh bay ("Can bang"/"Suc tich"/"Thoai mai") map sang
  `max_chars_per_line`/`max_lines` cua `optimize_segments` (tham so moi
  cua `translate_and_export`).
- ~~**GIOI HAN TRUNG THUC:** "dich theo ngu canh/giong dieu" kieu VietDub can
  LLM - NLLB khong nhan chi dan. Ghi ro o UI; LLM translator adapter la
  viec sau (can API key).~~ - **DA LAM (2026-07-15, xem muc 6q)**: co
  GeminiTranslator (GEMINI_API_KEY trong .env), fallback NLLB.

**Buoc 4 - Phu de:**
- `SubtitleStyle` dataclass moi trong `export/formats.py` (font/co chu/mau
  chu/mau+do day vien/vi tri tren-giua-duoi/hop nen dac/do mo nen);
  `to_ass(segments, style)` - mac dinh khop CHINH XAC header cu (co test
  chot: `test_to_ass_default_style_matches_legacy_header`).
- Hardsub: `burn_subtitles()` trong `audio_mux.py` - ffmpeg `ass=` filter,
  re-encode libx264 CRF theo preset. LUU Y Windows: filter `ass=` parse
  loi duong dan co `C:\` -> lenh chay voi `cwd=thu muc chua .ass` va chi
  truyen TEN file (xem `_build_burn_command`).
- Xem truoc tinh bang HTML/CSS mo phong style (khong can ffmpeg).

**Buoc 5 - Am thanh & Xuat:**
- `_build_mux_command` viet lai: `original_volume` (slider 0-100%, 0 = xoa
  tieng goc - GOP 2 radio cu thanh 1 slider), `dub_volume` (50-150%),
  `ducking` (ffmpeg `sidechaincompress` + `asplit` - tu nen tieng goc khi
  giong long tieng dang noi). Bo tham so `keep_original_audio` cu.
- Dinh dang mp4/mkv + preset chat luong dung (`QUALITY_CRF`
  fast/balanced/high - chi ap dung khi hardsub).

**Buoc 6 - Xem lai:** the tom tat tung nhom cau hinh + nut "Tao va khoi
chay". Dashboard co them nut "Tao lai voi cau hinh nay" (doc
`job_config.json`; job URL thi worker tu tai lai, job file thi copy file
goc sang thu muc job moi - khong tham chieu chung, xoa job cu khong hong
job moi).

**Plumbing:** `dub_and_export()` doi sang nhan `DubRenderOptions` dataclass
(voice/rate/pitch/volumes/ducking/format/hardsub/style/quality) thay cho
tham so roi. `dub_job` (Editor) giu signature don gian cu, map
`keep_original_audio` -> `original_volume=0.3`. Them dependency `yt-dlp`.

**Test moi/cap nhat:** `test_downloader.py`, `test_glossary.py`,
`test_export_formats.py` (styled ASS), `test_audio_mux.py` (ducking/volume/
burn), `test_tts_voices.py` (catalog/rate/pitch), `test_audio_timing.py`
(trim), `test_job_repository.py` (update_source), `test_dub.py`
(DubRenderOptions).

**Viec can lam tren may dev that:** restart Celery worker + Streamlit, roi:
1. Dan 1 link YouTube ngan, che do "Chay thu 60 giay dau" -> xac nhan ra
   video long tieng (stage "download" hien tren Dashboard).
2. Buoc 2: bam "Nghe thu giong nay" voi vai giong (dac biet giong
   multilingual doc tieng Viet - chua danh gia chat luong that).
3. Bat "Giam am goc khi co loi thoai" + volume goc 30% -> nghe thu tieng
   goc co tu nho di khi giong dich noi khong.
4. Bat "Gan phu de vao video" voi style tuy chinh -> xac nhan chu ve dung
   vi tri/mau/co; render cham hon ro ret la binh thuong (re-encode).
5. Nhap bang thuat ngu 1-2 muc -> kiem tra term duoc giu dung trong ban
   dich (rui ro token bi NLLB dich - xem Buoc 3 o tren).

## 6k. UI React + FastAPI backend (2026-07-03/04 - THAY THE Streamlit lam UI chinh)

**Trang thai:** Code xong. `pytest` 91/91 pass (15 test backend moi), `ruff`
sach, `npm run build` pass (tsc + vite), smoke test THAT tren Postgres:
health/register/admin-login/meta-voices/admin-users deu OK. **CHUA test E2E
flow tao job qua UI React** - xem "Viec can lam".

Nguoi dung ket luan Streamlit khong du cho UI chuyen nghiep. Quyet dinh nay
DAO NGUOC 2 quyet dinh cu: (1) "Streamlit xuyen suot, khong FastAPI", (2)
"xoa hoan toan Auth".

**Cap nhat 2026-07-04 (cung ngay) - DA XOA HOAN TOAN Streamlit** (nguoi dung:
"bỏ streamlit đi ko cần nữa, tối ưu toàn bộ cho source mới"), khong con giu
lam legacy nhu du dinh ban dau - UI React da du dung de thay the hoan toan.
Da xoa: `app/pages/` (1_Upload.py, 2_Dashboard.py, 3_Editor.py), `app/Home.py`,
`app/ui.py` (chi con dung boi Streamlit, logic that da chuyen het sang
`app/jobs/stages.py` tu truoc), `.streamlit/config.toml`. Bo dependency
`streamlit`, `pandas` (chi Editor.py dung) khoi `requirements.txt`. Bo 2 dong
`per-file-ignores` E402 cho `app/Home.py`/`app/pages/*.py` trong
`pyproject.toml` (khong con file nao can ngoai le nay). Them job
`frontend-build` (npm install + `npm run build`) vao `.github/workflows/ci.yml`
de CI cung xac nhan FE build duoc, khong chi BE. **91/91 pytest + ruff sach
sau khi xoa** (xac nhan khong con gi phu thuoc code Streamlit cu).

**Kien truc:**
- **`backend/`** - FastAPI (`python -m uvicorn backend.main:app --port 8000`):
  - `db.py` - session factory dung chung (lazy singleton, test override bang
    `set_session_factory`).
  - `security.py` - bcrypt + JWT (SESSION_SECRET_KEY). **Admin la tai khoan
    CHUNG tu env `ADMIN_EMAIL`/`ADMIN_PASSWORD`** (mac dinh admin@local/
    admin123 - DOI trong .env), khong nam trong bang users, token role=admin.
    Token nhan qua header Bearer HOAC query `?token=` (cho `<video>`).
  - `routers/auth.py` - register/login/me. `routers/jobs.py` - CRUD job
    (multipart file + options JSON string hoac source.url), rerun, files
    (nhom video/phu de + preview), download/stream. `routers/meta.py` -
    languages/voices/voice-sample. `routers/admin.py` - users (kem job
    count), xoa user (kem job cua ho), toan bo jobs.
  - Ownership: user chi thay job minh; admin thay het; job cu `user_id=NULL`
    chi admin thay. Sai chu tra 404 (khong lo thong tin).
  - Startup migration: `ALTER TABLE jobs ADD COLUMN IF NOT EXISTS user_id`
    (khong can reset DB).
- **DB**: them lai `User` + `Job.user_id` (nullable) vao `app/db/models.py`;
  `app/users/repository.py` moi; `JobRepository.list_by_user` +
  `create(user_id=)`.
- **`app/jobs/stages.py`** moi - PIPELINE_STAGES/stage_progress tach khoi
  `app/ui.py` (von import streamlit) de backend dung duoc; `app/ui.py`
  re-export.
- **`frontend/`** - Vite + React 18 + TypeScript + Tailwind +
  react-router-dom + TanStack Query (Node 22 co san tren may):
  - `/` Landing (hero + 6 tinh nang + 3 buoc + CTA, theme cam/kem kieu
    VietDub), `/login`, `/register`.
  - `/studio` - danh sach job (metric, filter, progress bar nhieu doan,
    poll 3s, xoa/tao lai). `/studio/new` - **wizard 6 buoc stepper sidebar
    THAT** (Nguon/Giong doc/Dich/Phu de/Am thanh & Xuat/Xem lai) - options
    dict giu NGUYEN schema cu nen Celery worker khong doi.
    `/studio/jobs/:id` - chi tiet: video player inline (token query), tai
    phu de theo nhom, xem truoc noi dung.
  - `/admin` - bang users (xoa kem job) + toan bo jobs.
  - Dev: Vite proxy `/api` -> localhost:8000 (khong vuong CORS).
- Dependency moi: fastapi, uvicorn[standard], python-multipart,
  pydantic[email], pyjwt, bcrypt (requirements.txt); frontend/package.json
  rieng.

**Cach chay day du (4 tien trinh):**
1. `docker compose up -d` (Postgres 15432 + Redis 6379)
2. `python -m celery -A app.jobs.celery_app worker --loglevel=info`
3. `python -m uvicorn backend.main:app --port 8000`
4. `cd frontend && npm run dev` -> mo http://localhost:5173

**Viec can lam (E2E qua UI React):** dang ky tai khoan -> wizard tao job tu
URL YouTube che do 60s -> xem progress tren Studio -> mo chi tiet xem video
+ tai phu de -> dang nhap admin@local/admin123 -> kiem tra thay user + toan
bo job, thu xoa user. Bao loi de sua tiep.

## 7. Quyet dinh moi / thay doi so voi ban dau

- **2026-07-01 - Bo qua thu tu roadmap goc:** Nguoi dung chon viet Phase 2 truoc
  khi Phase 1 co ket qua do tren may that (chua xac nhan VRAM/thoi gian thuc te).
  Chap nhan rui ro: pipeline Phase 2 co the OOM hoac dung sai model size khi chay
  thuc te - se phai sua lai sau khi co so lieu that.
- **2026-07-01 - Bo Silero VAD nhu mot buoc rieng trong pipeline chinh thuc
  (Phase 2):** Faster-Whisper co san `vad_filter=True` (dung Silero VAD noi bo)
  de loc khoang lang, nen mot adapter VAD doc lap se trung lap chuc nang ma
  khong co noi tieu thu ket qua ro rang trong luong chinh. Script
  `phase1_feasibility/step03_vad.py` van giu de do hieu nang rieng, nhung
  `subtitle_pipeline/` khong co adapter/port VAD rieng.
- **2026-07-01 - Tiep tuc Phase 3 truoc khi Phase 1/2 duoc xac minh tren may
  that:** Nguoi dung yeu cau lam tiep, chua can push len GitHub. Rui ro Phase 2
  (OOM, model size) van con nguyen, gio them ca rui ro Phase 3 (Postgres/Redis/
  Celery/Streamlit chua duoc khoi dong lan nao). Ưu tien khi len may dev that la
  chay theo dung thu tu: Phase 1 -> Phase 2 CLI -> Phase 3 web UI, de cac loi
  duoc phat hien va sua o lop don gian nhat truoc.
- **2026-07-02 - Chot chuan code chung (Ruff + pytest + pre-commit):** Xem chi
  tiet trong `docs/CODE_STYLE.md`. Ap dung cho ca Claude Code va Codex tu thoi
  diem nay. Chua chay `ruff check`/`ruff format` tren code Phase 1-3 da viet
  truoc do (sandbox khong co Python that) - can chay 1 lan tren may dev that de
  chuan hoa toan bo code cu (xem muc 8).
- **2026-07-02 - Refactor toan bo phase1_feasibility de xoa trung lap voi
  subtitle_pipeline (Phase 2):** Doi ten file (`0X_ten.py` -> `stepNN_ten.py`,
  `00_env_check.py` -> `check_env.py`, lam phang `utils/measure.py` ->
  `measure.py`) va sua `step01/02/04/05/06` de goi TRUC TIEP adapter trong
  `subtitle_pipeline/infrastructure/` thay vi tu viet lai logic goi thu vien AI.
  Ly do: truoc do Phase 1 va Phase 2 co 2 ban song song cua cung 1 logic (goi
  FFmpeg/DeepFilterNet3/Faster-Whisper/WhisperX/pyannote), de lech nhau theo
  thoi gian va vi pham DRY; sau khi sua, so lieu VRAM/thoi gian do o Phase 1
  phan anh dung hieu nang cua code se chay that trong production. `step03_vad`
  khong doi vi khong co adapter VAD tuong duong trong subtitle_pipeline. Chua
  chay thu lai tren may dev that sau refactor nay (xem muc 8).
- **2026-07-02 - Viet toan bo Phase 4-8 trong 1 lan, theo yeu cau ro rang cua
  nguoi dung** ("hoan thanh not du an luon hoan thien toan bo va san sang test
  de co loi se sua sau"). Phase 9 (Monitoring/Scale) CO CHU DICH khong lam,
  giu dung quyet dinh goc trong roadmap (chi lam khi co traffic that). Xem chi
  tiet tung phase o muc 6d-6h. Day la lan mo rong pham vi lon nhat tu truoc
  den nay trong 1 lan - CHUA co bat ky phan nao trong Phase 4-8 duoc chay thu.

- **2026-07-03 - Xay dung flow long tieng (dubbing) day du, ket thuc bang 1
  file video co giong doc thay cho phu de text don thuan (Phase 5b, xem muc
  6i).** Truoc do flow "dich" chi dung o xuat phu de dich (srt/vtt/ass/txt/
  json) - nguoi dung phat hien qua thu muc job mau
  (`storage/498a6250-.../output/`) chi co phu de, khong co audio/video moi,
  va yeu cau hoan thien den ket qua cuoi cung. Chot qua trao doi voi nguoi
  dung:
  - Ngon ngu dich/long tieng chinh: **tieng Viet**. Loai Coqui XTTS-v2 (voice
    cloning tot nhat) vi khong ho tro tieng Viet, chon MMS-TTS
    (`facebook/mms-tts-vie` qua `transformers`) vi co checkpoint tieng Viet,
    dung chung thu vien da co, VRAM nhe.
  - **Khong lam voice cloning o v1** - dung giong doc chuan/trung tinh cho
    moi cau (khong clone giong nguoi noi goc). Co the nang cap sau.
  - **UI gop lam 1 nut duy nhat** "Dich + Long tieng" o Editor (khong bat
    nguoi dung bam "Dich" xong roi moi bam "Long tieng" rieng) - Celery task
    `dub_job` tu dong dich truoc neu chua co file dich.
  - Dong bo audio-video moi o muc "khop khung thoi gian" (ffmpeg `atempo`
    time-stretch tung cau khop `[start, end]` cua segment goc), KHONG phai
    lip-sync that.
- **2026-07-03 - Du an chuyen huong thanh ca nhan/phi thuong mai, BO gioi han
  usage/goi cuoc (Phase 7):** nguoi dung xac nhan "khong thuong mai nua chi
  la project ca nhan... bo luon phan limit di". Da xoa khoi kiem tra
  `subscription`/`plan_info`/`minutes_used` + `st.stop()` chan upload trong
  `app/pages/1_Upload.py`. **Khong xoa** `app/billing/` hay
  `app/pages/4_Billing.py` (van giu de xem usage tham khao, chi bo phan chan
  cung). Ly do quyet dinh nay lien quan truc tiep: vi khong con rang buoc
  thuong mai nen viec chon model TTS non-commercial license (MMS-TTS,
  CC-BY-NC) o tren cung khong con la van de.
- **2026-07-03 - XOA HOAN TOAN Auth (Phase 6) + Billing (Phase 7), khong con
  gioi han "chi bo phan chan" nhu quyet dinh truoc:** nguoi dung yeu cau ro
  "coi source nay chi la Tool ca nhan thoi... bo di luon phan dang nhap Authen
  cac kieu... xoa luon phan billing va cach tinh toan thoi gian". Khac voi
  quyet dinh 2026-07-03 phia tren (chi tat gioi han, giu code billing lai),
  lan nay xoa SACH:
  - `app/auth/` (`security.py`, `repository.py`, `streamlit_helpers.py`),
    model `User`.
  - `app/billing/` (`plans.py`, `usage.py`, `repository.py`),
    `app/pages/4_Billing.py`, model `PlanTier`/`Subscription`.
  - Cot `Job.user_id` (khong con khai niem "chu so huu job" - moi job hien
    thi cho tat ca, tool 1 nguoi dung).
  - Dependency `bcrypt`, `pyjwt`, `extra-streamlit-components`; bien env
    `SESSION_SECRET_KEY`.
  - `JobRepository.list_by_user()` -> cac trang gio dung `list_all()`.
  - `require_login()` bi go khoi `1_Upload.py`, `2_Dashboard.py`,
    `3_Editor.py`; `Home.py` bo hien thi trang thai dang nhap.
  **Anh huong DB:** day la thay doi schema (bo cot/bang) - `create_all()`
  KHONG tu xoa cot/bang cu, xem canh bao reset DB o muc 8.

## 6l. Tu dong lay cookie YouTube bang Playwright (2026-07-05, xoa roi KHOI PHUC lai cung ngay)

**Dong doi 2 lan trong cung 1 ngay - doc ky de khoi nham lan:**
1. Xoa hoan toan cung luc voi tinh nang tai URL (theo yeu cau "chi cho phep
   upload thoi") - xem muc 9 nhat ky lan lien quan.
2. Codex (lam song song, xem quy uoc HANDOFF.md dau file) sau do TU VIET LAI
   tinh nang tai video tu link (dua theo repo tham khao cua nguoi dung,
   github.com/DauDinhQuangAnh/Youtube_link) nhung KHONG co co che cookie -
   dan den tai lai dung loi cu "Sign in to confirm you're not a bot" ma muc
   nay tung duoc tao ra de giai quyet. Da doi chieu repo tham khao: repo do
   **KHONG xu ly van de nay** (README ghi ro "intentionally does not
   include ... anti-bot circumvention"), nen khong co gi de "hoc theo" tu
   do - phai tu khoi phuc lai co che cookie cua chinh du an nay.
3. Nguoi dung xac nhan chon khoi phuc Playwright auto-refresh (thay vi
   cookies.txt thu cong hoac chap nhan gioi han) - **DA KHOI PHUC LAI**, xem
   "Cap nhat 2026-07-05 (khoi phuc)" o cuoi muc nay. Module/endpoint/nut UI
   mo ta ben duoi (viet luc con Douyin trong scope) **VAN CON DUNG THAT**,
   chi khac 1 diem: ban khoi phuc bo Douyin khoi `DEFAULT_SITES` (chi con
   YouTube, khop dung scope hien tai cua `downloader_ytdlp.py` - khong con
   nhac gi toi Douyin nua).

**Trang thai (lich su luc viet lan dau - xem cap nhat khoi phuc o cuoi muc
de biet trang thai THAT hien tai):** Code xong, test that (107/107 pytest pass, ruff sach,
`npm run build` pass). Da smoke-test THAT tren may (Playwright + Chromium
that, khong gia lap) - xem phat hien quan trong ve Douyin ben duoi.

**Boi canh:** nguoi dung gap loi tai video YouTube/Douyin qua yt-dlp bi chan
"Sign in to confirm you're not a bot" / "Fresh cookies are needed". Cach cu
(export cookies.txt qua extension trinh duyet, hoac
`YTDLP_COOKIES_FROM_BROWSER`) deu bat tien (thao tac tay, hoac loi khoa file
neu trinh duyet dang mo - da xac nhan tren may nay: Edge/Chrome deu dang mo
lien tuc). Nguoi dung yeu cau tim cach "manh hon, tien hon".

**Da nghien cuu + xac nhan bang thu nghiem THAT truoc khi code:**
- Test `--extractor-args "youtube:player_client=android,web,tv"`: tai duoc
  YouTube KHONG can cookie nhung bi gioi han ~360p (YouTube da ap "SABR
  streaming" + "n challenge" can JS runtime de mo khoa chat luong cao, yt-dlp
  bao "JS Challenge Providers: unavailable" dù may co Node.js) - khong dung
  cach nay, giu chat luong 720p uu tien.
- Test HTTP request thuong (`requests`) toi douyin.com de tu lay cookie: chi
  lay duoc 1 cookie (`__ac_nonce`), THIEU cac cookie do JAVASCRIPT tao ra
  (`ttwid`, `odin_tt`, `msToken`...) - xac nhan can trinh duyet THAT (chay
  JS) chu khong the gia lap bang HTTP request don thuan.
- Xem repo tham khao nguoi dung dua (github.com/jiji262/douyin-downloader):
  xac nhan dung dung Playwright de lay cookie tu dong - dung huong da chon,
  khong co "meo" nao khac.
- **PHAT HIEN QUAN TRONG (khien Douyin khong the fix bang cookie):** doc
  truc tiep source code yt-dlp (`yt_dlp/extractor/tiktok.py`, class
  `DouyinIE._real_extract`) thay dong comment
  `# TODO: Run verification challenge code to generate signature cookies`
  ngay truoc loi "Fresh cookies (not necessarily logged in) are needed".
  Day la GIOI HAN CUA CHINH YT-DLP (chua code xong buoc giai verification
  challenge cua Douyin), KHONG PHAI do cookie cu/thieu. Da thu voi 44 cookie
  that lay tu Playwright (dieu huong den dung URL video, cho 5s, co ca
  `passport_csrf_token`/`ttwid`/`odin_tt`) - van loi y het. **Ket luan: Douyin
  se KHONG tai duoc cho toi khi yt-dlp tu code xong phan nay**, bat ke cookie
  nao. YouTube khong co van de nay (khong TODO tuong tu trong code), nen giai
  phap Playwright van co gia tri day du cho YouTube.

**Kien truc (`subtitle_pipeline/infrastructure/cookie_refresh.py`):**
- 2 CHE DO tach rieng vi ly do khac nhau:
  - `setup_login_session(profile_dir)`: mo Chromium THAT (khong an,
    `headless=False`) qua `launch_persistent_context` - nguoi dung tu dang
    nhap YouTube/Douyin 1 LAN trong do (co the giai CAPTCHA neu co), nhan
    Enter trong terminal de luu profile + dong trinh duyet. CHI chay duoc tu
    terminal (CLI), KHONG the goi tu backend API vi server khong co man
    hinh cho nguoi dung tuong tac.
  - `refresh_cookies(output_path, profile_dir)`: mo LAI CUNG profile o che
    do AN (`headless=True`) - tai su dung session dang nhap da luu, khong
    can dang nhap lai, chi ghe qua tung trang de lay cookie MOI (bao gom ca
    cookie JS tao ra). AN TOAN de goi tu dong/dinh ky hoac qua API.
- `_cookie_to_netscape_line()` - ham thuan chuyen 1 cookie Playwright (dict)
  sang dinh dang Netscape ma yt-dlp `--cookies` doc duoc; cookie phien
  (`expires=-1`) duoc gia han 1 nam thay vi ghi -1 (Netscape/yt-dlp coi gia
  tri am la het han, se bo qua). Test rieng trong `tests/test_cookie_refresh.py`
  (khong can Playwright/trinh duyet that).
- CLI: `python -m subtitle_pipeline.infrastructure.cookie_refresh --setup`
  (chay 1 lan dau) / `--refresh` (chay lai bat cu khi nao can, doc
  `YTDLP_COOKIES_FILE` tu env de biet ghi vao dau).
- **`backend/routers/admin.py`**: them `POST /admin/refresh-cookies`
  (admin-only, `require_admin`) - goi `refresh_cookies()` qua
  `asyncio.to_thread` (Playwright sync API se chan/block, khong duoc goi
  truc tiep trong async route handler). Loi ro rang neu chua chay `--setup`
  lan nao (browser profile chua ton tai).
- **`frontend/src/pages/Admin.tsx`**: them nut "Lam moi cookie" + ghi chu ro
  rang Douyin chua tai duoc du co cookie moi (tranh nguoi dung ky vong sai).
- Dependency moi: `playwright>=1.47.0` (them vao `requirements.txt`). **CAN
  CHAY THEM 1 LAN SAU KHI `pip install`:**
  `python -m playwright install chromium` (tai ~150-300MB browser binary,
  da xac nhan chay thanh cong tren may nay).
- `.env.example`: `YTDLP_COOKIES_FILE=cookies.txt` la mac dinh moi (thay cho
  de trong) - khop voi noi `cookie_refresh.py --refresh` ghi ra.
  `storage/browser_profile/` (profile luu session dang nhap) nam trong
  `storage/` da duoc `.gitignore` toan bo tu truoc, khong can them dong moi.

**Ban dau ve deploy VPS (nguoi dung hoi, ghi lai de tham khao sau):**
Playwright chay tot tren Linux headless (thiet ke cho dung truong hop nay),
khong kho setup (`playwright install --with-deps chromium`). NHUNG van de
lon hon la **uy tin IP**: YouTube/Douyin chan IP datacenter/VPS gat hon
nhieu so voi IP nha rieng, du cookie/Playwright hoan hao van co the bi chan
thuong xuyen hon - can proxy residential/mobile tra phi de on dinh. Rieng
pipeline AI (Whisper/WhisperX/pyannote/DeepFilterNet) can GPU CUDA - VPS
thuong (DigitalOcean, Linode...) khong co GPU, phai thue loai co GPU rieng
(RunPod, Vast.ai, AWS g4/g5...) dat hon nhieu, hoac chay CPU se cham hon
10-20 lan. Chua quyet dinh/lam gi cho huong VPS, chi ghi nhan de ban khi
can deploy that.

**Viec nguoi dung can lam:**
1. `pip install -r requirements.txt` (them `playwright`).
2. `python -m playwright install chromium` (1 lan).
3. `python -m subtitle_pipeline.infrastructure.cookie_refresh --setup` -
   dang nhap YouTube (va Douyin neu muon, du hien chua tai duoc) trong cua
   so trinh duyet mo ra, nhan Enter trong terminal khi xong.
4. Vao trang Admin (dang nhap admin@local...), bam "Lam moi cookie" bat cu
   khi nao gap loi cookie het han - khong can lam lai buoc 3 tru khi profile
   bi xoa hoac session dang nhap thuc su het han (hiem, thuong vai thang).
5. Restart Celery worker sau khi cookies.txt duoc tao/cap nhat lan dau (de
   chac chan doc dung file moi - thuc ra `YTDLP_COOKIES_FILE` doc lai moi
   lan tai, khong can restart, nhung restart 1 lan cho chac an toan).

**Cap nhat 2026-07-05 (khoi phuc, sau khi bi xoa roi gap lai loi cu):**
Nguoi dung bao loi that "Sign in to confirm you're not a bot" khi dung
tinh nang tai video tu link (ban Codex viet lai, khong co cookie). Da doi
chieu repo tham khao nguoi dung dua (github.com/DauDinhQuangAnh/Youtube_link,
clone ve doc source that) - xac nhan repo do **cung khong xu ly duoc van de
nay** (ghi ro trong README, `friendly_yt_dlp_error` khong co nhanh nao cho
"not a bot"/cookie). Nguoi dung chon khoi phuc lai Playwright auto-refresh
(so voi 2 phuong an khac: cookies.txt thu cong, hoac chap nhan gioi han).
Da khoi phuc + noi vao dung cau truc MOI cua `downloader_ytdlp.py` (khac
ban cu o cho: khong con Douyin trong scope, dung `analyze_video()`/
`download_video()` thay vi ham cu):
- `subtitle_pipeline/infrastructure/cookie_refresh.py` - khoi phuc gan
  nguyen ban tu git history (commit `d3d4a1b`), CHI bo Douyin khoi
  `DEFAULT_SITES` (chi con `{"youtube": "https://www.youtube.com/"}` - dung
  huong dan setup/refresh, dinh dang Netscape cookie giu nguyen).
- `subtitle_pipeline/infrastructure/downloader_ytdlp.py`: them ham moi
  `_cookie_options()` (doc `YTDLP_COOKIES_FILE` tu env, tra ve
  `{"cookiefile": path}` neu file ton tai, nguoc lai `{}`) va spread vao
  dict `opts` cua CA `analyze_video()` lan `download_video()` (repo tham
  khao/ban Codex ca 2 ham nay von khong truyen cookie gi ca). Them nhanh
  moi trong `friendly_yt_dlp_error()` nhan dien "sign in to confirm"/"not a
  bot"/"fresh cookies"/"cookies are needed" -> tra ve thong bao huong dan
  bam "Lam moi cookie" trong Admin.
- `backend/routers/admin.py`: khoi phuc `POST /admin/refresh-cookies`
  (giong het logic cu, goi `refresh_cookies()` qua `asyncio.to_thread`).
- `frontend/src/pages/Admin.tsx`: khoi phuc section "Cookie tải video
  (YouTube)" + nut "Làm mới cookie" (bo cau chu ve Douyin khoi mo ta, chi
  con nhac YouTube).
- `requirements.txt`: them lai `playwright>=1.47.0`. `.env.example`: them
  lai `YTDLP_COOKIES_FILE=cookies.txt` kem huong dan setup.
- Test: khoi phuc `tests/test_cookie_refresh.py` (bo cac test-case rieng
  cho Douyin, chi giu test chung cho ham thuan `_cookie_to_netscape_line`/
  `_write_netscape_file`); them moi `tests/test_downloader.py` (module nay
  TRUOC DAY CHUA CO TEST NAO - kiem tra `_cookie_options()` + nhanh bot-check
  moi trong `friendly_yt_dlp_error()`); them 3 test cho endpoint
  `/admin/refresh-cookies` trong `tests/test_backend_api.py`.
114/114 pytest pass, ruff sach, `npm run build` pass. **Chua chay
`--setup`/`--refresh` that voi Chromium that trong phien nay** (sandbox
khong the mo trinh duyet that) - nguoi dung can tu chay
`pip install -r requirements.txt` + `python -m playwright install chromium`
+ `python -m subtitle_pipeline.infrastructure.cookie_refresh --setup` roi
thu tai lai 1 video YouTube tung bi chan de xac nhan het loi.

## 6m. Bang phat am rieng cho giong doc long tieng (2026-07-05)

**Trang thai:** Code xong, 94/94 pytest pass (them `tests/test_pronunciation.py`),
ruff sach, `npm run build` pass. **CHUA nghe thu that voi edge-tts tren may
dev** - can nguoi dung tao 1 job tieng Viet co tu "SQL" trong cau de xac nhan
audio doc thanh "ét quy eo" dung nhu ky vong.

**Boi canh:** nguoi dung nhan xet Buoc 3 "Dich" khong co cho chon ngon ngu
dich (that ra nam o Buoc 2 "Giong doc", chi la khong hien thi lai o Buoc 3
nen de nham lan), va muon co the tuy chinh CACH PHAT AM cua giong doc TTS cho
tung tu/thuat ngu - vi du "SQL" thuong doc la "ét quy lờ" nhung muon mac dinh
la "ét quy eo". Da hoi lai nguoi dung 2 diem truoc khi code:
- Pham vi anh huong: **CHI giong doc (audio)**, KHONG doi chu hien thi tren
  phu de (khac voi bang thuat ngu dich hien co - `application/glossary.py` -
  von giu nguyen CHU VIET khi dich, khong lien quan cach doc).
- Noi chinh sua: **CA 2** - 1 file JSON mac dinh trong repo (nguoi dung tu
  sua truc tiep de dung lau dai) VA 1 o nhap tren web (rieng cho 1 job) -
  uu tien gia tri tren web truoc, thieu thi rot ve JSON mac dinh.

**Kien truc:**
- `subtitle_pipeline/infrastructure/pronunciation_glossary.json` - file JSON
  mac dinh, cau truc `{"<ma_ngon_ngu>": {"<tu>": "<cach_doc>"}}`. Hien chi co
  du lieu cho `"vi"` (nguoi dung xac nhan lam tieng Viet truoc), seed 1 muc
  vi du `"SQL": "ét quy eo"` - nguoi dung se tu bo sung them qua thoi gian
  bang cach sua truc tiep file nay (khong can code/deploy lai).
- `subtitle_pipeline/application/pronunciation.py` (module moi):
  `load_default_pronunciation(language)` doc file JSON tren;
  `parse_pronunciation_overrides(text)` parse textarea nguoi dung nhap rieng
  cho 1 job (cung format `tu = cach doc` voi bang thuat ngu dich, nhung la
  truong du lieu HOAN TOAN tach biet); `resolve_pronunciation_glossary(
  language, overrides_text)` gop 2 nguon (override textarea thang qua JSON
  neu trung tu, khong phan biet hoa thuong); `apply_pronunciation(text,
  glossary)` thay tu khop nguyen tu (tu dai thay truoc tu ngan, giong
  logic `glossary.py`).
- `subtitle_pipeline/application/dub.py`: `DubRenderOptions` them field
  `pronunciation: dict[str, str]`. Trong `dub_and_export()`, goi
  `apply_pronunciation()` ngay sau `_clean_text_for_speech()` - TRUOC khi
  dua text vao `tts.synthesize()` - nen CHI anh huong audio, cac file phu de
  xuat ra (`translate_and_export()` trong `translate.py`) hoan toan khong
  doi.
- `app/jobs/tasks.py`: `_build_dub_options()` (flow chinh tu wizard Upload)
  goi `resolve_pronunciation_glossary(target_language, translation.get(
  "pronunciation", ""))` truyen vao `DubRenderOptions`. `dub_job` (Celery
  task rieng cua Editor, khong co o nhap override) ap dung it nhat bang JSON
  mac dinh qua `resolve_pronunciation_glossary(target_language)`.
- Frontend (`frontend/src/lib/types.ts`): `JobOptions.translation` them field
  `pronunciation: string` (mac dinh rong). `frontend/src/pages/NewJob.tsx`
  Buoc 3 them:
  - 1 dong thong tin dau trang hien ro dang dich/long tieng sang ngon ngu
    nao (doc tu `dubbing.target_language` da chon o Buoc 2) + nut nhay
    nhanh ve Buoc 2 de doi - giai quyet nhan xet ban dau cua nguoi dung ve
    viec "khong thay cho chon ngon ngu" o buoc nay. Neu long tieng dang tat,
    hien canh bao buoc nay khong co tac dung (vi `process_video_job` chi goi
    `translate_and_export`/`dub_and_export` khi `dubbing.enabled=true`, xem
    `app/jobs/tasks.py`).
  - Textarea moi "Bang phat am cho giong long tieng" (mau `SQL = ét quy eo`)
    ngay duoi o "Bang thuat ngu" hien co, cung dinh dang `tu = cach doc`.
  - The tom tat o Buoc 6 (Xem lai) them dong dem so muc bang phat am rieng
    canh dong dem bang thuat ngu.

**Han che/rui ro chua kiem chung:**
- Chua nghe thu that tren may dev xem edge-tts doc "ét quy eo" co tu nhien
  hon "SQL" nguyen ban hay khong - day la gia dinh ngon ngu hoc cua nguoi
  dung, can nguoi dung tu danh gia va bo sung/sua entry trong file JSON neu
  chua ung y.
- `apply_pronunciation` dung `\b` (word boundary) - co the khop nham 1 phan
  cua cau neu tu viet tat trung voi 1 tu thuong (vd. neu sau nay them entry
  "AI" ma cau co "AI" la viet tat khac ngu canh) - chap nhan duoc o pham vi
  hien tai (danh sach nho, nguoi dung tu kiem soat noi dung file JSON).

## 6n. Telegram bot - tai video qua chat, nhan link/email rieng (2026-07-07)

**Trang thai:** Code viet boi nguoi dung/Codex (khong phai Claude Code), Claude
Code duoc yeu cau **rà soát lại** ("kiểm tra coi code có đang ổn không") -
xem ket qua ra soat + cac cho da sua o duoi. 116/116 pytest pass, ruff sach.
**Chua chay bot that voi Telegram token that** trong phien ra soat nay.

**Muc dich:** Luong RIENG voi web UI - nguoi dung nhan link YouTube/Douyin
qua Telegram, bot tu tai + long tieng, roi tra ket qua qua Telegram (link
tai co chu ky, khong can dang nhap web) hoac qua email (link tai truc tiep,
khac voi email web dung cho nguoi dung DA CO tai khoan).

**Kien truc:**
- `app/jobs/service.py` (module moi) - `create_download_job()`: tao 1 job
  tai-tu-URL y het schema wizard web (`default_download_job_options()`),
  ghi `job_config.json`, enqueue `process_video_job` Celery task - dung
  chung PIPELINE voi web, chi khac o CHO TAO job (khong qua backend API/
  React) va them field tuy chon `options["telegram"]` (`chat_id`,
  `notify_email`) de Celery task biet co can bao Telegram khi xong khong.
- `app/telegram_bot/` (module moi, package rieng):
  - `client.py` - `TelegramClient`, goi thang Telegram Bot API qua
    `urllib.request` (KHONG them dependency python-telegram-bot nao ca).
  - `bot.py` - `TelegramJobBot.run_forever()`: vong lap polling
    `getUpdates`, may trang thai don gian per-chat (`self.pending`) cho
    luong "gui link -> hoi tai chat luong nao -> hoi gui email hay lay
    link -> tao job". Loc chat duoc phep qua `TELEGRAM_ALLOWED_CHAT_IDS`
    (de trong = AI CUNG dung duoc bot - luu y neu may chay AI pipeline
    nang, nen dien gioi han de tranh nguoi la lam ton GPU).
  - `notifier.py` - `notify_telegram_job_done()`/`notify_telegram_job_failed()`,
    goi tu `app/jobs/tasks.py` (hook nho o cuoi `process_video_job`, boc
    trong `with suppress(Exception)` nen KHONG anh huong job web binh
    thuong neu Telegram loi/chua cau hinh - chi kich hoat khi
    `options["telegram"]` co mat).
- `backend/share_links.py` (module moi) - `create_file_share_token()`/
  `verify_file_share_token()`: token HMAC-SHA256 tu ky (base64url
  payload + base64url chu ky, KHONG dung JWT vi khong can decode noi
  dung, chi can verify), mang theo `job_id`/`filename`/`exp` - cho phep
  TAI 1 FILE CU THE ma khong can dang nhap web (khac han token JWT dang
  dung cho `AuthUser`). Het han theo `PUBLIC_LINK_TTL_SECONDS` (mac dinh
  7 ngay).
- `backend/routers/public.py` (router moi, KHONG qua `get_current_user`) -
  `GET /api/public/jobs/{job_id}/files/{name}?token=...`: verify token roi
  serve file, chong path traversal giong het `jobs.py::download_file`
  (chi khop file la con truc tiep cua `output_dir`).
- `backend/email_sender.py` them ham `send_direct_download_email()` (khac
  `send_job_result_email()` da co - ham cu gui link toi trang job yeu cau
  dang nhap, ham moi gui thang link tai da ky, dung cho nguoi dung Telegram
  khong nhat thiet co tai khoan web).
- `.env.example` them nhom `TELEGRAM_*` (token, allowlist chat id, chat
  luong/ngon ngu/trim mac dinh) + `BACKEND_PUBLIC_URL`/
  `PUBLIC_LINK_TTL_SECONDS`/`PUBLIC_LINK_SECRET` (fallback ve
  `SESSION_SECRET_KEY` neu de trong).
- `start_project.ps1`/`stop_project.ps1`: tu chay/dung process bot NEU
  `TELEGRAM_BOT_TOKEN` co dien trong `.env`, bo qua neu khong (khong bat
  buoc phai dung tinh nang nay).

**Cac loi/diem chua toi uu phat hien khi Claude Code ra soat + DA SUA:**
- **Ro ri ket noi DB (quan trong nhat):** `create_download_job()` ban dau
  goi `JobRepository()` khong tham so -> mac dinh goi `make_session_factory()`
  MOI LAN GOI, tao engine + connection pool MOI + chay lai `create_all()`
  (chinh `backend/db.py` da canh bao dieu nay "rat nang neu lap lai"). Vi
  bot Telegram song lau trong 1 vong lap polling va goi ham nay moi khi co
  nguoi xac nhan tai video, moi job se ro ri 1 pool ket noi Postgres khong
  bao gio dong - co the can Postgres `max_connections` neu dung nhieu. Da
  sua: them tham so `job_repo_factory=job_repo` (dung lai `backend.db.job_repo`
  - CUNG 1 session factory singleton ma FastAPI backend dang dung).
- Dead-code + kho doc: `bot.py::run_forever()` dung ternary-lam-statement
  de gui tin nhan khoi dong, kem 1 nhanh fallback `or self.allowed_chat_hint()`
  KHONG BAO GIO chay toi (vi dieu kien ngoai da dam bao truoc do). Da doi
  thanh `if` binh thuong, xoa `allowed_chat_hint()` (khong con noi nao goi).
- 3 loi ruff E501 (dong qua 100 ky tu) trong `bot.py`/`notifier.py` - da sua.
- `tests/test_telegram_job_service.py` cap nhat theo tham so
  `job_repo_factory` moi (truoc do monkeypatch thang class `JobRepository`).

**Da xac nhan KHONG dong den:** flow tao job qua web (`backend/routers/jobs.py`)
hoan toan khong doi - `options["telegram"]` la field tuy chon, job web binh
thuong khong co field nay nen `notify_telegram_job_done()` return ngay o
dong dau (`if not chat_id: return`).

**Van de con lai (chua sua, ghi nhan de theo doi):**
- `TELEGRAM_ALLOWED_CHAT_IDS` de trong theo mac dinh = AI CO Telegram username
  cua bot deu dung duoc, kich hoat job GPU nang - day la lua chon co y trong
  `.env.example` (ghi ro trong comment), nhung nen nhac nguoi dung dien gioi
  han neu may dev chi co 1 GPU dung chung nhieu viec.
- Secret ky token (`PUBLIC_LINK_SECRET`) fallback ve `SESSION_SECRET_KEY` roi
  fallback tiep ve chuoi hardcode `dev-secret-doi-khi-deploy` neu ca hai deu
  trong - giong het pattern JWT hien co (khong phai loi moi), nhung dang
  y hon voi link nay vi KHONG CAN dang nhap de dung - nen dien
  `SESSION_SECRET_KEY` that truoc khi de bot public.
- Chua co test end-to-end that voi Telegram Bot API that (chi test
  `create_download_job()` bang fake repo/task).

## 6o. Trang "Sua phu de" (Editor) trong UI React (2026-07-14)

**Trang thai:** Code xong, chay THAT tren may dev (Python that tai
`D:\hoctap\python\python.exe` - khac mo ta cu trong HANDOFF ve sandbox khong
Python, xem ghi chu dau file CLAUDE.md ve viec tu kiem tra lai moi truong):
`pytest` 121/121 pass (them 8 test moi), `ruff check`/`ruff format` sach,
`npm run build` (tsc + vite) pass. **Chua tu tay mo trinh duyet click qua
UI that** (can Docker Postgres/Redis/Celery dang chay) - xem "Viec can lam".

**Boi canh:** nguoi dung hoi "du an co the phat trien tiep gi khong", duoc
de xuat vai huong (bat SMTP/Telegram co san, lam lai Editor, doi dich sang
LLM, verify end-to-end) va chon **lam lai trang Sua phu de** - tinh nang nay
bi mat khi xoa Streamlit (2026-07-04, xem muc 8 cu) va chua duoc port sang
React.

**Kien truc (dua theo `app/pages/3_Editor.py` cu, xem lai qua
`git show becda70:app/pages/3_Editor.py` - commit truoc khi xoa):**
- **Backend (`backend/routers/jobs.py`)** - 5 route moi tren `/jobs`:
  - `GET /{id}/subtitles/{language}` - doc `{stem}.json` (language="goc")
    hoac `{stem}.{language}.json` (ban da dich), tra ve list segment.
  - `PUT /{id}/subtitles/{language}` - nhan list segment da sua, ghi de CA 5
    dinh dang qua `FORMAT_WRITERS` (dung dinh dang ten file voi
    `translate_and_export()`/`process_video_job` de khop 1:1).
  - `POST /{id}/translate` - goi `translate_job.delay(job.id, target_language)`
    (task co san tu Phase 5b/Editor cu, khong doi). Yeu cau `job.status ==
    DONE`.
  - `POST /{id}/dub` - goi `dub_job.delay(job.id, target_language, voice,
    keep_original_audio)` (task co san, tham so roi giu nguyen tu ban cu).
  - `GET /{id}/original` - serve `job.input_path` (file goc nam trong job_dir,
    KHONG nam trong `output_dir` nen khong xuat hien qua `/files` hien co) -
    dung cho `<video>` xem lai khi sua timing, cung ho tro token qua query
    (`get_current_user` da ho tro san, khong can sua `security.py`).
  - Schema moi trong `backend/schemas.py`: `SubtitleSegmentOut`,
    `UpdateSubtitlesIn`, `TranslateJobIn`, `DubJobIn`.
- **Frontend (`frontend/src/pages/Editor.tsx`, route moi
  `/studio/jobs/:id/edit`)** - 3 tab giong cau truc Editor Streamlit cu:
  - **Chinh sua phu de:** chon ngon ngu (tu `files.subtitles` - danh sach
    nhom phu de co san tra ve boi `/jobs/{id}/files`), video/audio canh bang
    danh sach segment dang form co the sua (khong dung bang/grid nhu
    `st.data_editor` vi khong co thu vien tuong duong san co - moi segment 1
    "card" voi input start/end/speaker + textarea text), nut "Them dong"/
    "Xoa dong", nut "Luu va xuat lai file" goi `PUT /subtitles/{lang}`.
  - **Dich phu de:** chon ngon ngu dich (tu `/meta/languages`), nut goi
    `POST /translate` - chi xuat phu de, khong tao audio (giong y het editor
    cu).
  - **Long tieng lai:** chon ngon ngu + giong (tu `/meta/voices/{lang}`,
    dropdown rong = mac dinh) + checkbox "Giu tieng goc giam 70%", nut goi
    `POST /dub`.
  - `frontend/src/lib/api.ts` them `put()` (chua co truoc do, chi co
    get/post/postForm/del) va `originalUrl()` (cung mau `fileUrl()`, tro
    `/jobs/{id}/original`).
  - `frontend/src/lib/types.ts` them `SubtitleSegment`.
  - `JobDetail.tsx` them nut "Sua phu de" (o ca 2 nhanh: co video ket qua LAN
    truong hop job DONE nhung chua co video dubbed - vd. chi bat phu de,
    khong bat long tieng).
- Test moi trong `tests/test_backend_api.py` (8 test): doc/sua subtitles
  (thanh cong + 404 khi thieu ngon ngu), dich/long tieng (enqueue task khi
  job DONE + tu choi 400 khi chua DONE), tai file goc.

**Khac voi ban Streamlit cu (co y, khong phai thieu sot):**
- Khong dung bang/grid keo-sua-hang-loat (`st.data_editor` co
  `num_rows="dynamic"`) - moi segment la 1 khoi form rieng, phu hop web
  thuan (khong co thu vien data-grid nao trong `frontend/package.json`).
  Neu video co RAT nhieu segment (video dai), UX nay se cham hon - danh gia
  lai neu nguoi dung phan nan, luc do co the can them 1 thu vien
  table/grid (vd. TanStack Table) hoac ao hoa danh sach (virtualization).
- Video xem lai luon la file GOC (`GET /original`) hoac video dubbed KHOP
  ngon ngu dang chon (neu co) - khac ban cu chi co 1 `st.video(input_path)`
  co dinh, khong doi theo tab ngon ngu.

**Viec can lam tren may dev that:** bat Docker (`docker compose up -d`) +
Celery worker + `uvicorn`/`npm run dev`, mo 1 job DONE that, vao
`/studio/jobs/:id/edit`:
1. Tab "Chinh sua phu de": doi text/timing 1 dong, bam "Luu va xuat lai
   file", xac nhan file `.srt`/`.json`... trong `storage/<job_id>/output/`
   da cap nhat dung.
2. Tab "Dich phu de": dich sang 1 ngon ngu chua co, cho Celery chay xong,
   quay lai tab dau chon ngon ngu do, xac nhan doc/sua duoc phu de moi dich.
3. Tab "Long tieng lai": chon giong khac, bam "Dich + Long tieng", cho xong,
   kiem tra video moi xuat hien trong `/jobs/{id}/files` (videos).

## 6p. Clone giong long tieng (VieNeu-TTS) (2026-07-14)

**Trang thai:** Code xong, chay THAT tren may dev (`D:\hoctap\python\python.exe`
- xem muc 6o ve phat hien Python that trong sandbox nay): `pytest` 131/131
  pass (them 12 test moi), `ruff check`/`ruff format` sach, `npm run build`
  pass. **QUAN TRONG - khac voi hau het adapter AI khac trong du an: DA SPIKE
  THAT co che clone giong truoc khi viet code chinh thuc** (khong phai
  "viet xong roi cho nguoi dung tu chay thu tren may that" nhu thong le) -
  xem chi tiet spike o duoi. Van con 1 phan CHUA verify duoc trong sandbox
  nay (khong co ffmpeg): buoc resample cuoi cung trong
  `VieNeuCloneSynthesizer.synthesize()` (`ffmpeg -ar 24000 -ac 1`) - da xac
  nhan code chay dung TOI NGAY TRUOC buoc nay (model load, encode reference,
  infer, ghi wav 48kHz deu OK), chi ban than lenh ffmpeg (giong het pattern
  da dung trong `tts_edge.py`) la chua chay duoc trong sandbox.

**Boi canh:** nguoi dung hoi "dự án hiện tại có thể phát triển tiếp gì
không", duoc de xuat 4 huong (SMTP/Telegram, Editor React, dich LLM, verify
end-to-end) va chon lam Editor truoc (xem muc 6o). Sau khi xong Editor,
nguoi dung de xuat them 1 tinh nang moi: "khu clone giong" - nguoi dung doc
1 doan van, he thong dung do lam giong long tieng thay cho giong co san,
va yeu cau **nghien cuu cong nghe + flow tot nhat** truoc khi lam.

**Nghien cuu cong nghe (xem chi tiet da trinh bay voi nguoi dung, tom tat
lai o day de tra cuu sau):**
- Coqui XTTS-v2 (voice cloning tot nhat pho bien): **KHONG co tieng Viet**
  trong 17 ngon ngu ho tro - da bi loai tu dau du an (xem muc 6i).
- OpenVoice V2 (MyShell/MIT): tieng Viet **KHONG nam trong danh sach ngon
  ngu native** (en/es/fr/zh/ja/ko) - chi "zero-shot cross-lingual", chat
  luong tieng Viet khong chac chan.
- RVC (Retrieval-based Voice Conversion): kha thi (VRAM 6GB du de train)
  nhung can **buoc train rieng** (10-30 phut audio sach/giong) + kien truc
  2 tang (TTS tao noi dung dung tieng Viet -> RVC doi timbre) phuc tap hon.
  Ghi nhan la huong nang cap sau neu chat luong VieNeu-TTS khong du tot.
- **VieNeu-TTS (github.com/pnnbao97/VieNeu-TTS, tac gia ca nhan, Apache-2.0)
  - CHON huong nay:** model TTS tieng Viet NATIVE (10.000+ gio du lieu
  Anh-Viet) co san clone giong zero-shot (chi can 3-8 giay audio tham
  chieu, khong can buoc train rieng nhu RVC), chay CPU duoc (ONNX, ban
  "v3turbo") nen nhe VRAM, offline hoan toan (khac edge-tts can internet).
  Cai qua `pip install vieneu`.

**Spike da chay THAT truoc khi code (2026-07-14):**
1. `pip install vieneu` (cai them ca `edge-tts` de sinh 1 clip tieng Viet
   lam reference audio thu nghiem, khong co san sample that trong sandbox).
2. Gap loi 401 khi tai model tu HuggingFace (co che tang toc "Xet") - sua
   bang bien moi truong `HF_HUB_DISABLE_XET=1` (da dat lam mac dinh trong
   code, xem `tts_vieneu.py`).
3. Gap loi thieu `torchaudio` (dung boi buoc trich speaker embedding, du
   tai lieu ghi "CPU torch-free") - cai them
   `pip install torchaudio --index-url https://download.pytorch.org/whl/cpu`.
   **LUU Y quan trong cho may dev that:** `requirements.txt` da ghi chu ro
   torchaudio gio la BAT BUOC (khong chi torch) - buoc cai torch/torchaudio
   thu cong (muc 0) van dung, chi can dam bao dung ca 2.
4. Sau khi sua 2 diem tren: tai model thanh cong (~13s sau khi cache am,
   ~3.5 phut lan dau tai tu HuggingFace), clone giong tu clip edge-tts, sinh
   cau moi - xac nhan qua `soundfile` audio dau ra hop le (RMS ~0.1, khong
   im lang/khong loi). Toc do CPU: ~30s cho 3.6s audio (~8x cham hon thoi
   gian thuc) - QUA CHAM de dung that tren CPU, nhung tren GPU CUDA that
   (RTX 4050), thu vien tu chuyen backend PyTorch (device="auto") nhanh hon
   nhieu - **CHUA do toc do thuc te tren GPU that**.
5. Test rieng `VieNeuCloneSynthesizer` (class adapter chinh thuc, khong
   phai script spike) - xac nhan chay dung toi ngay truoc buoc ffmpeg
   resample cuoi (khong co ffmpeg trong sandbox nay).

**Kien truc:**
- `subtitle_pipeline/infrastructure/tts_vieneu.py` (moi) - `VieNeuCloneSynthesizer`
  (VoiceSynthesizer Protocol, giong `EdgeTTSSynthesizer`): `__enter__` load
  model + `encode_reference()` MOT LAN (khong phai moi segment), `synthesize()`
  goi `infer(text, voice=<speaker_emb+codes da cache>)` roi ghi wav + ffmpeg
  resample ve 24kHz mono (khop `tts_edge.OUTPUT_SAMPLE_RATE`). Ham thuan
  `probe_reference_seconds()` do do dai audio (dung o backend de tu choi
  mau qua ngan).
- `subtitle_pipeline/application/dub.py`: `DubRenderOptions` them field
  `custom_voice_ref_audio: Path | None`. Neu dat, `dub_and_export()` dung
  **1 `VieNeuCloneSynthesizer` DUY NHAT cho CA VIDEO** (bo qua hoan toan
  `_build_speaker_voice_map`/nhieu-giong-theo-nguoi-noi va
  `voice`/`rate_percent`/`pitch_hz` cua edge-tts) - pham vi v1 CHUA ho tro
  nhieu giong clone khac nhau cho nhieu nguoi noi trong 1 video (ghi nhan
  o muc 8 neu can nang cap sau).
- `app/db/models.py`: model moi `CustomVoice` (id, user_id, name,
  ref_audio_path, created_at) - KHONG luu speaker embedding (numpy array),
  `VieNeuCloneSynthesizer` tu ma hoa lai tu file moi lan dung (1 lan/job,
  khong phai 1 lan/segment) de tranh serialize numpy array qua Celery.
  Bang tao tu dong qua `create_all()` (khong can ALTER/reset DB nhu khi them
  `Job.user_id` truoc day).
- `app/voices/repository.py` (moi) - `CustomVoiceRepository`, cung mau
  `JobRepository`/`UserRepository`. `backend/db.py` them `custom_voice_repo()`.
- `backend/routers/voices.py` (moi, `/api/voices`): `POST` (multipart
  name+file, ffmpeg transcode ve wav 24kHz, tu choi neu `probe_reference_seconds
  < MIN_REFERENCE_SECONDS` (3s)), `GET` (list theo user), `DELETE` (xoa DB
  + file, kiem tra chu so huu). Ham `get_owned_voice()` export de
  `backend/routers/jobs.py` tai su dung (kiem tra quyen truoc khi enqueue
  job dung custom voice).
- `backend/routers/jobs.py`: `_create_job_from_options()` (wizard) va
  `POST /{id}/dub` (Editor) deu kiem tra `custom_voice_id` thuoc dung user
  truoc khi enqueue (tra 404 neu khong phai chu, giong pattern `_get_owned_job`).
  `DubJobIn` them field `custom_voice_id`.
- `app/jobs/tasks.py`: ham moi `_resolve_custom_voice_ref_audio()` (doc
  `ref_audio_path` tu DB qua `CustomVoiceRepository`, tra `None` neu giong
  da bi xoa - roi ve edge-tts thay vi lam fail job). Dung trong ca
  `_build_dub_options()` (wizard, doc `dubbing.custom_voice_id` tu options)
  lan `dub_job` Celery task (Editor, them tham so `custom_voice_id`).
- Frontend: trang moi `frontend/src/pages/Voices.tsx` (route `/voices`,
  link tu NavBar) - ghi am truc tiep qua `MediaRecorder` (API trinh duyet
  chuan, khong them thu vien) VOI 1 doan van mau goi y san de doc, HOAC tai
  file audio co san len; danh sach giong da tao + nut xoa. `NewJob.tsx`
  (Buoc "Giong doc") va `Editor.tsx` (tab "Long tieng lai") deu them lua
  chon "Giong co sanh" / "Giong da clone" (an cac o toc do/cao do/nghe thu
  giong khi dung giong clone, vi khong ap dung).

**Test moi:** `tests/test_tts_vieneu.py` (`probe_reference_seconds` - ham
thuan, khong can model that). `tests/test_dub.py`: 1 test moi xac nhan
`dub_and_export` dung 1 synthesizer clone duy nhat cho ca video du nhieu
nguoi noi (khac han co che xoay vong giong cua edge-tts). `tests/test_backend_api.py`:
9 test moi (`POST/GET/DELETE /voices`, tu choi mau qua ngan, phan quyen so
huu giong o ca 2 duong tao job wizard lan `/dub` cua Editor) - stub
`subprocess.run`/`probe_reference_seconds` (khong goi ffmpeg/audio that
trong test, giong tinh than cac test khac trong repo).

**Han che/rui ro CHUA kiem chung tren may dev that (GPU that):**
- Chat luong giong clone tieng Viet thuc te CHUA duoc nguoi dung nghe thu
  danh gia - spike chi xac nhan pipeline CHAY DUOC, khong danh gia chat
  luong am thanh qua tai.
- Toc do inference tren GPU CUDA that (RTX 4050) CHUA duoc do - CPU trong
  spike qua cham (~8x realtime) de dung production, ky vong GPU nhanh hon
  nhieu nhung chua co so lieu that.
- VRAM peak cua VieNeu-TTS v3-turbo tren GPU CHUA duoc do - can luu y ngan
  sach 6GB dang chia se voi Whisper/pyannote/NLLB (kien truc load-tuan-tu
  hien co van ap dung: `VieNeuCloneSynthesizer` la 1 buoc rieng trong
  `dub_and_export`, khong chay dong thoi voi buoc nao khac).
- 1 giong clone CHI ap dung cho TOAN BO video (khong ho tro nhieu giong
  clone khac nhau theo tung nguoi noi trong 1 video) - gioi han co y cho v1.
- Buoc ghi am qua `MediaRecorder` trong trinh duyet **CHUA duoc thu qua
  trinh duyet that** (sandbox khong co man hinh/micro) - dinh dang blob tra
  ve (thuong la `audio/webm`) da duoc xu ly qua ffmpeg transcode phia
  server nen ly thuyet tuong thich, nhung chua xac nhan bang mat.
- `vieneu` keo theo `gradio`+`pandas` (dependency cua chinh no, du an
  KHONG dung gradio - chi import class TTS) - lam nang requirements.txt
  hon can thiet, chap nhan duoc de tranh tu viet lai wrapper HuggingFace.

**Viec nguoi dung can lam tren may dev that:**
1. `pip install -r requirements.txt` (cai `vieneu`, keo theo gradio/pandas/
   onnxruntime...). Dam bao co ca `torchaudio` (khong chi `torch`) - neu
   thieu, cai bang lenh CUDA phu hop (xem muc 0 buoc 4, doi index-url tu
   cu121 sang cu128 dung driver dang co).
2. Neu tai model loi 401/qua cham: kiem tra bien moi truong `HF_HUB_DISABLE_XET`
   (da dat mac dinh=1 trong code, chi can quan tam neu van loi).
3. Vao `/voices`, doc thu doan van mau (hoac tai 1 file ghi am san), luu
   giong, xac nhan xuat hien trong danh sach.
4. Tao 1 job moi (hoac vao Editor cua job DONE), chon "Giong da clone" o
   buoc Giong doc, chon giong vua tao, chay het job - nghe thu video ket
   qua, danh gia chat luong that + do toc do xu ly that tren GPU.
5. Bao lai loi/danh gia chat luong de tinh chinh (vd. doi sang RVC neu chat
   luong VieNeu-TTS khong du, hoac dieu chinh do dai/chat luong reference
   audio goi y).

## 6q. Nang cap chat luong "Uu tien 3" (2026-07-15): audio fit + Gemini + Alembic

3 nang cap lam cung 1 phien theo yeu cau nguoi dung (chon tu danh sach de
xuat sau lan ra soat du an). Toan bo da chay THAT: 155/155 pytest pass,
ruff sach, `npm run build` pass tren sandbox co Python that.

**1. Chong chong lan/troi audio khi long tieng** (giai quyet danh doi ghi
nhan tu 2026-07-03 lan 8 khi bo hoan toan atempo):
- `application/dub.py`: ham thuan moi `_fit_target_duration(clip_duration,
  window)` + `_fit_clips_to_timeline()`. Sau khi synthesize xong tat ca
  clip, clip nao dai hon khoang trong toi START cua cau ke tiep (qua nguong
  `FIT_TOLERANCE=1.05`) se duoc TANG TOC bang ffmpeg atempo, nhung toi da
  `MAX_TEMPO_FACTOR=1.3` (nguong nghe con tu nhien - khac co che cu ep khop
  cung [start, end] bat ke factor, lam giong nghe do). Vuot nguong van tran
  thi chap nhan chong lan phan du + in canh bao tong hop ra log worker.
  Loi ffmpeg khi stretch chi lam clip do dung ban raw, khong fail job.
- `infrastructure/audio_mux.py` `build_dub_track`: doan chong lan gio TRON
  CONG (`+=`) thay vi gan de (`=`) - truoc do clip sau cat cut clip truoc
  roi con de sot duoi clip truoc phat lai sau khi clip sau ket thuc (artifact
  te hon ca chong lan). Co `np.clip` ve [-1, 1] chong vo tieng khi cong don.
- Test moi trong `tests/test_dub.py` (5 test `_fit_target_duration` + 2 test
  tich hop stretch/loi stretch) va `tests/test_audio_mux.py` (tron cong +
  clip bien do). **CHUA nghe thu tren video that** - can tao job voi video
  co cau noi day (vd. tieng Anh nhanh dich sang tieng Viet dai hon) va nghe
  doan truoc day bi chong lan.

**2. Dich theo ngu canh bang Google Gemini (LLM)** (lam duoc dieu ghi "can
LLM - viec sau" o muc 6j):
- Adapter moi `subtitle_pipeline/infrastructure/translator_gemini.py`
  (`GeminiTranslator`) - cung interface context-manager + `translate()` voi
  `NLLBTranslator`. Goi REST `generateContent` truc tiep qua urllib stdlib
  (KHONG them dependency - cung ly do email_sender dung smtplib). Dich theo
  BATCH 40 cau/request de giu ngu canh xuyen suot + it request; ep tra JSON
  array dung so phan tu (`response_mime_type=application/json`), retry 3
  lan/batch, temperature 0.2.
- `application/translate.py`: ham moi `_translate_segments()` - co
  `GEMINI_API_KEY` trong env thi dung Gemini, khong co HOAC Gemini loi
  (mat mang/het quota sau khi retry) thi tu fallback ve NLLB local ngay
  trong cung lan dich - tinh nang dich khong bao gio phu thuoc cung Gemini.
- `.env.example`: them `GEMINI_API_KEY` (tao mien phi tai
  https://aistudio.google.com/apikey) + `GEMINI_MODEL` (mac dinh
  `gemini-2.5-flash`). UI Buoc 3 wizard cap nhat ghi chu engine.
- Test moi `tests/test_translator_gemini.py` (11 test: prompt/parse/batch/
  retry/chon engine/fallback - mock `_call_api`, khong goi mang). **CHUA
  goi API Gemini that lan nao** - can dien key that vao `.env` roi chay 1
  job dich de xac nhan prompt/parse hoat dong voi response that.

**3. Alembic migration cho DB** (het canh "doi schema la phai reset DB"):
- File moi: `alembic.ini` (goc repo), `migrations/env.py` (doc DATABASE_URL
  tu .env/bien moi truong, dung chung nguon voi app/db/session.py),
  `migrations/versions/0001_initial_schema.py` - baseline co GUARD inspector:
  DB moi tinh thi tao du 3 bang (users/jobs/custom_voices), DB co san do
  `create_all()` tao truoc day thi bo qua bang da co + chi va cot
  `jobs.user_id` neu thieu. Tu revision 0002 tro di viet ALTER binh thuong
  (`python -m alembic revision -m "..." --autogenerate`).
- `backend/main.py`: `_ensure_schema()` (ALTER tay `user_id`) thay bang
  `_run_migrations()` goi `alembic upgrade head` luc khoi dong - van nuot
  loi co chu dich (test/sandbox khong co Postgres van khoi dong duoc).
- `make_session_factory()` GIU NGUYEN `create_all` (test SQLite + tien dev),
  khong xung dot vi baseline co guard.
- `requirements.txt`: them `alembic>=1.13.0`.
- Test moi `tests/test_migrations.py` (4 test chay THAT upgrade tren SQLite
  file tam: DB moi / chay 2 lan idempotent / nhan nuoi DB create_all / doi
  chieu cot migration khop cot ORM). **CHUA chay tren Postgres that** - lan
  dau chay backend tren may dev, xem log khoi dong xac nhan
  `alembic_version` duoc tao trong DB (khong can lam gi them, tu dong).

## 8. Van de dang mo / can quyet dinh

- ~~Chua co trang "Sua phu de" (Editor) trong UI React~~ - **DA LAM LAI
  (2026-07-14)**, xem muc 6o.
- **Clone giong long tieng (VieNeu-TTS, muc 6p) CHUA duoc verify tren GPU
  that** - code xong + spike xac nhan pipeline chay dung (model tai duoc,
  clone giong khong loi), nhung TOC DO (spike CPU ~8x cham hon thoi gian
  thuc), VRAM peak, va CHAT LUONG giong clone tieng Viet thuc te deu chua
  co so lieu tren RTX 4050. Neu chat luong khong dat, xem lai huong RVC da
  ghi nhan trong muc 6p (can them buoc train, phuc tap hon nhung co the
  chat luong on dinh hon).
- **Code Phase 1-3 chua duoc chay qua Ruff/pytest lan nao** - chuan code o
  `docs/CODE_STYLE.md` moi duoc chot (2026-07-02) nhung code truoc do viet
  trong sandbox khong co Python that nen chua verify duoc. Da ra soat thu cong
  toan bo file .py (2026-07-02): sua dong qua 100 ky tu, sua E402 (import sau
  sys.path bootstrap trong app/Home.py + app/pages/*.py - da khai bao ngoai le
  trong `pyproject.toml` `per-file-ignores`), bo type hint du thua trong
  `JobRepository.__init__`. Ra soat tay KHONG thay the duoc viec chay that
  `ruff check --fix .` + `ruff format .` + `pytest` - can lam viec nay dau
  tien tren may dev that (`pip install -r requirements-dev.txt` truoc), roi
  `pre-commit install` de tu dong enforce cho cac lan commit sau.

- **Chua xac minh Phase 1 tren may that (bao gom sau refactor 2026-07-02)** -
  moi so lieu VRAM/thoi gian trong muc 6 con trong. Ten file va cach goi adapter
  vua doi (xem "Quyet dinh moi") - can chay lai tu dau: `check_env.py` roi
  `run_all.py` de xac nhan cac script step0X hoat dong dung sau refactor, truoc
  khi tin tuong so lieu. **Cap nhat 2026-07-13:** `check_env.py` da chay THAT
  tren may dev (khong phai sandbox) va PASS toan bo (ffmpeg, torch 2.8.0+cu128
  CUDA=True tren RTX 4050, faster_whisper/whisperx/pyannote.audio/df/
  transformers/edge_tts/soundfile da cai, HF_TOKEN da set) - moi truong da san
  sang, nhung `run_all.py` VAN CHUA chay (khong co file mau nao trong
  `phase1_feasibility/samples/`, thu muc `results/` chua ton tai) nen bang so
  lieu VRAM/thoi gian van con trong. Can bo 1 file video/audio mau vao
  `phase1_feasibility/samples/` roi chay `run_all.py` +
  `summarize_results.py`.
- **Phase 2: logic dieu phoi da duoc `pytest` xac nhan (2026-07-03, xem muc
  9), nhung CHUA chay voi model AI that/GPU that** - dac biet: giai phong VRAM
  giua cac buoc trong CUNG 1 process (`subtitle_pipeline/infrastructure/gpu.py`)
  co du tranh OOM khi chay lien tiep denoise -> transcribe -> align -> diarize
  hay khong. Neu OOM, phuong an du phong: chay tung buoc trong subprocess
  rieng (nhu `phase1_feasibility/run_all.py`) thay vi trong cung 1 process
  Celery task.
- **Chua xac minh Phase 3 tren may that** - toan bo (docker-compose Postgres/
  Redis, Celery worker, Streamlit multipage, doan them sys.path thu cong o dau
  moi file trong `app/`) chua duoc chay lan nao. Rui ro cao nhat: loi import do
  sys.path (neu Streamlit/Celery version xu ly khac voi gia dinh), va Celery
  worker chay task GPU nang trong tien trinh worker co the gap van de tuong tu
  Phase 2 (OOM) nhung kho debug hon vi chay ngam.
- ~~Repo chua push len GitHub~~ - DA push toan bo Phase 2-8 len
  github.com/DauDinhQuangAnh/testai (2026-07-02) de mang qua may dev that.
- **Chua xac minh Phase 4-8 tren may that** - TOAN BO code Editor, dich thuat,
  storage abstraction, CI moi chi duoc viet va ra soat bang mat (khong chay),
  do sandbox viet code khong co Python that. Danh sach rui ro rieng cua tung
  phan:
  - **Phase 4 (Editor):** `st.data_editor` voi `num_rows="dynamic"` co the co
    hanh vi khac ky vong o phien ban Streamlit cu the; `pd.isna()` xu ly gia
    tri thieu trong cot `speaker` chua duoc kiem chung thuc te.
  - **Phase 5 (Dich - RUI RO CAO NHAT truoc khi co Phase 5b):** `NLLBTranslator`
    dung `tokenizer.convert_tokens_to_ids()` +
    `model.generate(forced_bos_token_id=...)` - cach goi nay hoan toan chua
    duoc chay thu, kha nang cao se can sua lai tham so hoac cach lay ma ngon
    ngu khi test that (xem docstring trong `translator_nllb.py`). Model
    `nllb-200-distilled-600M` (~2.4GB) can tai ve lan dau, cong them VRAM/RAM.
  - ~~Phase 8: `app/storage.py` (S3Storage) hoan toan chua test...~~ - **DA XOA
    (2026-07-13)** theo yeu cau nguoi dung, khong con la van de mo (xem muc 6h
    "Cap nhat 2026-07-13").
- **DB schema vua thay doi (2026-07-03, bo Auth/Billing) - CAN RESET DB truoc
  khi chay lai:** bang `jobs` cu (neu da tung chay `docker compose up` va tao
  job that) co the con cot `user_id NOT NULL` va bang `users`/`subscriptions`
  cu - model Python moi khong con cac truong/bang nay.
  `Base.metadata.create_all()` (`app/db/session.py`) CHI tao bang con thieu,
  KHONG tu ALTER bang da ton tai - neu khong reset, insert Job moi se loi vi
  pham NOT NULL tren cot `user_id` cu. Cach reset (XOA HET DU LIEU JOB CU,
  chi lam neu khong can giu job cu): `docker compose down -v` roi
  `docker compose up -d` de tao lai volume Postgres sach, hoac
  `DROP TABLE jobs, users, subscriptions CASCADE;` thu cong qua `psql`.
- **Phase 5b da chay thu 1 lan tren may that voi MMS-TTS - chat luong giong
  qua te, da doi sang `edge-tts` (xem muc 6i "Cap nhat 2026-07-03 lan 2").
  Ban `edge-tts` CHUA duoc chay thu end-to-end lan nao:**
  - `EdgeTTSSynthesizer` (`tts_edge.py`) can INTERNET on dinh - chua test
    hanh vi khi mat mang giua chung (job that bai giua chung, chua co retry).
  - `time_stretch_to_duration` dung ffmpeg `atempo` da chay duoc voi MMS-TTS
    nhung chua verify lai voi audio dau ra tu `edge-tts` (sample rate/dinh
    dang khac - da ep ve wav 24kHz mono trong `tts_edge.py`, can xac nhan
    `_clamp_atempo_factors` xu ly dung voi do dai cau thuc te cua giong moi).
  - `build_dub_track`/`mux_audio_into_video` da chay duoc 1 lan (video xuat ra
    thanh cong) nhung chat luong giong la van de chinh dan den quyet dinh doi
    TTS - can chay lai voi `edge-tts` de xac nhan video cuoi cung nghe on.
  - Buoc don file (`shutil.rmtree(work_dir)` trong `dub_and_export`) MOI THEM,
    chua chay thu - can xac nhan khong xoa nham file dang can dung (vd. neu
    `dub_job` chay 2 lan song song cho 2 ngon ngu khac nhau tren cung 1 job -
    truong hop hiem, chua xu ly).
- **Uu tien thu tu kiem thu tren may dev that de cach ly loi hieu qua:**
  Phase 1 (`check_env.py` + `run_all.py`) -> Phase 2 CLI -> `pytest` toan bo
  (bao gom `test_optimize.py`, `test_storage.py`, `test_audio_timing.py`,
  `test_audio_mux.py`, `test_dub.py`, `test_job_repository.py`) -> Phase 3 web
  UI (Upload/Dashboard, luu y Upload gio chay het ca transcribe+dich+long
  tieng trong 1 job, khong con can dang nhap - xem muc 6i) -> Phase 4
  (Editor) -> Phase 5 (dich) -> Phase 5b (long tieng, rui ro cao nhat, test
  sau cung) -> Phase 8.

## 9. Nhat ky cap nhat

- 2026-07-01: Tao HANDOFF.md, viet xong code Phase 1 (chua chay thu, cho chay tren
  may dev that co GPU).
- 2026-07-01: Push repo len GitHub (github.com/DauDinhQuangAnh/testai, nhanh main).
- 2026-07-01: Viet xong code Phase 2 (AI Pipeline Core, `subtitle_pipeline/` +
  `tests/`) - CHUA chay thu tren may dev that, Phase 1 cung chua co ket qua do.
- 2026-07-01: Viet xong code Phase 3 (Streamlit App - `app/` + `docker-compose.yml`
  + test JobRepository) - CHUA chay thu, CHUA push len GitHub (theo yeu cau
  nguoi dung, se hoi lai truoc khi commit/push).
- 2026-07-02: Chot chuan code (`docs/CODE_STYLE.md`, Ruff config trong
  `pyproject.toml`, `.pre-commit-config.yaml`) - theo yeu cau nguoi dung, ap
  dung cho ca Claude Code va Codex tu nay ve sau. Chua chay tren code cu (xem
  muc 8).
- 2026-07-02: Ra soat toan bo repo theo yeu cau nguoi dung ("go re phai chac"):
  sua 2 loi lint thuc su (E402 can khai bao ngoai le, type hint du thua trong
  `JobRepository`), va refactor `phase1_feasibility/` de doi ten file ro rang
  hon (`stepNN_ten.py`) va xoa trung lap logic voi `subtitle_pipeline/` (goi
  lai adapter Phase 2 thay vi tu viet lai). Xem chi tiet muc 7 va 8.
- 2026-07-02: Viet xong code Phase 4 (Editor - `app/pages/3_Editor.py`, doi
  huong sang `st.data_editor` thay vi Custom Streamlit Component), Phase 5
  (dich + toi uu subtitle - `subtitle_pipeline/application/optimize.py`,
  `translate.py`, `subtitle_pipeline/infrastructure/translator_nllb.py`),
  Phase 6 (Auth - `app/auth/`, them `User`/`user_id` vao schema), Phase 7
  (Billing/Stripe - `app/billing/`), va mot phan Phase 8 (`app/storage.py`,
  `.github/workflows/ci.yml`, hardening upload). Phase 9 co chu dich khong
  lam. TOAN BO CHUA CHAY THU - xem danh sach rui ro day du va thu tu kiem thu
  de nghi o muc 8.
- 2026-07-02: Them muc "0. Setup nhanh tren may dev that" (checklist gop) va
  push toan bo code Phase 2-8 len GitHub de nguoi dung clone ve may RTX 4050
  chay kiem thu.
- 2026-07-02: BO toan bo thanh toan Stripe theo yeu cau nguoi dung ("khong can
  thanh toan kieu vay qua app"): xoa `app/billing/stripe_service.py`,
  `app/billing/webhook_app.py`, bien env STRIPE_*, dependency
  stripe/fastapi/uvicorn. GIU goi Free/Pro + gioi han phut/thang; nang goi lam
  thu cong qua `SubscriptionRepository.upsert`. `Subscription` model khong con
  cac truong Stripe; `plans.py` doi tu ham `get_plan_catalog()` sang hang so
  `PLAN_CATALOG` (khong con phu thuoc env).
- 2026-07-03: Viet xong code Phase 5b - Long tieng (Dubbing/TTS), hoan thien
  flow den ket qua cuoi cung la 1 file video da long tieng (xem muc 6i):
  `subtitle_pipeline/infrastructure/tts_mms.py` (MMS-TTS qua transformers),
  `audio_timing.py` (time-stretch ffmpeg atempo), `audio_mux.py` (dung track
  + mux vao video), `application/dub.py` (dieu phoi), Celery task `dub_job`
  + helper `_load_or_translate_segments` (`app/jobs/tasks.py`), UI gop 1 nut
  "Dich + Long tieng" trong `app/pages/3_Editor.py`, them `soundfile` vao
  `requirements.txt`, test `test_audio_timing.py`/`test_audio_mux.py`. Cung
  luc, BO gioi han usage/goi cuoc trong `app/pages/1_Upload.py` theo yeu cau
  nguoi dung (du an chuyen thanh ca nhan/phi thuong mai - xem muc 7). TOAN BO
  Phase 5b CHUA CHAY THU, la phan rui ro cao nhat cua du an (xem muc 8).
- 2026-07-03: Xac nhan dang chay tren MAY DEV THAT (RTX 4050 6GB VRAM) - venv
  + torch 2.8.0+cu128 (CUDA available=True) + HF_TOKEN + ffmpeg (qua winget)
  da co san tu truoc. Theo yeu cau nguoi dung don gian hoa flow: gop
  transcribe+dich+long tieng thanh 1 job DUY NHAT kich hoat tu trang Upload
  (chon ngon ngu ngay luc upload, khong can vao Editor bam them buoc nao -
  xem muc 6i "Cap nhat 2026-07-03"). Them tinh nang xoa job (ca DB lan file
  tren dia) o Dashboard (`JobRepository.delete`, checkbox xac nhan + nut "Xoa
  job"). Gop `SUPPORTED_LANGUAGES` ve 1 noi dung
  (`translator_nllb.py`) thay vi hardcode rieng o Upload/Editor.
- 2026-07-03 (lan 2): Nguoi dung chay thu long tieng tren may that, danh gia
  chat luong giong MMS-TTS "qua te". Research va doi TTS backend sang
  `edge-tts` (giong Neural TTS mien phi cua Microsoft, chat luong tot hon han
  - xem HANDOFF.md muc 6i "Cap nhat 2026-07-03 lan 2"): xoa `tts_mms.py`,
  them `tts_edge.py`, `dub_and_export()` bo tham so `device` (khong con can
  GPU cho TTS). Them `edge-tts>=6.1.9` vao requirements.txt. Danh doi:
  adapter nay can internet, khac voi phan con lai cua pipeline (100%
  offline). Cung luc, them buoc TU DONG XOA thu muc `_work/` (audio trung
  gian, clip TTS tam) ngay sau khi long tieng xong, chi giu lai file ket qua
  trong thu muc output - theo yeu cau nguoi dung "xoa file khong can thiet,
  de lai ket qua thoi".
- 2026-07-03 (lan 3): Sau khi cai `edge-tts` va chay thu, gap loi
  "No module named 'edge_tts'" (chua `pip install`, da cai truc tiep vao
  venv), roi loi edge-tts "No audio was received..." khi chay job that. Them
  co che retry (3 lan, cach 2s) + bo qua segment text rong trong
  `dub_and_export()` de job khong fail toan bo vi 1 segment loi.
- 2026-07-03 (lan 4): Nguoi dung phat hien giong doc bi ngat quang/loi khi
  xem file `.vi.json` thuc te - phat hien nguyen nhan: `optimize_segments()`
  chen ky tu xuong dong vao `text` de ngat dong hien thi phu de, nhung
  `dub_and_export()` dua thang text co xuong dong do vao TTS. Them ham
  `_clean_text_for_speech()` de gop text ve 1 dong truoc khi TTS (khong anh
  huong file phu de xuat ra). Co test moi `tests/test_dub.py`.
- 2026-07-03 (lan 5): XOA HOAN TOAN Auth (Phase 6) + Billing (Phase 7) theo
  yeu cau nguoi dung ("coi source nay chi la Tool ca nhan thoi"). Xoa
  `app/auth/`, `app/billing/`, `app/pages/4_Billing.py`, model
  `User`/`PlanTier`/`Subscription`, cot `Job.user_id`,
  `JobRepository.list_by_user()`, dependency `bcrypt`/`pyjwt`/
  `extra-streamlit-components`, bien env `SESSION_SECRET_KEY`. Bo
  `require_login()` khoi `1_Upload.py`/`2_Dashboard.py`/`3_Editor.py`, don
  `Home.py`. Xoa test `test_security.py`/`test_user_repository.py`/
  `test_subscription_repository.py`/`test_usage.py`, sua `test_job_repository.py`
  cho schema moi (bo `user_id`). **CAN RESET DB** (xem muc 8) vi bang `jobs` cu
  co the con cot `user_id NOT NULL`.
- 2026-07-03 (lan 6): **LAN DAU chay `ruff check`/`ruff format`/`pytest` THAT
  tren may dev (truoc gio chi ra soat bang mat do sandbox khong co Python).**
  Sua `JobStatus` sang `enum.StrEnum` (UP042). Phat hien + sua 2 bug CO TU
  TRUOC (Phase 2, chua tung chay) qua pytest that:
  - `tests/test_pipeline.py::test_run_merges_speaker_into_segments`: fixture
    `_make_pipeline()` khong set `hf_token`, khien `TranscriptionPipeline.run()`
    am tham bo qua diarization (dung dung y `test_run_without_hf_token_skips_diarization`)
    - `FakeDiarizer` inject vao test khong bao gio duoc goi, ket qua speaker
    luon la `None` thay vi `SPEAKER_00`/`SPEAKER_01`. Sua: them
    `hf_token="fake-token"` vao `PipelineConfig()` cua fixture.
  - `tests/test_merge.py::test_merge_assigns_dominant_overlapping_speaker`:
    fixture co 2 turn overlap **hoa diem tuyet doi** (ca hai deu 1.0s) voi
    segment - `_dominant_speaker()` (`application/merge.py`) dung
    `if overlap > best_overlap` (strict greater-than) nen turn dau tien thang
    khi hoa, nhung test lai assert turn THU HAI thang. Sua fixture de overlap
    chenh lech ro rang (khong sua logic `merge_speakers`, van giu quy tac
    "turn dau tien thang khi hoa diem" - hop ly, khong can doi).
  - Sua tolerance qua chat trong `tests/test_audio_mux.py` (viet trong phien
    nay) - `soundfile.write` mac dinh ghi wav dang PCM_16 (co luong tu hoa
    ~3e-5), vuot nguong mac dinh cua `np.allclose`; tang `atol=1e-3`.
  Ket qua: **33/33 test pass, `ruff check` sach.**
- 2026-07-03 (lan 7): Reset DB theo yeu cau nguoi dung (sau khi bo `user_id`
  khoi schema). Qua trinh nay phat hien 1 quy uoc rieng cua may dev nay CHUA
  duoc ghi lai: may co san 1 Postgres native (Windows Service) chiem dung
  **port 5432** - vi vay Postgres cho du an nay PHAI chay o port khac.
  `docker-compose.yml` truoc do van khai bao map ra 5432 (KHONG khop thuc te),
  trong khi `.env` that cua nguoi dung da tu sua thanh port **15432** va chay
  Postgres qua 1 container `docker run` rieng (khong qua `docker compose`) -
  2 co che khong dong bo, de gay nham lan (chinh toi da tuong 1 luc DB "da
  reset" nhung thuc ra reset nham container `docker compose` khong ai dung,
  container that qua port 15432 van con nguyen du lieu cu). Da sua:
  `docker-compose.yml` doi port map postgres thanh `15432:5432`,
  `.env.example` doi `DATABASE_URL` mac dinh sang port 15432, xoa container
  `docker run` rieng le, hop nhat lai thanh 1 chuoi quan ly duy nhat qua
  `docker compose up -d`/`down`. Da xac nhan lai bang script that (tao +
  xoa 1 Job qua `JobRepository`) - ket noi + schema hoat dong dung. Ghi chu
  them: **`load_dotenv()` KHONG duoc goi o bat ky dau trong `app/`**
  (`app/config.py`, `app/db/session.py`, `app/jobs/celery_app.py`, cac trang
  Streamlit) - cac ham `from_env()` chi doc `os.environ` truc tiep, nen
  `.env` CHI co tac dung neu shell/terminal dang chay `streamlit`/`celery`
  da tu export cac bien do truoc (hoac dung cong cu nhu `direnv`). Chua ro
  day co phai van de that voi setup hien tai cua nguoi dung khong (chua bao
  loi) - ghi nhan de kiem tra neu Celery worker/Streamlit bao loi ket noi
  DB/Redis sau khi restart.
- 2026-07-03 (lan 8): **Thay doi song song ngoai phien lam viec nay** (rat co
  the tu Codex - xem quy uoc dung chung HANDOFF.md o dau file), phat hien qua
  `git log`/`git diff` khi dieu tra khieu nai "van con \\n trong .vi.json":
  - `subtitle_pipeline/export/formats.py`: them `_single_line_text()`, `to_json()`
    gio loai bo het `\n` (do `optimize_segments` chen vao de ngat dong hien
    thi) khoi truong `text` - **CHI anh huong file JSON**, cac dinh dang
    srt/vtt/ass/txt van giu `\n` de hien thi dung chuan phu de. Co test
    `test_to_json_removes_line_wrapping_newlines`.
  - `subtitle_pipeline/application/dub.py`: **BO HOAN TOAN buoc co-gian thoi
    luong (`time_stretch_to_duration`/ffmpeg `atempo`)** - xac nhan voi nguoi
    dung day la co y (atempo lam giong nghe do). Gio dung thang do dai raw
    cua clip TTS, dat vao dung `seg.start` tren timeline, KHONG ep khop
    `seg.end - seg.start` nua. **Danh doi moi (chua co giai phap)**: neu cau
    dich dai/ngan hon dang ke so voi khung thoi gian goc, cac cau lien tiep
    co the CHONG LAN (overlap) hoac lech xa dan ve sau trong video dai (tich
    luy drift, khong co co che bu tru). `infrastructure/audio_timing.py`
    (`time_stretch_to_duration`, `probe_duration_seconds`,
    `_clamp_atempo_factors`) van con trong code (khong bi xoa, van co test)
    nhung KHONG con duoc goi trong luong chinh - giu lai nhu 1 lua chon co
    the bat lai sau nay neu drift qua nang.
  - Da xac nhan file JSON cua job that tren may (`storage/b8be05de-.../`)
    khong con `\n`, va toan bo `pytest` (35 test) van pass voi code hien tai.
- 2026-07-03 (lan 9): **Sua bug nghiem trong - dich sot/sai vi ngon ngu nguon
  sai** (nguoi dung bao file `.vi.json` con nguyen nhieu doan tieng Anh chua
  dich). Root cause tim duoc qua doc code (khong phai NLLB "dich dom"):
  `PipelineConfig.language` (mac dinh `"vi"` tu `.env`) bi dung SAI muc dich
  lam ca ngon ngu align (`WhisperXAligner`) LAN ngon ngu nguon cho
  `NLLBTranslator`, bat ke video that su la tieng gi (vd. video mau la tieng
  Anh nhung bi bao NLLB "day la tieng Viet" - NLLB luc dich duoc luc khong).
  Whisper van auto-detect dung (vi `transcriber_faster_whisper.py` khong
  truyen `language=`) nhung ket qua detect (`info.language`) bi vut bo, khong
  truyen tiep cho Align/Translate. Da sua:
  - `domain/ports.py`: `Transcriber.transcribe()` tra ve
    `tuple[list[TranscriptSegment], str]` (them ngon ngu detect duoc).
  - `infrastructure/transcriber_faster_whisper.py`: tra ve kem `info.language`.
  - `application/pipeline.py`: `aligner_factory` doi thanh
    `Callable[[str], Aligner]` (dung sau khi biet ngon ngu that, khong dung
    sang lap luc `__post_init__` nhu truoc). Them try/except quanh buoc align
    - neu WhisperX khong co align model cho ngon ngu detect duoc (hoan toan
    co the xay ra voi auto-detect da ngon ngu) thi fallback dung thang
    timestamp segment-level tu Whisper thay vi lam crash ca job.
    `TranscriptionPipeline.run()` gio tra ve
    `tuple[list[SubtitleSegment], str]`.
  - `infrastructure/translator_nllb.py`: mo rong `NLLB_LANGUAGE_CODES` them
    12 ngon ngu NGUON pho bien (de/ru/it/pt/th/hi/id/nl/tr/pl/ar/uk).
    `SUPPORTED_LANGUAGES` (dropdown ngon ngu DICH o Upload/Editor) tach rieng
    thanh list co dinh `["vi","en","zh","ja","ko","fr","es"]`, khong con
    derive tu dict nguon (gio lon hon nhieu) nua - phai khop dung
    `EDGE_TTS_VOICES` trong `tts_edge.py`.
  - `app/jobs/tasks.py`: `process_video_job` dung `detected_language` that
    (khong phai `config.language`) cho `translate_and_export`; ghi ra file
    sidecar `{stem}.source_language.txt` de `translate_job`/`dub_job` (chay
    Celery task rieng, khong co bien nay san trong bo nho) doc lai dung qua
    helper `_read_source_language()` moi (fallback `config.language` cho job
    cu chua co file sidecar). Khoi translate+dub boc trong try/except rieng:
    neu NLLB rai `ValueError` (ngon ngu nguon hiem, chua co trong dict) thi
    KHONG lam FAILED ca job (transcribe da xong, phu de goc van dung duoc) -
    ghi `error_message` (Dashboard se hien canh bao) nhung `status` van
    `DONE`.
  - **Nguyen nhan phu gay "dich khong tu nhien"**: WhisperX chia segment o
    muc manh cau (vd. giua cau bi cat rieng), dich tung manh rieng le thieu
    ngu canh. Them file moi `application/sentence_merge.py`
    (`merge_into_sentences()` - ham thuan, gop cac segment lien tiep thanh 1
    cau hoan chinh dua vao dau cau ket thuc `. ! ? …`) va goi no trong
    `application/translate.py` TRUOC khi dua vao NLLB. **Chi ap dung cho
    nhanh dich** (khong dung toi phu de goc chua dich, tranh doi hanh vi
    phan dang chay dung). Loi ich phu: TTS cung it bi ngat quang hon vi moi
    cau hoan chinh chi tao 1 clip TTS thay vi nhieu clip roi cho tung manh.
  - Test moi: `tests/test_sentence_merge.py`. Cap nhat `tests/fakes.py`
    (`FakeTranscriber.transcribe()` tra tuple), `tests/test_pipeline.py`
    (aligner factory nhan `language`, unpack tuple tra ve). **40/40 test
    pass, `ruff check`/`ruff format` sach** (chay that tren may dev).
  - **Chua kiem chung tren job that** (can nguoi dung xoa job loi cu, upload
    lai video mau, xac nhan `.vi.json` moi khong con doan tieng Anh nao va
    cau dich muot hon).
- 2026-07-03 (lan 10, Claude Code ra soat cheo sau cac thay doi cua Codex):
  Dong bo lai tai lieu bi lech sau khi du an chuyen huong tool ca nhan +
  dubbing: README.md (bo "SaaS", mo ta pipeline moi co long tieng), HANDOFF
  muc 0 (bo buoc dien SESSION_SECRET_KEY da xoa), muc 1 (tool ca nhan +
  pipeline co TTS), roadmap 5b (edge-tts thay MMS-TTS). Sua 2 van de code
  that:
  - **Dong van de mo "load_dotenv() khong duoc goi trong app/" (nhat ky lan
    7):** them `load_dotenv()` vao `app/db/session.py`, `app/jobs/celery_app.py`,
    `app/config.py` - `.env` gio co tac dung that voi Streamlit/Celery ma
    khong can shell tu export bien.
  - **`DEFAULT_DATABASE_URL` (session.py) van tro port 5432** trong khi
    docker-compose/.env da chuyen sang 15432 (may dev co Postgres native
    chiem 5432) - neu .env khong duoc nap thi app am tham ket noi nham
    Postgres native. Da doi fallback sang 15432 khop docker-compose.
  - `check_env.py` kiem tra them package moi: transformers, edge_tts,
    soundfile.
  LUU Y: cac sua doi nay CHUA duoc chay ruff/pytest (phien nay chay trong
  sandbox khong co Python) - chay lai `pytest` + `ruff check` tren may dev
  truoc khi tin tuong.
- 2026-07-03 (lan 11): **Them lua chon nhieu giong doc** theo yeu cau nguoi
  dung. Da research danh sach giong edge-tts: tieng Viet chi co dung 2 giong
  thuan Viet (`vi-VN-HoaiMyNeural` nu - mac dinh, `vi-VN-NamMinhNeural` nam);
  bo sung them 9 giong "Multilingual" cua Azure (Ava/Emma/Seraphina/Vivienne/
  Xiaoxiao nu, Andrew/Brian/Remy/Florian nam - 1 giong doc duoc nhieu ngon
  ngu, bao gom tieng Viet, chat giong khac nhau) -> tieng Viet co tong cong
  11 lua chon giong. Nguoi dung xac nhan muon tieng Viet co NHIEU lua chon
  nhat co the - day da la toi da voi edge-tts (Microsoft chi phat hanh 2
  giong thuan Viet). Thay doi:
  - `tts_edge.py`: `EDGE_TTS_VOICES` (1 giong/ngon ngu) -> `VOICE_OPTIONS`
    (dict {nhan hien thi: ten giong} cho moi ngon ngu, giong dau tien la mac
    dinh) + ham `default_voice()`. Moi ngon ngu deu co giong ban dia nam/nu
    + 6 giong multilingual. `EdgeTTSSynthesizer(language, voice=None)`.
  - `dub.py` (`dub_and_export`), `tasks.py` (`process_video_job`/`dub_job`)
    nhan them tham so `voice` truyen xuyen suot.
  - `1_Upload.py` + `3_Editor.py`: them selectbox "Giong doc" (danh sach doi
    theo ngon ngu da chon).
  - Test moi: `tests/test_tts_voices.py` (tinh nhat quan VOICE_OPTIONS voi
    SUPPORTED_LANGUAGES, default, khong goi mang).
  CHUA chay thu: (1) ruff/pytest chua chay (sandbox khong Python), (2) chat
  luong THUC TE cua cac giong multilingual khi doc tieng Viet chua duoc nghe
  thu tren may that - can nguoi dung tao job voi tung giong de danh gia, neu
  giong nao doc tieng Viet te thi bao lai de loai khoi danh sach.
- 2026-07-03 (lan 12): **Them 2 che do xu ly tieng goc khi long tieng** theo
  yeu cau nguoi dung:
  - "Xoa tieng goc": thay audio hoan toan bang tieng dich (hanh vi cu, van
    la mac dinh).
  - "Giu tieng goc": tieng goc giam 70% (`volume=0.3`), tieng dich tron len
    tren - kieu thuyet minh/voice-over phim tai lieu, giu duoc nhac nen/hieu
    ung. Ky thuat: ffmpeg `filter_complex` voi `amix=inputs=2:normalize=0`
    (normalize=0 de amix khong tu chia doi am luong ca 2 track).
  Thay doi: `audio_mux.py` (tach `_build_mux_command()` thuan de test duoc
  khong can ffmpeg + hang so `KEEP_ORIGINAL_VOLUME=0.3`),
  `dub.py`/`tasks.py` truyen `keep_original_audio` xuyen suot, radio chon
  che do o `1_Upload.py` + `3_Editor.py`, test moi trong
  `tests/test_audio_mux.py`. **Han che da biet:** che do "giu tieng goc" yeu
  cau video goc PHAI co audio stream (video cam se loi ffmpeg - che do xoa
  tieng thi khong sao); tieng noi goc van nghe duoc mo mo duoi nen (dac thu
  voice-over, khong phai loi). Nang cap sau neu can: sidechain ducking
  (`sidechaincompress` - chi giam tieng goc DUNG LUC giong dich noi, nhung
  phuc tap hon nhieu). CHUA chay thu tren may that.
- 2026-07-03 (lan 13): **Nang cap UI/UX toan bo cac trang Streamlit** theo yeu
  cau nguoi dung ("giao dien qua don gian, can co quy trinh hon"):
  - `.streamlit/config.toml` MOI: theme mau rieng + `maxUploadSize=500` -
    **sua 1 bug tiem an co that**: Streamlit mac dinh chi cho upload 200MB
    trong khi app tu dat gioi han 500MB (nguoi dung upload file 200-500MB se
    bi Streamlit chan truoc khi code app kip kiem tra).
  - `app/ui.py` MOI: map `Job.stage` -> (phan tram, nhan tieng Viet) dung
    chung, de progress bar nhat quan giua cac trang.
  - `Home.py`: metric tong quan (tong/dang chay/hoan thanh/that bai) +
    page_link dieu huong + mo ta quy trinh 3 buoc.
  - `1_Upload.py`: bo cuc wizard 3 buoc (chon file -> tuy chon long tieng ->
    tao job); them **toggle tat long tieng** (chi tao phu de -
    `target_language=None`, kha nang von co san cua `process_video_job`
    nhung truoc do UI khong expose); hien ten/kich thuoc file truoc khi tao.
  - `2_Dashboard.py`: **tu lam moi moi 3s** bang `st.fragment(run_every=3)`
    (khong con nut "Lam moi" thu cong), progress bar theo stage (10 buoc),
    metric tong quan, loc theo trang thai (`st.segmented_control`), nut tai
    file xep cot.
  - `3_Editor.py`: chia 3 tab (Chinh sua phu de / Dich / Long tieng lai),
    tab chinh sua dat video canh bang phu de (2 cot).
  - `requirements.txt`: bump `streamlit>=1.41.0` (can cho fragment
    run_every/st.rerun scope/icon tren button/segmented_control).
  CHUA chay thu tren may that (sandbox khong co Python) - rui ro chinh: cac
  API Streamlit moi dung (fragment, segmented_control, icon) can dung phien
  ban >=1.41, neu venv tren may dev dang co ban cu hon thi phai
  `pip install -U streamlit` truoc khi chay lai.
- 2026-07-03 (lan 14): **Chuyen TOAN BO chuoi hien thi cho nguoi dung sang
  tieng Viet CO DAU** theo yeu cau nguoi dung (truoc do viet khong dau tu
  dau du an). Pham vi: 4 trang UI (`Home.py`, `1_Upload.py`, `2_Dashboard.py`,
  `3_Editor.py`), nhan stage/status (`app/ui.py`), nhan giong doc
  (`tts_edge.VOICE_OPTIONS`), thong bao loi hien tren Dashboard
  (`tasks.py` error_message, ValueError trong `translator_nllb.py`/
  `tts_edge.py`). Quy uoc moi ghi vao `docs/CODE_STYLE.md`: chuoi UI PHAI co
  dau; comment/docstring/tai lieu noi bo (HANDOFF.md, docs/) van giu khong
  dau. LUU Y: nhan giong doc trong VOICE_OPTIONS la KEY cua dict - doi nhan
  khong anh huong logic (test chi assert theo voice ID/values), da ra soat.
- 2026-07-03 (lan 10): **Them tinh nang gan giong doc rieng cho tung nguoi
  noi khi long tieng** (nguoi dung yeu cau, danh muc "1" trong 4 muc can
  nang cap duoc de xuat). Truoc do `dub_and_export()` dung CHUNG 1 giong cho
  ca video bat ke bao nhieu nguoi noi (`SubtitleSegment.speaker` tu
  diarization bi bo qua hoan toan o buoc long tieng). Da sua
  `subtitle_pipeline/application/dub.py`:
  - Ham thuan moi `_build_speaker_voice_map(segments, language, voice)` -
    nguoi noi xuat hien DAU TIEN dung dung `voice` nguoi dung chon (giu
    dung ky vong UI hien tai), cac nguoi noi tiep theo lan luot nhan 1
    giong KHAC trong `VOICE_OPTIONS[language]`, xoay vong neu nhieu nguoi
    noi hon so giong co san. Video khong co diarization (`speaker=None` het)
    van dung 1 giong duy nhat - khong doi hanh vi cu.
  - `dub_and_export()` doi tu 1 `EdgeTTSSynthesizer` duy nhat (`with ... as
    tts`) sang dung `contextlib.ExitStack` + dict cache 1 synthesizer/giong -
    tao moi khi gap giong chua dung, tai su dung khi gap lai. Vi
    `EdgeTTSSynthesizer.__enter__/__exit__` hien khong lam gi (khong co GPU
    state that), doi nay an toan; ExitStack giup neu sau nay doi sang TTS
    backend co state that (vd. VieNeu-TTS, xem tts_edge.py) van dong dung
    properly.
  - `sample_rate` gio lay truc tiep tu hang so `OUTPUT_SAMPLE_RATE` trong
    `tts_edge.py` thay vi doc tu 1 instance `tts.sample_rate` - tranh loi
    edge case segments rong (truoc day set sau vong lap trong 1 `with` duy
    nhat, gio co nhieu synthesizer nen khong con 1 diem "sau vong lap" ro
    rang).
  - Them help text o `1_Upload.py`/`3_Editor.py` giai thich giong chon la
    cho "nguoi noi dau tien", cac nguoi khac tu dong nhan giong khac.
  - Test moi trong `tests/test_dub.py`: 5 test cho
    `_build_speaker_voice_map` (don nguoi noi, nhieu nguoi noi, tai su dung
    khi lap lai, xoay vong khi vuot so giong co san, dung `default_voice()`
    khi khong chon) + 1 test tich hop xac nhan `dub_and_export` tao dung so
    synthesizer/giong. **55/55 test pass, ruff sach.**
  - **Chua kiem chung tren video that nhieu nguoi noi** (can video co it
    nhat 2 speaker qua diarization, tuc can `HF_TOKEN` hop le va video co
    doi thoai that).
- 2026-07-03 (lan 11): **Nang cap lon - wizard "Tao video" 6 buoc kieu
  VietDub** theo yeu cau nguoi dung (dua screenshot lam tham chieu). Xem
  chi tiet day du o muc 6j moi. Tom tat: (1) Nguon: dan URL
  YouTube/Douyin (yt-dlp, stage "download" trong worker,
  `JobRepository.update_source`), che do chay thu 60/120s dau
  (`trim_media`), ep cung ngon ngu nguon; (2) Giong doc:
  `voice_catalog()` co gender/style/recommended, slider toc do/cao do
  (edge-tts rate/pitch), nut nghe thu (`synthesize_sample`); (3) Dich:
  bang thuat ngu (`application/glossary.py` mask/restore), preset trinh
  bay map sang tham so optimize; (4) Phu de: `SubtitleStyle` dataclass +
  `to_ass(style)`, hardsub (`burn_subtitles`, luu y cwd tren Windows),
  preview HTML; (5) Am thanh & Xuat: slider am luong goc/giong (bo radio
  keep_original cu), ducking sidechaincompress, mp4/mkv + CRF preset; (6)
  Xem lai: the tom tat + `job_config.json` + nut "Tao lai voi cau hinh
  nay" o Dashboard. `process_video_job` doi sang nhan dict `options`;
  `dub_and_export` nhan `DubRenderOptions`. Them dep `yt-dlp`. **76/76
  test pass, ruff sach; CHUA chay thu end-to-end qua UI** (xem checklist
  muc 6j). GIOI HAN trung thuc: "dich theo ngu canh" that su can LLM -
  chua lam, da ghi ro o UI + muc 6j.
- 2026-07-04: **Chuyen UI tu Streamlit sang React + FastAPI** (nguoi dung:
  "Streamlit khong phu hop lam UI chuyen nghiep") - DAO NGUOC 2 quyet dinh
  cu (Streamlit-only, khong-Auth). Xem chi tiet muc 6k moi. Tom tat:
  `backend/` FastAPI (JWT + bcrypt, admin = tai khoan chung tu env, khong
  gioi han usage theo yeu cau), `frontend/` Vite+React+TS+Tailwind (landing
  page, login/register, Studio + wizard 6 buoc stepper that, job detail voi
  video player, trang admin). Them lai `User`/`Job.user_id` (nullable,
  migration ALTER tu dong luc startup - KHONG can reset DB). Lỗi pipeline/
  Celery/options schema giu NGUYEN 100%. Streamlit pages giu lam legacy.
  91/91 pytest + ruff sach + `npm run build` pass + smoke test that tren
  Postgres OK. CHUA test E2E qua UI React (checklist muc 6k).
- 2026-07-04 (cung ngay, lan 2): **Xoa hoan toan Streamlit** theo yeu cau
  nguoi dung (khong con giu legacy nhu du dinh) - xem chi tiet muc 6k "Cap
  nhat 2026-07-04". Xoa `app/pages/`, `app/Home.py`, `app/ui.py`,
  `.streamlit/`; bo dependency `streamlit`/`pandas`; don `pyproject.toml`
  (bo E402 ignore da het can); them job `frontend-build` vao CI. Cap nhat
  docstring `app/jobs/tasks.py`/`repository.py`/`stages.py` (khong con nhac
  Streamlit). README.md them huong dan chay 4 tien trinh (docker compose +
  celery + uvicorn + npm run dev). 91/91 pytest + ruff sach sau khi xoa.
- 2026-07-05: **Them tu dong lay cookie YouTube/Douyin bang Playwright**
  (nguoi dung: "tim phuong thuc manh hon tien hon" thay vi export cookie tay
  qua extension). Xem chi tiet muc 6l. File moi
  `subtitle_pipeline/infrastructure/cookie_refresh.py` (2 che do:
  `setup_login_session` mo trinh duyet that dang nhap 1 lan, `refresh_cookies`
  chay an tai su dung session da luu), endpoint
  `POST /api/admin/refresh-cookies`, nut "Lam moi cookie" trong trang Admin.
  Them dependency `playwright`. **Phat hien quan trong qua doc source code
  yt-dlp**: Douyin hien KHONG THE tai duoc du co cookie moi vi chinh yt-dlp
  chua code xong buoc "verification challenge" (con la TODO trong code cua
  ho) - da xac nhan bang thu nghiem that (44 cookie that van loi y het).
  YouTube khong bi gioi han nay nen giai phap Playwright van huu ich day du.
  107/107 pytest pass (them `test_cookie_refresh.py` + 3 test backend moi),
  ruff sach, `npm run build` pass, da chay Playwright+Chromium THAT tren may
  (khong gia lap) de xac nhan dinh dang cookies.txt sinh ra dung.
- 2026-07-05 (cung ngay, lan 2): **BO HOAN TOAN tinh nang tai video tu URL
  (YouTube/Douyin/TikTok...)** theo yeu cau nguoi dung ("bỏ luôn các chức
  năng liên quan tới đưa link YOUTUBE và douyin để tải về đi, chỉ cho phép
  upload thôi"). Xoa sach ca phan "Buoc 1 - Nguon" (muc 6j) lan tinh nang
  cookie refresh vua them cung ngay (muc 6l) vi ca 2 chi ton tai de phuc vu
  download URL:
  - Xoa file: `subtitle_pipeline/infrastructure/downloader_ytdlp.py`,
    `subtitle_pipeline/infrastructure/cookie_refresh.py`,
    `tests/test_downloader.py`, `tests/test_cookie_refresh.py`.
  - `app/jobs/tasks.py`: `_resolve_input()` bo nhanh tai URL (`download_video`),
    chi con logic cat ngan (trim) khi test doan ngan. `process_video_job` bo
    stage "download".
  - `app/jobs/stages.py`: bo entry `("download", "Tải video từ URL")` khoi
    `PIPELINE_STAGES` (con 10 buoc thay vi 11).
  - `app/jobs/repository.py`: xoa `JobRepository.update_source()` (chi dung
    de cap nhat filename/input_path THAT sau khi tai URL xong).
  - `backend/routers/jobs.py`: `_create_job_from_options()`/`rerun_job()` bo
    nhanh `source.url` - gio BAT BUOC phai co file upload, khong co file thi
    tra loi 400.
  - `backend/routers/admin.py`: xoa endpoint `POST /admin/refresh-cookies`.
  - `requirements.txt`: bo `yt-dlp`, `playwright`. `.env.example`: bo
    `YTDLP_COOKIES_FILE`/`YTDLP_COOKIES_FROM_BROWSER`.
  - `frontend/src/pages/NewJob.tsx` (Buoc 1 cua wizard): bo toggle "Dán
    URL"/"Tải video lên" - gio CHI hien input chon file. Bo state `useUrl`,
    `sourceValid` gio chi phu thuoc `file`.
  - `frontend/src/lib/types.ts`: bo `url`/`quality` khoi `JobOptions.source`.
  - `frontend/src/lib/constants.ts`: xoa `QUALITY_CHOICES`, bo entry
    `download` khoi `PIPELINE_STEPS` (con 10 buoc).
  - `frontend/src/pages/Admin.tsx`: xoa section "Cookie tải video" + nut "Làm
    mới cookie".
  - `frontend/src/pages/Landing.tsx`: sua copy quang cao (bo nhac "Dán link
    là xong"/"video YouTube, Douyin") thanh mo ta upload-only.
  - Test: xoa 2 test lien quan URL/cookie trong `tests/test_backend_api.py`
    (`test_create_url_job_without_file`, `test_refresh_cookies_*`), doi ten
    `test_create_job_without_file_or_url_rejected` ->
    `test_create_job_without_file_rejected`; xoa
    `test_update_source_changes_filename_and_input_path` trong
    `tests/test_job_repository.py`.
  Xac nhan **86/86 pytest pass, ruff sach, `npm run build` pass** (tsc + vite)
  sau khi xoa. Tinh nang trim/kiem thu doan ngan va ep ngon ngu nguon o Buoc 1
  KHONG bi anh huong (van dung cho ca video upload).
- 2026-07-05 (cung ngay, lan 3): **Vi tri phu de tu do (keo tha) + doi "Mau
  vien" thanh "Mau nen"** o Buoc 4 wizard (theo yeu cau nguoi dung). Truoc do
  vi tri chi co 3 nut co dinh (Duoi/Giua/Tren, canh giua ngang) va o mau chi
  chinh duoc mau vien chu (khong chinh duoc mau hop nen). Thay doi:
  - `subtitle_pipeline/export/formats.py`: `SubtitleStyle` bo field
    `position` (enum) va `outline_color`, them `position_x`/`position_y`
    (% 0..100, mac dinh 50/90 ~ tuong duong "Duoi" cu) va `background_color`
    (mac dinh `#000000`, giu nguyen hanh vi cu). `to_ass()` gio ghi de vi tri
    tung dong bang override tag `{\an5\pos(x,y)}` (x,y quy doi tu % sang
    pixel theo `PlayResX=1920`/`PlayResY=1080`) thay vi dua vao
    Alignment/MarginV o Style header; mau vien chu co dinh den (khong con
    tuy chinh duoc). Header Style mac dinh GIU NGUYEN dung y het truoc do
    (test khoa `test_to_ass_default_style_matches_legacy_header` van pass
    khong sua) vi Alignment/Margin trong header van la gia tri cu, chi khong
    con anh huong render (bi `\pos()` de len).
  - `frontend/src/pages/NewJob.tsx` Buoc 4: bo 3 nut vi tri, thay bang khung
    xem truoc co the KEO THA truc tiep dong chu mau (pointer events, tinh %
    theo vi tri con tro so voi khung). O mau "Mau vien" doi thanh "Mau nen"
    (`background_color`, chi hien ro khi bat "Hop nen dac sau chu").
  - `frontend/src/lib/types.ts`/`constants.ts`: `JobOptions.subtitle.style`
    doi field tuong ung; xoa `POSITION_CHOICES` (khong con dung).
  - `tests/test_export_formats.py`: doi
    `test_to_ass_custom_style_changes_alignment_box_and_colors` thanh
    `test_to_ass_custom_style_changes_box_and_colors` (kiem tra BackColour
    tuy chinh thay vi Alignment) + test moi
    `test_to_ass_custom_position_emits_pos_override_tag`.
  87/87 pytest pass, ruff sach, `npm run build` pass. **Chua render thu video
  hardsub that** de xac nhan `\pos()` hien dung vi tri da keo tren video xuat
  ra (chi xac nhan qua unit test chuoi ASS sinh ra dung).
- 2026-07-05 (cung ngay, lan 4): **Them bang phat am rieng cho giong doc long
  tieng** (khac bang thuat ngu dich hien co) - xem chi tiet muc 6m. Tom tat:
  file JSON mac dinh `subtitle_pipeline/infrastructure/pronunciation_glossary.json`
  (seed `"vi": {"SQL": "ét quy eo"}`) + textarea moi o Buoc 3 wizard (uu tien
  hon JSON neu trung tu) + module `subtitle_pipeline/application/
  pronunciation.py` ap dung ngay truoc buoc TTS trong `dub.py` - CHI doi
  audio, khong dung phu de xuat ra. Cung luc them 1 dong thong tin o dau
  Buoc 3 hien ro dang dich/long tieng sang ngon ngu nao (doc tu Buoc 2) vi
  nguoi dung nhan xet Buoc 3 khong co cho chon ngon ngu (thuc ra nam o Buoc
  2, chi thieu hien thi lai). 94/94 pytest pass, ruff sach, `npm run build`
  pass. **Chua nghe thu that voi edge-tts** de xac nhan phat am "ét quy eo"
  nghe tu nhien hon "SQL" nguyen ban.
- 2026-07-05 (cung ngay, lan 5): **Khoa tuan tu cac buoc wizard "Tao video"**
  theo yeu cau nguoi dung ("phai xong tung buoc roi moi cho phep qua buoc
  moi... co the quay lai va luu cac cai da chinh chu khong mat di"). Truoc do
  sidebar cho bam thang toi bat ky buoc nao (kem "Tiep tuc" khong kiem tra
  gi), du chua chon file o Buoc 1. `frontend/src/pages/NewJob.tsx`:
  - State moi `maxStepReached` (buoc xa nhat da tung mo khoa, khoi tao 0).
    Nut "Tiep tuc" chi bat khi `canAdvanceFromStep(step)` dung (hien chi
    Buoc 1 co dieu kien that: phai chon file - cac buoc sau deu co gia tri
    mac dinh hop le nen luon qua duoc), va khi bam thi nang
    `maxStepReached` len `step + 1`.
  - Nut sidebar cho tung buoc: disable (kem icon khoa 🔒 + tooltip) neu
    `i > maxStepReached`. Di LUI (bam sidebar buoc nho hon, hoac nut "Quay
    lai") luon duoc phep vi `i <= maxStepReached` da dung; du lieu nguoi
    dung nhap o `options`/`file` KHONG bi xoa khi chuyen qua lai giua cac
    buoc (chi bi xoa khi tu bam "Dat lai buoc nay"/"Dat lai tat ca").
  - "Dat lai buoc nay" tren Buoc 1 (xoa file) va "Dat lai tat ca" (Buoc 6)
    deu dua `maxStepReached` ve 0 (khoa lai cac buoc sau, dung vi nguon
    khong con hop le) - rieng "Dat lai tat ca" chuyen luon ve Buoc 1 de
    tranh ket lai o Buoc 6 (`step` cu) trong khi sidebar da khoa het cac
    buoc trung gian.
  `npm run build` pass (tsc + vite). Khong dong Python, khong can chay lai
  pytest.
- 2026-07-05 (cung ngay, lan 6): **Phat hien tinh nang tai video tu link da
  duoc Codex viet lai** (song song, khong biet quyet dinh xoa truoc do cua
  nguoi dung) - nguoi dung xac nhan MUON GIU ban moi. Xem chi tiet muc 6j.
  Tom tat: xac nhan ban CU (cookie/Playwright) da xoa sach khong lan voi ban
  moi; sua bug parity `PIPELINE_STEPS` (frontend) thieu stage "download" so
  voi backend gay hien sai ten buoc tren thanh tien do; sua 1 test cua chinh
  minh (`test_pronunciation.py`) bi fail vi phu thuoc noi dung file JSON
  nguoi dung tu sua. 96/96 pytest pass, `npm run build` pass.
- 2026-07-05 (cung ngay, lan 7): **Them chi bao loading (spinner/skeleton)
  cho toan bo thao tac trong UI React** theo yeu cau nguoi dung ("làm tăng
  trải nghiệm người dùng qua các thanh load với tất cả thao tác"). Truoc do
  cac nut bam mutation (dang nhap, dang ky, tao job, xoa/tao lai job, xoa
  user, nghe thu giong, phan tich link) chi doi CHU (vd. "Dang tai...")
  khong doi mau/icon, mot so noi (bang Admin) khong co bat ky dau hieu dang
  tai nao. Them:
  - `frontend/src/components/Spinner.tsx` - icon SVG xoay (dung class
    Tailwind `animate-spin` co san), tai su dung moi noi.
  - `frontend/src/components/GlobalLoadingBar.tsx` - thanh mong co dinh o
    dau trang, TU DONG hien khi co BAT KY mutation nao dang chay
    (`useIsMutating()`) HOAC lan fetch DAU TIEN cua 1 trang
    (`useIsFetching({ predicate: query => query.state.data === undefined })`)
    - dung predicate thay vi `useIsFetching()` tho de KHONG nhap nhay moi
    lan cac trang co `refetchInterval` (Studio/JobDetail/Admin) tu poll
    ngam o nen. Mount 1 lan duy nhat trong `App.tsx` nen ap dung cho TOAN BO
    trang khong can sua tung noi.
  - Them animation `loading-bar` (keyframe truot ngang, kieu thanh loading
    cua GitHub/YouTube) vao `tailwind.config.js`.
  - Gan `<Spinner />` canh chu vao TAT CA nut mutation: Login/Register submit,
    NewJob (phan tich link, nghe thu giong, tao job), Studio (tung job rieng
    biet dung `mutation.variables === job.id` de chi hien spinner dung
    hang dang xu ly, khong phai ca danh sach), Admin (xoa user, cung ky
    thuat `variables` per-row), JobDetail (chon noi luu video).
  - Cai thien trang thai loading LAN DAU cua trang: Studio (skeleton
    card `animate-pulse` thay vi chu "Dang tai..."), Admin (spinner + chu
    trong bang users/jobs, truoc do KHONG co gi ca), JobDetail (spinner canh
    chu), NewJob (spinner khi dang tai danh sach giong doc).
  **Chua kiem tra bang mat trong trinh duyet that** (sandbox khong co
  Postgres/Redis/Celery de dang nhap va kich hoat cac mutation that) - chi
  xac nhan `npm run build` (tsc + vite) sach va da chay thu `vite dev` xac
  nhan trang khoi dong khong loi runtime ngay lap tuc. Can nguoi dung tu mo
  UI that de xem GlobalLoadingBar/skeleton hien dung nhu mong doi, dac biet
  kiem tra KHONG bi nhap nhay do polling.
- 2026-07-05 (cung ngay, lan 8): **Don dep code du thua/chua toi uu toan repo**
  theo yeu cau nguoi dung. Da chay `ruff check .`/`ruff format .` tren TOAN
  BO repo (truoc gio moi chi chay tren file vua sua trong tung phien) va sua
  het 13 loi con sot lai:
  - I001 (import chua sort) o `phase1_feasibility/step01/02/03/04/05.py` +
    `subtitle_pipeline/infrastructure/downloader_ytdlp.py` - auto-fix.
  - SIM117 (gop `with` long nhau) o 4 script `phase1_feasibility/step02/04/
    05/06` - gop thanh 1 `with (A, B as b):` (Python 3.10+ parenthesized
    context managers), khong doi hanh vi.
  - SIM105 (`try/except OSError: pass` -> `contextlib.suppress(OSError)`)
    o `app/jobs/tasks.py::_cleanup_downloaded_input` va
    `subtitle_pipeline/infrastructure/downloader_ytdlp.py::_cleanup_download_temps`.
  - **Phat hien + sua 1 BUG THAT (khong chi loi lint):**
    `phase1_feasibility/step04_transcribe.py` goi
    `transcriber.transcribe()` va coi ket qua la thang list segment, nhung
    `FasterWhisperTranscriber.transcribe()` da doi sang tra ve
    `tuple[list[TranscriptSegment], str]` (kem ngon ngu detect duoc) tu lan
    sua bug dich sai ngon ngu nguon (xem muc 9, "2026-07-03 lan 9") - script
    nay chua tung duoc cap nhat theo, se crash ngay o `asdict()` neu chay
    (asdict() tren 1 list/string thay vi dataclass). Da sua: unpack dung
    `segments, detected_language = transcriber.transcribe(...)`, in them
    ngon ngu detect duoc ra console.
  - **Rut gon 1 cho code lap:** `backend/routers/jobs.py` co 2 noi ghi
    `job_config.json` giong het nhau (`_create_job_from_options` va
    `rerun_job`) - gop thanh ham dung chung `_write_job_config(job_dir,
    options)`.
  - Da ra soat them (khong sua vi khong phai "du thua" ma la thieu sot CO
    CHU DICH, da ghi ro trong HANDOFF tu truoc): `app/storage.py`
    (`Storage`/`LocalStorage`/`S3Storage`) CHI duoc dung boi
    `tests/test_storage.py`, chua duoc noi vao Upload/Celery task nao - day
    la Phase 8 "chua lam" tu lau (xem muc 4/8), KHONG xoa vi la placeholder
    co y cho tinh nang S3 sau nay, chi ghi nhan lai o day de nguoi dung
    biet van con ton tai.
  - Kiem tra frontend: `tsconfig.app.json` da bat san
    `noUnusedLocals`/`noUnusedParameters` (strict) nen KHONG co import/bien
    thua nao (xac nhan qua `npm run build` sach) - khong co ESLint rieng
    trong repo nay.
  Xac nhan **96/96 pytest pass, `ruff check`/`ruff format --check` sach
  toan repo, `npm run build` pass** sau khi don dep.
- 2026-07-05 (cung ngay, lan 9): **Them tinh nang gui email khi job hoan
  thanh** theo yeu cau nguoi dung ("2 chuc nang la tai ve hoac gui ve mail o
  buoc cuoi"). Da hoi lai nguoi dung 2 quyet dinh truoc khi code:
  - **Chi gui LINK toi trang chi tiet job, KHONG dinh kem video** - video
    long tieng thuong vuot gioi han dinh kem cua hau het nha cung cap email
    (vd. Gmail ~25MB), de bi bounce/vao spam.
  - **Dung Gmail SMTP + App Password** (khong phai dich vu transactional
    email rieng) - phu hop tool ca nhan, khong can dang ky them tai khoan.
  Kien truc:
  - `backend/email_sender.py` (module moi) - dung `smtplib` chuan cua
    Python (KHONG them dependency moi vao requirements.txt).
    `send_job_result_email(to_email, job_id, filename)` gui email chua link
    `{FRONTEND_URL}/studio/jobs/{job_id}` toi email DA DANG KY tai khoan
    (`AuthUser.email` co san trong `backend/security.py`, khong can hoi lai
    nguoi dung). Link KHONG chua token (khac `fileUrl()` dung cho
    `<video src>`) - nguoi nhan phai dang nhap lai de xem, an toan hon neu
    email bi forward/leak. Rai `EmailNotConfiguredError` neu chua dien
    `SMTP_USER`/`SMTP_PASSWORD` trong `.env`.
  - `backend/routers/jobs.py`: them `POST /jobs/{id}/send-email` (chi cho
    phep khi `job.status == JobStatus.DONE`, dung lai `_get_owned_job` de
    kiem tra quyen so huu) - tra 400 neu job chua xong, 503 neu SMTP chua
    cau hinh, 502 neu gui that bai (loi mang/dang nhap SMTP sai).
  - `.env.example`: them `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/
    `SMTP_PASSWORD`/`SMTP_FROM_NAME` + `FRONTEND_URL` (dung de dung link
    trong email) kem huong dan tao Gmail App Password.
  - `frontend/src/pages/JobDetail.tsx`: them nut "Gui ve email" canh "Chon
    noi luu"/"Tai video" trong the "Clip ket qua", dung `useMutation` + hien
    `<Spinner>` luc dang gui (nhat quan voi cac nut mutation khac da them o
    lan sua truoc), hien thong bao thanh cong/loi ngay duoi.
  - Test moi: `tests/test_email_sender.py` (mock `smtplib.SMTP_SSL`, xac
    nhan gui dung link + KHONG dinh kem file, rai loi khi chua cau hinh) +
    3 test trong `tests/test_backend_api.py` (tu choi khi job chua DONE,
    gui dung email da dang ky, tra 502 khi SMTP loi).
  **Chua gui thu email that** (sandbox khong the ket noi SMTP that ra
  ngoai) - nguoi dung can tu dien `SMTP_USER`/`SMTP_PASSWORD` (Gmail App
  Password) vao `.env` roi bam thu nut "Gui ve email" tren 1 job DONE that
  de xac nhan nhan duoc mail + link mo dung trang job. Xac nhan **101/101
  pytest pass, ruff sach, `npm run build` pass**.
- 2026-07-05 (cung ngay, lan 10): **Khoi phuc co che Playwright tu dong lay
  cookie YouTube** (da bi xoa truoc do cung ngay) sau khi nguoi dung bao
  gap lai loi that "Sign in to confirm you're not a bot" tren tinh nang tai
  video tu link ban Codex viet lai (khong co cookie). Nguoi dung dua repo
  tham khao github.com/DauDinhQuangAnh/Youtube_link - da clone ve doc source
  that, xac nhan repo do **cung KHONG xu ly duoc van de nay** (README ghi ro
  "intentionally does not include anti-bot circumvention"), nen khong dung
  de "hoc theo" duoc ma phai tu khoi phuc co che cookie cua chinh du an.
  Xem chi tiet muc 6l "Cap nhat 2026-07-05 (khoi phuc)". Tom tat: khoi phuc
  `subtitle_pipeline/infrastructure/cookie_refresh.py` (tu git history, bo
  Douyin khoi scope) + noi vao `downloader_ytdlp.py` qua ham moi
  `_cookie_options()` (ca `analyze_video()` va `download_video()`) + nhan
  dien loi bot-check trong `friendly_yt_dlp_error()` + khoi phuc endpoint
  `POST /admin/refresh-cookies` va nut "Làm mới cookie" trong Admin.tsx +
  them lai dependency `playwright` va bien env `YTDLP_COOKIES_FILE`. Them
  moi `tests/test_downloader.py` (module nay truoc gio chua co test nao).
  114/114 pytest pass, ruff sach, `npm run build` pass. **Chua chay
  `--setup`/`--refresh` voi Chromium that** - nguoi dung can tu
  `pip install -r requirements.txt`, `python -m playwright install
  chromium`, roi `python -m subtitle_pipeline.infrastructure.cookie_refresh
  --setup` va thu tai lai video tung bi chan de xac nhan het loi.
- 2026-07-07: **Sua trai nghiem gay hieu lam trong `cookie_refresh.py`**:
  nguoi dung chay `--refresh` TRUOC `--setup` (chua tung dang nhap) - lenh
  chay AN (headless, dung thiet ke) nen KHONG co cua so nao hien ra, tuong
  nhu bi treo nen nguoi dung tu nhan Ctrl+C (`KeyboardInterrupt`, khong phai
  loi code that). `refresh_cookies()` gio kiem tra `profile_dir` (tao boi
  `--setup`) co ton tai truoc khi chay - neu chua co, rai `RuntimeError` ro
  rang ngay lap tuc (huong dan chay `--setup` truoc) thay vi im lang chay
  tiep va lay cookie AN DANH (truoc day se "thanh cong" gia, khong bao loi
  gi ca du chua he dang nhap). Them 1 dong in "Dang mo trinh duyet an de
  lay cookie moi..." truoc khi bat dau de nguoi dung biet lenh dang chay,
  khong phai dung im. 114/114 pytest pass, ruff sach.
- 2026-07-07: **Ra soat tinh nang Telegram bot** (viet boi nguoi dung/Codex,
  khong phai Claude Code) theo yeu cau "kiểm tra coi code có đang ổn không".
  Xem chi tiet muc 6n. Tom tat: kien truc tach luong dung nhu mo ta (job
  Telegram di qua `app/jobs/service.py`, khong dung backend API), sua 1 loi
  ro ri ket noi DB thuc su (`create_download_job()` tao engine/pool moi moi
  lan goi thay vi dung chung session factory singleton), dep 1 doan
  dead-code kho doc trong `bot.py`, sua 3 loi ruff E501. Nguoi dung xac
  nhan viec doi `ADMIN_EMAIL`/`ADMIN_PASSWORD` mau trong `.env.example`
  thanh `admin`/`admin` la CO Y (khong phai sot lai), giu nguyen. 116/116
  pytest pass, ruff sach sau khi sua.
- 2026-07-13: **Ra soat toan du an theo yeu cau nguoi dung ("kiem tra da hoan
  thien phan nao va thieu sot phan nao")** - phien nay chay THAT tren may dev
  (RTX 4050, khong phai sandbox - xac nhan qua `nvidia-smi`), khong chi doc
  HANDOFF ma con chay lai kiem tra thuc te:
  - `pytest` 116/116 pass, `ruff check .` + `ruff format --check .` sach,
    `cd frontend && npm run build` pass - tat ca chay THAT, khong chi doc code.
  - `check_env.py` PASS toan bo lan dau tien (xem chi tiet muc 8) - moi truong
    AI (torch/CUDA/faster_whisper/whisperx/pyannote/deepfilternet/
    transformers/edge_tts) da san sang tren may nay.
  - Xac nhan qua git log: khong co commit nao sau `7ac8d43` (2026-07-07,
    Telegram bot) - HANDOFF dang khop 100% voi lich su git, khong bi lech.
  - Phat hien cac khoang trong CHUA tung duoc chay end-to-end that:
    `phase1_feasibility/samples/` rong (chua co video mau), thu muc `results/`
    chua ton tai (`run_all.py` chua chay lan nao), `storage/` chi co
    `browser_profile/` (khong co job nao tung chay xong qua web pipeline).
    Docker Desktop dang KHONG chay (`docker ps` loi "cannot connect to
    dockerDesktopLinuxEngine") nen Postgres/Redis chua san sang de test
    Phase 3 tro len ngay luc ra soat.
  - Doi chieu `.env` thuc te voi `.env.example`: da dien `HF_TOKEN`,
    `DATABASE_URL` (port 15432 dung), `ADMIN_EMAIL`/`ADMIN_PASSWORD`,
    `YTDLP_COOKIES_FILE`. **CON THIEU hoan toan** (rong, chua co dong nao
    trong `.env`): `SMTP_*`/`FRONTEND_URL` (tinh nang gui email job xong -
    code xong tu 2026-07-05 nhung chua the dung vi chua cau hinh SMTP),
    `TELEGRAM_*`/`BACKEND_PUBLIC_URL`/`PUBLIC_LINK_*` (bot Telegram - code
    xong + ra soat 2026-07-07 nhung chua chay voi token that vi chua dien).
  Khong sua code gi trong phien nay (chi ra soat + cap nhat tai lieu). Xem
  cau tra loi day du gui nguoi dung de biet danh sach hoan thien/thieu sot
  chi tiet theo tung phase.
- 2026-07-13 (lan 2): **Don dep 2 khoang du thua theo yeu cau nguoi dung**
  ("streamlit là phần cũ cần phải được clean bỏ, s3 storage đi ko cần đâu
  clean phần đó luôn"):
  - Xac nhan Streamlit CODE da duoc xoa sach tu 2026-07-04 (khong con file
    `app/pages/`, `app/Home.py`, `app/ui.py`, `.streamlit/` nao) - chi con sot
    2 dong DEAD trong `start_project.ps1`/`stop_project.ps1`
    (pattern `"streamlit run app/Home.py"` trong `Stop-DevProcesses`, dung de
    tim tien trinh Streamlit cu con chay de kill - khong con tac dung vi
    script do khong con ton tai). Da xoa 2 dong nay.
  - Xoa hoan toan S3 storage abstraction (xem chi tiet muc 6h "Cap nhat
    2026-07-13"): `app/storage.py`, `tests/test_storage.py`, dependency
    `boto3`, bien env `STORAGE_BACKEND`/`S3_BUCKET`/`S3_PREFIX` (ca `.env` va
    `.env.example`). Xac nhan module nay chua tung duoc goi o dau khac ngoai
    test cua chinh no truoc khi xoa (grep toan repo).
  113/113 pytest pass (116 - 3 test cua `test_storage.py` da xoa), `ruff
  check`/`ruff format --check` sach.
- 2026-07-13 (lan 3): **Viet lai `README.md`** theo yeu cau nguoi dung ("trang
  tri readme dep vao") - them badge CI/Python/React, so do pipeline dang
  Mermaid, bang cong nghe su dung, danh sach tinh nang co emoji, giu nguyen
  noi dung ky thuat (khong bia them tinh nang chua co). Khong dong code, chi
  doi 1 file markdown.
- 2026-07-14: **Dep `__pycache__`/`.pytest_cache`/`.ruff_cache`** theo yeu
  cau nguoi dung ("nhe source") - xac nhan qua `git ls-files` khong file nao
  bi track (deu la cache tu sinh), xoa 14 thu muc, khong dong test that nao.
- 2026-07-14 (lan 2): **Lam lai trang "Sua phu de" (Editor) trong UI React**
  - nguoi dung hoi huong phat trien tiep, chon tinh nang nay trong 4 lua
  chon de xuat. Xem chi tiet muc 6o. Tom tat: 5 route moi trong
  `backend/routers/jobs.py` (GET/PUT `/subtitles/{language}`, POST
  `/translate`, POST `/dub`, GET `/original`), trang moi
  `frontend/src/pages/Editor.tsx` (3 tab: Chinh sua phu de/Dich/Long tieng
  lai, route `/studio/jobs/:id/edit`), nut "Sua phu de" moi trong
  `JobDetail.tsx`. **Phat hien quan trong ve moi truong:** sandbox phien nay
  CO Python that (`D:\hoctap\python\python.exe`, khac mo ta cu trong
  HANDOFF/CLAUDE.md ve sandbox khong Python) - da chay THAT `pytest` (121/121
  pass, them 8 test moi trong `tests/test_backend_api.py`), `ruff check`
  sach, `ruff format --check` (phat hien + sua 1 file `app/jobs/stages.py`
  chua dung format tu truoc, khong lien quan thay doi lan nay), va
  `npm run build` (tsc + vite) pass that qua Node/npm co san. **Chua tu tay
  test qua trinh duyet that** (can Docker Postgres/Redis/Celery worker dang
  chay) - xem checklist muc 6o.
- 2026-07-14 (lan 3): **Them tinh nang clone giong long tieng (VieNeu-TTS)**
  - nguoi dung de xuat "khu clone giong: đọc 1 đoạn, xử lý thành âm thanh
  được chọn khi lồng tiếng", yeu cau nghien cuu cong nghe + flow truoc, roi
  xac nhan "build luôn đi". Xem chi tiet muc 6p. Da **SPIKE THAT** (khac
  thong le "viet roi cho nguoi dung tu chay thu"): cai `vieneu` that, tai
  model that tu HuggingFace (sua 2 loi thuc te gap phai: 401 qua "Xet" ->
  `HF_HUB_DISABLE_XET=1`; thieu `torchaudio` -> cai them), clone giong tu 1
  clip edge-tts sinh ra, xac nhan audio dau ra hop le qua `soundfile`. Tom
  tat code: adapter moi `subtitle_pipeline/infrastructure/tts_vieneu.py`
  (`VieNeuCloneSynthesizer`), `DubRenderOptions.custom_voice_ref_audio`
  moi trong `dub.py` (1 giong clone duy nhat cho ca video, khong xoay vong
  nhu edge-tts), model DB moi `CustomVoice` + `app/voices/repository.py` +
  router moi `backend/routers/voices.py` (`/api/voices` CRUD, kiem tra chu
  so huu), trang moi `frontend/src/pages/Voices.tsx` (ghi am qua
  `MediaRecorder` + doan van mau, hoac tai file) noi vao NavBar/route
  `/voices`, wizard NewJob + Editor deu them lua chon "Giong da clone".
  **131/131 pytest pass (them 12 test moi), ruff sach, `npm run build`
  pass.** Toc do CPU trong spike ~8x cham hon thoi gian thuc (khong dung
  duoc that) - ky vong nhanh hon nhieu tren GPU CUDA that (RTX 4050, tu
  dong chon qua `device="auto"`) nhung **CHUA do toc do/VRAM/chat luong
  giong that tren GPU** - xem checklist day du + rui ro con lai o muc 6p.
- 2026-07-15: **Trien khai 3 nang cap "Uu tien 3"** (nguoi dung chon tu danh
  sach de xuat sau lan ra soat): (1) chong chong lan/troi audio khi long
  tieng - tang toc clip TTS co gioi han 1.3x chi khi tran sang cau ke tiep
  (`_fit_clips_to_timeline` trong `dub.py`) + `build_dub_track` tron cong
  thay vi ghi de khi chong lan; (2) dich theo ngu canh bang Gemini
  (`translator_gemini.py`, REST qua urllib stdlib, batch 40 cau, tu fallback
  NLLB khi khong co GEMINI_API_KEY hoac API loi); (3) Alembic migration
  (`alembic.ini` + `migrations/`, baseline 0001 co guard inspector nhan nuoi
  DB cu, backend startup goi `upgrade head` thay ALTER tay cu). Xem chi tiet
  day du muc 6q moi. **155/155 pytest pass (them 24 test moi), ruff sach,
  `npm run build` pass** - chay THAT tren sandbox co Python. CHUA kiem chung
  tren may that: chua nghe thu audio fit voi video that, chua goi Gemini API
  that (can dien key), chua chay migration tren Postgres that (tu dong khi
  khoi dong backend lan toi).
