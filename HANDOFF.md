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
- **Subtitle editor (Phase 4) dung widget Streamlit thuan (`st.data_editor`),
  KHONG dung Custom Streamlit Component nhu du kien ban dau.** Ly do doi huong
  (2026-07-02): viet mot Streamlit Component that can Node.js/npm de build va
  kiem thu bundle JS/React - moi truong viet code khong co cong cu do (tuong tu
  ly do khong co Python that), nen code React chua tung duoc build la rui ro
  cao hon han. Nang cap len timeline/waveform keo-tha that su la viec lam sau.
- **Stripe webhook (ngoai le HTTP API) da duoc trien khai o Phase 7:**
  `app/billing/webhook_app.py` (FastAPI toi gian, 1 route `/stripe/webhook`),
  chay rieng biet voi Streamlit qua `uvicorn`.

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
6. Auth/User Management trong Streamlit (code xong, **CHUA chay**)
7. Billing/Subscription (Stripe) (code xong, **CHUA chay, can Stripe test account**)
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

## 6f. Phase 6 - Auth/User Management

**Muc tieu:** Dang ky/dang nhap, moi user chi thay job cua minh.

**Trang thai:** Code xong (2026-07-02), **CHUA chay thu, CHUA kiem thu tren
trinh duyet that.**

**Kien truc:**
- `app/db/models.py` them `User` (email, password_hash, created_at). `Job` them
  `user_id` (bat buoc, khong con nullable).
- `app/auth/security.py` - `hash_password`/`verify_password` (bcrypt),
  `create_session_token`/`verify_session_token` (JWT, can `SESSION_SECRET_KEY`).
  Co test (`tests/test_security.py`).
- `app/auth/repository.py` - `UserRepository` (cung mau DI voi JobRepository).
  Co test (`tests/test_user_repository.py`).
- `app/auth/streamlit_helpers.py` - `require_login()` (hien form dang nhap/dang
  ky inline neu chua dang nhap, `st.stop()` neu chua xac thuc), `logout()`.
  Session luu qua cookie (`extra-streamlit-components` CookieManager) vi
  Streamlit khong co session/cookie manager rieng - **day la phan CHUA duoc
  kiem thu tren trinh duyet that, co the co van de tuong thich phien ban
  `extra-streamlit-components`.**
- Upload/Dashboard/Editor deu goi `require_login()` o dau trang va loc job theo
  `user.id` (`JobRepository.list_by_user`).

**Viec can lam:** Mo `streamlit run app/Home.py`, vao trang Upload -> se thay
form dang nhap/dang ky -> dang ky tai khoan moi -> xac nhan job chi hien thi
cho dung user do (tao 2 tai khoan, kiem tra tai khoan A khong thay job cua B).

## 6g. Phase 7 - Billing/Subscription (Stripe)

**Muc tieu:** Goi Free (30 phut/thang) va Pro (thanh toan qua Stripe), gioi han
usage truoc khi cho tao job moi.

**Trang thai:** Code xong (2026-07-02), **CHUA chay thu voi Stripe that (khong
co Stripe test account trong moi truong viet code).**

**Kien truc:**
- `app/db/models.py` them `PlanTier` (free/pro), `Subscription`.
- `app/billing/plans.py` - dinh nghia gioi han phut/thang moi goi.
- `app/billing/usage.py` - `monthly_minutes_used()`, uoc luong thoi luong da xu
  ly tu timestamp `end` cuoi cung trong file JSON ket qua (khong can them
  dependency ffprobe). Co test (`tests/test_usage.py`).
- `app/billing/repository.py` - `SubscriptionRepository`. Co test.
- `app/billing/stripe_service.py` - tao Checkout Session, xac minh webhook.
- `app/billing/webhook_app.py` - FastAPI toi gian, route `/stripe/webhook`,
  cap nhat `Subscription` khi Stripe bao thanh toan thanh cong/huy. Chay rieng:
  `uvicorn app.billing.webhook_app:app --port 8001`.
- `app/pages/4_Billing.py` - xem goi hien tai, usage, nut nang cap (mo link
  Stripe Checkout).
- `app/pages/1_Upload.py` - chan tao job moi neu da vuot gioi han phut/thang
  cua goi hien tai; them kiem tra dinh dang/kich thuoc file (Phase 8).

**Viec can lam (can Stripe test account - https://dashboard.stripe.com, mode
Test):** Tao 1 Product/Price, dien `STRIPE_SECRET_KEY`/`STRIPE_PRO_PRICE_ID`
vao `.env`. Dung `stripe listen --forward-to localhost:8001/stripe/webhook`
(Stripe CLI) de lay `STRIPE_WEBHOOK_SECRET` va forward webhook khi test local.
Thu nang cap tu trang Billing, xac nhan Subscription duoc cap nhat sau khi
thanh toan test thanh cong.

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
- **Chua xac minh Phase 2 tren may that** - dac biet: giai phong VRAM giua cac
  buoc trong CUNG 1 process (`subtitle_pipeline/infrastructure/gpu.py`) co du
  tranh OOM khi chay lien tiep denoise -> transcribe -> align -> diarize hay
  khong. Neu OOM, phuong an du phong: chay tung buoc trong subprocess rieng
  (nhu `phase1_feasibility/run_all.py`) thay vi trong cung 1 process Celery task.
- **Chua xac minh Phase 3 tren may that** - toan bo (docker-compose Postgres/
  Redis, Celery worker, Streamlit multipage, doan them sys.path thu cong o dau
  moi file trong `app/`) chua duoc chay lan nao. Rui ro cao nhat: loi import do
  sys.path (neu Streamlit/Celery version xu ly khac voi gia dinh), va Celery
  worker chay task GPU nang trong tien trinh worker co the gap van de tuong tu
  Phase 2 (OOM) nhung kho debug hon vi chay ngam.
- **Repo hien tai CHUA duoc push len GitHub voi cac thay doi tu Phase 2 tro di**
  (nguoi dung yeu cau lam tiep truoc, chua can day len git - commit gan nhat tren
  remote chi co Phase 1). Nho hoi lai nguoi dung truoc khi commit/push.
- **Chua xac minh Phase 4-8 tren may that** - TOAN BO code Editor, dich thuat,
  auth, billing, storage abstraction, CI moi chi duoc viet va ra soat bang mat
  (khong chay), do sandbox viet code khong co Python that. Danh sach rui ro
  rieng cua tung phan:
  - **Phase 4 (Editor):** `st.data_editor` voi `num_rows="dynamic"` co the co
    hanh vi khac ky vong o phien ban Streamlit cu the; `pd.isna()` xu ly gia
    tri thieu trong cot `speaker` chua duoc kiem chung thuc te.
  - **Phase 5 (Dich - RUI RO CAO NHAT):** `NLLBTranslator` dung
    `tokenizer.convert_tokens_to_ids()` + `model.generate(forced_bos_token_id=...)`
    - cach goi nay hoan toan chua duoc chay thu, kha nang cao se can sua lai
    tham so hoac cach lay ma ngon ngu khi test that (xem docstring trong
    `translator_nllb.py`). Model `nllb-200-distilled-600M` (~2.4GB) can tai ve
    lan dau, cong them VRAM/RAM - CHUA do duoc anh huong toi rang buoc 6GB VRAM.
  - **Phase 6 (Auth):** Luu session qua cookie bang
    `extra-streamlit-components` - thu vien nay co lich su cham cap nhat theo
    Streamlit, co the khong tuong thich voi `streamlit>=1.35`. Neu loi, phuong
    an du phong: dung `st.session_state` don thuan (mat dang nhap khi tai lai
    trang) trong luc cho fix.
  - **Phase 7 (Billing):** CHUA co Stripe test account nao duoc dung - toan bo
    `stripe_service.py`/`webhook_app.py` la code "theo tai lieu Stripe", chua
    validate voi API that. `monthly_minutes_used()` la UOC LUONG (dua vao
    timestamp cuoi cung trong JSON, khong phai thoi luong file that) - co the
    sai lech nho.
  - **Phase 8:** `app/storage.py` (S3Storage) hoan toan chua test (can AWS
    that); CHUA duoc noi vao luong Upload/Editor/Celery task hien co.
  - **Tich hop cheo:** Them `user_id` bat buoc vao `Job` la thay doi schema -
    neu co du lieu Job cu trong DB that (khong co tren may nao vi chua chay
    lan nao) se can migration; hien tai khong van de vi DB luon duoc tao moi
    tu `Base.metadata.create_all()`.
- **Uu tien thu tu kiem thu tren may dev that de cach ly loi hieu qua:**
  Phase 1 (`check_env.py` + `run_all.py`) -> Phase 2 CLI -> `pytest` toan bo
  (bao gom cac test moi: `test_optimize.py`, `test_security.py`,
  `test_user_repository.py`, `test_subscription_repository.py`,
  `test_usage.py`, `test_storage.py`) -> Phase 3 web UI (Upload/Dashboard) ->
  Phase 6 (dang ky/dang nhap - BAT BUOC truoc vi Upload/Dashboard/Editor deu
  can dang nhap) -> Phase 4 (Editor) -> Phase 5 (dich, rui ro cao nhat, test
  sau cung) -> Phase 7 (billing, can Stripe test account rieng) -> Phase 8.

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
  de nghi o muc 8. Repo van CHUA push len GitHub (cho xac nhan tu nguoi dung).
