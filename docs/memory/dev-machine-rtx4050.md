# May dev muc tieu: RTX 4050 Laptop 6GB VRAM

Day la ho so cau hinh may dev THAT dung de code/test du an AI Subtitle Studio.
Khac voi bat ky sandbox tam thoi nao ma mot cong cu AI coding co the dang chay
lenh trong do (vi du: mot phien cloud cua Claude Code khong co GPU/Python that -
xem ghi chu o cuoi file nay).

## Cau hinh phan cung

- CPU: Intel Core i5-13450HX
- GPU: RTX 4050 Laptop, 6GB VRAM
- RAM: 24GB DDR5
- SSD: NVMe
- OS: Windows 11
- Day la may DEV, khong phai production. Thiet ke can tinh den dev/test tren may
  nay truoc, roi moi scale len ha tang production (cloud GPU) sau.

## Anh huong toi thiet ke pipeline AI

- 6GB VRAM khong du de giu dong thoi nhieu model lon tren GPU (DeepFilterNet3 +
  Faster-Whisper + WhisperX align + pyannote diarization cung luc se OOM). Kien
  truc pipeline bat buoc theo kieu **load model tuan tu -> infer -> giai phong
  VRAM -> load model tiep theo**.
- Faster-Whisper `large-v3` o fp16 can ~10GB VRAM -> tren 6GB phai dung
  quantization (`int8_float16` hoac `int8` qua CTranslate2) hoac dung
  `medium`/`large-v3-turbo` cho dev.
- Silero VAD va DeepFilterNet3 du nhe de chay CPU neu can danh GPU rieng cho STT.
- pyannote diarization can chap nhan license gated model tren HuggingFace
  (`pyannote/speaker-diarization-3.1`, `pyannote/segmentation-3.0`) + access
  token (bien moi truong `HF_TOKEN`).
- Celery worker cho hang doi GPU nen gioi han concurrency = 1 tren may dev - khong
  the test xu ly song song nhieu job GPU that su (khac voi production, noi can GPU
  lon hon 16GB+ de giu model resident va xu ly concurrent).

Chi tiet ket qua do dac VRAM/thoi gian thuc te cho tung buoc pipeline nam trong
`HANDOFF.md` (muc 6, do `phase1_feasibility/summarize_results.py` tu dong cap
nhat).

## Luu y cho AI coding assistant (Claude Code / Codex) doc file nay

- Neu ban dang chay lenh TRUC TIEP tren may co cau hinh nhu tren (co GPU that),
  ban CO THE tu chay/test cac script trong `phase1_feasibility/` - hay tu kiem
  tra bang `python phase1_feasibility/check_env.py` truoc khi ket luan gi.
- Neu ban dang chay trong 1 sandbox/container rieng (vi du moi truong cloud cua
  Claude Code khong gan voi may vat ly nay) thi co the KHONG co GPU/Python that -
  trong truong hop do, chi viet code, KHONG gia dinh minh chay/test duoc, va de
  nguoi dung tu chay tren may dev that roi bao lai ket qua.
