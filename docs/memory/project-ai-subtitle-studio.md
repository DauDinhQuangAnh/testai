# AI Subtitle Studio - Tong quan du an

Du an: "AI Subtitle Studio" - **tool ca nhan** (khong con huong toi SaaS
thuong mai - xem quyet dinh 2026-07-03 ben duoi) tu dong tao/chinh sua phu de
+ long tieng tu video/audio, tu trien khai toan bo pipeline AI ma nguon mo
(FFmpeg -> DeepFilterNet3 -> Silero VAD -> Faster-Whisper large-v3 -> WhisperX
align -> pyannote diarization -> dich da ngon ngu -> TTS long tieng -> export
SRT/VTT/ASS/TXT/JSON + video da long tieng).

**Quyet dinh 2026-07-03 - bo huong SaaS, chuyen thanh tool ca nhan:** nguoi
dung xac nhan khong can thanh toan/da nguoi dung nua. Da xoa hoan toan Auth
(dang ky/dang nhap) va Billing (goi cuoc/gioi han usage) - xem HANDOFF.md muc
6f/6g/7. Khong con can can nhac license thuong mai khi chon model AI (vd. TTS
- xem tts_edge.py).

## Quyet dinh kien truc quan trong (chot ngay 2026-07-01)

- Frontend/backend UI dung **Streamlit xuyen suot** (khong dung Next.js).
  Streamlit goi truc tiep ham Python, khong qua REST API/FastAPI.
- Celery + Redis + Postgres van giu de serialize job GPU nang va luu trang thai
  job (khong phai lam REST API).
- Subtitle editor (timeline/waveform) se can Custom Streamlit Component (React
  nho nhung vao Streamlit) - hien dang dung `st.data_editor` thuan cho v1.

## Roadmap (tom tat - xem HANDOFF.md de biet trang thai chi tiet/hien tai)

1. Feasibility Spike AI pipeline tren may dev
2. AI Pipeline Core (dong goi module hoa, CLI)
3. Streamlit App - Upload + Job Dashboard
4. Subtitle Editor (Custom Streamlit Component)
5. Da ngon ngu + toi uu cau subtitle
5b. Long tieng (Dubbing/TTS) - edge-tts + ghep audio vao video
6. ~~Auth/User Management~~ - DA XOA 2026-07-03 (tool ca nhan)
7. ~~Goi cuoc + gioi han usage~~ - DA XOA 2026-07-03 (khong con SaaS)
8. Bao mat nang cao + Ha tang Production
9. Monitoring/Scale nang cao - chi lam khi co traffic/user that (kha nang
   khong con can thiet vi la tool ca nhan)

## Ly do cac quyet dinh tren

May dev that la RTX 4050 Laptop 6GB VRAM - qua nho de giu nhieu model lon tren
GPU dong thoi (xem [dev-machine-rtx4050.md](dev-machine-rtx4050.md)), nen pipeline
phai thiet ke theo kieu load/unload tuan tu, va Phase 1 (feasibility spike do
VRAM/thoi gian thuc te) phai lam truoc tien de xac nhan tinh kha thi ky thuat
truoc khi dau tu cong suc vao UI/billing.
