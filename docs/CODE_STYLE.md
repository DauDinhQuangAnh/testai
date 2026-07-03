# Chuan Code (Python)

Ap dung cho toan bo code Python trong repo (`subtitle_pipeline/`, `app/`,
`phase1_feasibility/`, `tests/`) - danh cho ca Claude Code va Codex khi
them/sua code tu thoi diem file nay duoc tao (2026-07-02) tro di. Code cu hon
co the CHUA tuan thu day du (xem HANDOFF.md muc "Van de dang mo").

## Cong cu (xem `pyproject.toml`, `requirements-dev.txt`)

- Format + Lint: **Ruff** (`ruff format .`, `ruff check --fix .`)
- Test: **pytest** (`pytest` tu goc repo)
- Enforce tu dong: **pre-commit** (`.pre-commit-config.yaml`) - chay
  `pre-commit install` MOT LAN tren may dev that de kich hoat git hook; sau do
  moi lan `git commit` se tu dong chay Ruff tren cac file thay doi.

## Quy uoc

- Line length toi da 100 ky tu.
- Type hint day du cho tham so + gia tri tra ve cua moi public function/method.
- Docstring: CHI viet khi giai thich WHY (rang buoc an, quyet dinh thiet ke,
  workaround cho van de cu the) - KHONG mo ta WHAT (ten ham/bien/module da du
  ro nghia). Giu 1 doan ngan o dau module khi can, khong them docstring rieng
  cho tung ham don gian, tu no da giai thich duoc qua ten goi.
- Khong dung emoji trong code/comment/docstring.
- **Chuoi hien thi cho nguoi dung (UI Streamlit, thong bao loi ghi vao
  `Job.error_message`, nhan giong doc...) PHAI la tieng Viet CO DAU** (quyet
  dinh 2026-07-03 theo yeu cau nguoi dung). Comment/docstring/tai lieu noi bo
  (HANDOFF.md, docs/) van giu khong dau - nguoi dung cuoi khong nhin thay.
- Naming: `snake_case` cho function/variable, `PascalCase` cho class,
  `UPPER_SNAKE_CASE` cho constant.
- Package that (co logic ben trong, duoc import boi module khac) phai co
  `__init__.py` ro rang, khong dua vao namespace package ngoai y muon.
- Import thu vien AI nang (torch, faster_whisper, whisperx, pyannote, df) CHI o
  trong than ham/method, KHONG o top-level module - de cac layer khac
  (domain/, application/, export/) va test cua chung khong bi buoc phai cai
  dat cac thu vien do (xem vi du trong `subtitle_pipeline/infrastructure/`).
- Dependency injection qua constructor/factory khi 1 class phu thuoc tai
  nguyen ben ngoai (model AI, DB session) - xem
  `TranscriptionPipeline.denoiser_factory`, `JobRepository.session_factory` -
  giup test duoc bang fake/in-memory thay vi phai co GPU/DB that.
- Test dat trong `tests/`, ten file `test_<module>.py`, dung fixture pytest
  (`tmp_path`, `monkeypatch`) thay vi tu viet setup/teardown thu cong.
- Khi sua code co san, giu nguyen phong cach da co trong file do thay vi ap
  dat phong cach moi cuc bo trong cung 1 file.

## Quy trinh truoc khi coi 1 task la "xong"

1. `ruff check --fix .`
2. `ruff format .`
3. `pytest`

Luu y: sandbox cua mot so cong cu AI coding (vd. Claude Code trong mot so
phien) co the khong co Python that cai san - xem
`docs/memory/dev-machine-rtx4050.md`. Neu khong chay duoc 3 lenh tren, ghi ro
trong HANDOFF.md la "chua chay qua chuan code" thay vi tu nhan la da lam xong.
