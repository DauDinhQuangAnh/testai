"""Trang upload theo dang wizard 3 buoc: chon file -> tuy chon long tieng ->
tao job. Job tu chay het transcribe -> dich -> long tieng trong 1 lan (xem
HANDOFF.md Phase 5b); co the tat long tieng de chi tao phu de.

Kiem tra truoc khi tao job: dinh dang file hop le + kich thuoc khong vuot
gioi han (khop `maxUploadSize` trong .streamlit/config.toml).
"""

import sys
import uuid
from pathlib import Path

import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.config import AppConfig
from app.jobs.repository import JobRepository
from app.jobs.tasks import process_video_job
from subtitle_pipeline.infrastructure.translator_nllb import SUPPORTED_LANGUAGES
from subtitle_pipeline.infrastructure.tts_edge import VOICE_OPTIONS

ALLOWED_EXTENSIONS = {"mp4", "mkv", "mov", "wav", "mp3", "m4a"}
MAX_FILE_SIZE_MB = 500

st.set_page_config(page_title="Upload - AI Subtitle Studio", page_icon=":material/upload:")
st.title("Upload video/audio")

config = AppConfig.from_env()
job_repo = JobRepository()

st.subheader("Bước 1 - Chọn file", divider=True)
uploaded_file = st.file_uploader("Video/audio đầu vào", type=sorted(ALLOWED_EXTENSIONS))

file_valid = False
if uploaded_file is not None:
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

    col_name, col_size = st.columns(2)
    col_name.metric("Tên file", uploaded_file.name)
    col_size.metric("Kích thước", f"{size_mb:.1f} MB")

    if extension not in ALLOWED_EXTENSIONS:
        st.error(f"Định dạng '.{extension}' không được hỗ trợ.")
    elif size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File quá lớn ({size_mb:.0f} MB), giới hạn là {MAX_FILE_SIZE_MB} MB.")
    else:
        file_valid = True

st.subheader("Bước 2 - Tùy chọn lồng tiếng", divider=True)
dubbing_enabled = st.toggle(
    "Lồng tiếng tự động sau khi tạo phụ đề",
    value=True,
    help="Tắt nếu chỉ cần phụ đề (job chạy nhanh hơn, không cần internet cho TTS).",
)

target_language = None
voice = None
keep_original_audio = False
if dubbing_enabled:
    col_lang, col_voice = st.columns(2)
    target_language = col_lang.selectbox(
        "Ngôn ngữ lồng tiếng",
        SUPPORTED_LANGUAGES,
        index=SUPPORTED_LANGUAGES.index("vi") if "vi" in SUPPORTED_LANGUAGES else 0,
    )
    # Danh sach giong doi theo ngon ngu (giong ban dia nam/nu + multilingual).
    voice_label = col_voice.selectbox("Giọng đọc", list(VOICE_OPTIONS[target_language].keys()))
    voice = VOICE_OPTIONS[target_language][voice_label]

    AUDIO_MODE_REPLACE = "Xóa tiếng gốc (chỉ còn tiếng dịch)"
    AUDIO_MODE_KEEP = "Giữ tiếng gốc giảm 70% + tiếng dịch lên trên (kiểu thuyết minh)"
    audio_mode = st.radio(
        "Xử lý tiếng gốc",
        [AUDIO_MODE_REPLACE, AUDIO_MODE_KEEP],
        help=(
            "Giữ tiếng gốc: giữ không khí nền (nhạc, hiệu ứng) của video gốc, "
            "giọng đọc dịch trộn lên trên - video gốc PHẢI có sẵn audio."
        ),
    )
    keep_original_audio = audio_mode == AUDIO_MODE_KEEP

st.subheader("Bước 3 - Tạo job", divider=True)
if not file_valid:
    st.caption("Chọn file hợp lệ ở Bước 1 để tiếp tục.")
elif st.button("Tạo job xử lý", type="primary", icon=":material/rocket_launch:"):
    job_id = str(uuid.uuid4())
    job_dir = config.storage_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / uploaded_file.name
    input_path.write_bytes(uploaded_file.getvalue())

    job = job_repo.create(
        filename=uploaded_file.name,
        input_path=input_path,
        output_dir=job_dir / "output",
        job_id=job_id,
    )
    process_video_job.delay(job.id, target_language, voice, keep_original_audio)

    st.success(f"Đã tạo job `{job.id[:8]}`.")
    if dubbing_enabled:
        st.caption(
            f"Job tự chạy hết: tách âm -> nhận diện lời nói -> dịch sang "
            f"'{target_language}' -> lồng tiếng -> xuất video, không cần thao tác thêm."
        )
    else:
        st.caption("Job chỉ tạo phụ đề (không lồng tiếng).")
    st.page_link(
        "pages/2_Dashboard.py", label="Xem tiến độ ở Dashboard", icon=":material/monitoring:"
    )
