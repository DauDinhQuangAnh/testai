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

st.subheader("Buoc 1 - Chon file", divider=True)
uploaded_file = st.file_uploader("Video/audio dau vao", type=sorted(ALLOWED_EXTENSIONS))

file_valid = False
if uploaded_file is not None:
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

    col_name, col_size = st.columns(2)
    col_name.metric("Ten file", uploaded_file.name)
    col_size.metric("Kich thuoc", f"{size_mb:.1f} MB")

    if extension not in ALLOWED_EXTENSIONS:
        st.error(f"Dinh dang '.{extension}' khong duoc ho tro.")
    elif size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File qua lon ({size_mb:.0f} MB), gioi han la {MAX_FILE_SIZE_MB} MB.")
    else:
        file_valid = True

st.subheader("Buoc 2 - Tuy chon long tieng", divider=True)
dubbing_enabled = st.toggle(
    "Long tieng tu dong sau khi tao phu de",
    value=True,
    help="Tat neu chi can phu de (job chay nhanh hon, khong can internet cho TTS).",
)

target_language = None
voice = None
keep_original_audio = False
if dubbing_enabled:
    col_lang, col_voice = st.columns(2)
    target_language = col_lang.selectbox(
        "Ngon ngu long tieng",
        SUPPORTED_LANGUAGES,
        index=SUPPORTED_LANGUAGES.index("vi") if "vi" in SUPPORTED_LANGUAGES else 0,
    )
    # Danh sach giong doi theo ngon ngu (giong ban dia nam/nu + multilingual).
    voice_label = col_voice.selectbox("Giong doc", list(VOICE_OPTIONS[target_language].keys()))
    voice = VOICE_OPTIONS[target_language][voice_label]

    AUDIO_MODE_REPLACE = "Xoa tieng goc (chi con tieng dich)"
    AUDIO_MODE_KEEP = "Giu tieng goc giam 70% + tieng dich len tren (kieu thuyet minh)"
    audio_mode = st.radio(
        "Xu ly tieng goc",
        [AUDIO_MODE_REPLACE, AUDIO_MODE_KEEP],
        help=(
            "Giu tieng goc: giu khong khi nen (nhac, hieu ung) cua video goc, "
            "giong doc dich tron len tren - video goc PHAI co san audio."
        ),
    )
    keep_original_audio = audio_mode == AUDIO_MODE_KEEP

st.subheader("Buoc 3 - Tao job", divider=True)
if not file_valid:
    st.caption("Chon file hop le o Buoc 1 de tiep tuc.")
elif st.button("Tao job xu ly", type="primary", icon=":material/rocket_launch:"):
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

    st.success(f"Da tao job `{job.id[:8]}`.")
    if dubbing_enabled:
        st.caption(
            f"Job tu chay het: tach am -> nhan dien loi noi -> dich sang "
            f"'{target_language}' -> long tieng -> xuat video, khong can thao tac them."
        )
    else:
        st.caption("Job chi tao phu de (khong long tieng).")
    st.page_link(
        "pages/2_Dashboard.py", label="Xem tien do o Dashboard", icon=":material/monitoring:"
    )
