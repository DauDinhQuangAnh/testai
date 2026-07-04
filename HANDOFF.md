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

- **Tool CA NHAN, KHONG con da nguoi dung/Auth/Billing (quyet dinh 2026-07-03,
  xem "Quyet dinh moi"):** khong dang nhap, khong phan quyen theo user, khong
  goi cuoc/gioi han usage. Moi job hien thi cho tat ca (thuc te chi 1 nguoi
  dung tren 1 may dev). Da xoa hoan toan `app/auth/`, `app/billing/`,
  `app/pages/4_Billing.py`, bang `users`/`subscriptions`, cot `Job.user_id`.
- **Frontend/Backend UI: Streamlit xuyen suot.** KHONG dung Next.js. Streamlit
  goi truc tiep ham Python (in-process), KHONG dung FastAPI lam lop REST API
  trung gian.
- **Celery + Redis + Postgres van giu nguyen** - khong phai de lam REST API, ma
  de serialize cac job GPU nang (may dev chi chay duoc concurrency=1 cho GPU) va
  luu trang thai job. Streamlit chi enqueue task roi poll Postgres/Redis.
- **Subtitle editor (Phase 4) dung widget Streamlit thuan (`st.data_editor`),
  KHONG dung Custom Streamlit Component nhu du kien ban dau.** Ly do doi huong
  (2026-07-02): viet mot Streamlit Component that can Node.js/npm de build va
  kiem thu bundle JS/React - moi truong viet code khong co cong cu do (tuong tu
  ly do khong co Python that), nen code React chua tung duoc build la rui ro
  cao hon han. Nang cap len timeline/waveform keo-tha that su la viec lam sau.
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
- `app/storage.py` - abstraction `Storage` (Protocol) + `LocalStorage` (dung
  hien tai) + `S3Storage` (boto3, lazy-import). **CHUA duoc noi vao
  Upload/Editor/Celery task** (cac cho do van dung `Path` filesystem truc tiep
  - hanh vi tuong duong `LocalStorage` nhung khong di qua abstraction nay). Co
  test cho `LocalStorage` (`tests/test_storage.py`); `S3Storage` khong test
  duoc (can AWS credential that).
- `.github/workflows/ci.yml` - chay `ruff check` + `ruff format --check` +
  `pytest` tren moi push/PR len `main`.
- Hardening Upload: gioi han kich thuoc file (500MB) + kiem tra dinh dang phia
  server (khong chi dua vao `type=[...]` cua `st.file_uploader`).

**CHUA lam (ghi nhan de lam sau, khong xay truoc khi can - tranh du thua):**
- Secrets management that (Vault, AWS Secrets Manager...) - hien dang dung
  `.env`/bien moi truong, du cho dev/MVP nhung khong phai chuan production.
- Deploy multi-instance Streamlit + reverse proxy (sticky session).
- Wiring `app/storage.py` vao cac luong hien co de dung S3 that.

**Viec can lam:** Xem CI chay pass tren GitHub sau khi push. Test
`LocalStorage`/`get_storage()` qua `pytest`.

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
- Neu cau TTS qua dai/qua ngan so voi khung thoi gian goc, `atempo` co the lam
  giong nghe khong tu nhien (nhanh/cham bat thuong) - chua co gioi han canh
  bao hay fallback nao khac ngoai viec chia nho factor cho hop le voi ffmpeg.
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
- **GIOI HAN TRUNG THUC:** "dich theo ngu canh/giong dieu" kieu VietDub can
  LLM - NLLB khong nhan chi dan. Ghi ro o UI; LLM translator adapter la
  viec sau (can API key).

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

## 8. Van de dang mo / can quyet dinh

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
  khi tin tuong so lieu.
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
  - **Phase 8:** `app/storage.py` (S3Storage) hoan toan chua test (can AWS
    that); CHUA duoc noi vao luong Upload/Editor/Celery task hien co.
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
