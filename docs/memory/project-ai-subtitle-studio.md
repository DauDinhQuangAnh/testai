# AI Subtitle Studio - Tong quan du an

Du an dai han: xay dung "AI Subtitle Studio" - website tu dong tao/chinh sua phu
de tu video/audio (kieu CapCut AI Subtitle, Veed.io, Descript, WhisperX), tu trien
khai toan bo pipeline AI ma nguon mo (FFmpeg -> DeepFilterNet3 -> Silero VAD ->
Faster-Whisper large-v3 -> WhisperX align -> pyannote diarization -> dich da ngon
ngu -> export SRT/VTT/ASS/TXT/JSON), huong toi SaaS thuong mai that.

## Quyet dinh kien truc quan trong (chot ngay 2026-07-01)

- Frontend/backend UI dung **Streamlit xuyen suot, ke ca ban thuong mai sau nay**
  (khong dung Next.js). Streamlit goi truc tiep ham Python, khong qua REST
  API/FastAPI.
- Celery + Redis + Postgres van giu de serialize job GPU nang va luu trang thai
  job (khong phai lam REST API).
- 2 ngoai le bat buoc phai co HTTP endpoint that: Stripe webhook (billing) va
  deploy multi-instance Streamlit sau nay.
- Subtitle editor (timeline/waveform) se can Custom Streamlit Component (React
  nho nhung vao Streamlit).

## Roadmap 9 phase (tom tat - xem HANDOFF.md de biet trang thai chi tiet/hien tai)

1. Feasibility Spike AI pipeline tren may dev
2. AI Pipeline Core (dong goi module hoa, CLI)
3. Streamlit App - Upload + Job Dashboard
4. Subtitle Editor (Custom Streamlit Component)
5. Da ngon ngu + toi uu cau subtitle
6. Auth/User Management trong Streamlit
7. Billing/Subscription (co ngoai le Stripe webhook)
8. Bao mat nang cao + Ha tang Production
9. Monitoring/Scale nang cao - chi lam khi co traffic/user that

## Ly do cac quyet dinh tren

May dev that la RTX 4050 Laptop 6GB VRAM - qua nho de giu nhieu model lon tren
GPU dong thoi (xem [dev-machine-rtx4050.md](dev-machine-rtx4050.md)), nen pipeline
phai thiet ke theo kieu load/unload tuan tu, va Phase 1 (feasibility spike do
VRAM/thoi gian thuc te) phai lam truoc tien de xac nhan tinh kha thi ky thuat
truoc khi dau tu cong suc vao UI/billing.
