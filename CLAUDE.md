# CLAUDE.md

Truoc khi lam bat ky viec gi trong repo nay, DOC TOAN BO file `HANDOFF.md` o goc
repo truoc tien. Do la nguon trang thai/tien do/quyet dinh kien truc DUY NHAT va
moi nhat cua du an "AI Subtitle Studio", dung chung giua Claude Code va Codex.

Sau khi hoan thanh hoac thay doi gi quan trong, cap nhat lai HANDOFF.md (khong
tao them file trang thai/markdown moi trung muc dich).

Ghi chu boi canh/ly do dang sau cac quyet dinh (kien truc, cau hinh may dev RTX
4050 6GB VRAM, quy uoc HANDOFF.md) nam o `docs/memory/` - doc them neu can hieu
sau hon "tai sao", nhung khong dung de theo doi tien do (do la viec cua
HANDOFF.md).

Code Python trong repo nay PHAI theo chuan trong `docs/CODE_STYLE.md` (Ruff
format/lint, type hint, quy uoc dat ten, docstring chi giai thich WHY...).
Truoc khi coi 1 task viet/sua code la xong, chay `ruff check --fix .`,
`ruff format .`, `pytest` neu moi truong hien tai cho phep (xem luu y ve
sandbox khong co Python o duoi).

**Luu y quan trong:** HANDOFF.md phan biet ro "sandbox cua Claude Code" (moi
truong dang chay lenh trong phien do) va "may dev that" (RTX 4050 6GB VRAM, noi
chay/test AI pipeline). Ket luan "khong co GPU/Python" trong HANDOFF.md chi dung
cho sandbox luc no duoc viet - KHONG mac dinh ap dung cho may ban dang chay hien
tai. Neu dang chay truc tiep tren may dev that co GPU, hay tu kiem tra lai (vd.
chay `phase1_feasibility/check_env.py`) thay vi gia dinh khong chay duoc.
