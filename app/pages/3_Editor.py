"""Trang editor chia 3 tab: chinh sua phu de / dich / long tieng lai.

Ban v1 dung widget Streamlit thuan (st.data_editor) thay vi Custom Streamlit
Component (React) - xay component that can Node.js/npm de build/kiem thu,
moi truong viet code khong co (xem HANDOFF.md quyet dinh 2026-07-02). Nang
cap len timeline/waveform keo-tha la viec lam sau.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.db.models import JobStatus
from app.jobs.repository import JobRepository
from app.jobs.tasks import dub_job, translate_job
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS
from subtitle_pipeline.infrastructure.translator_nllb import SUPPORTED_LANGUAGES
from subtitle_pipeline.infrastructure.tts_edge import VOICE_OPTIONS

st.set_page_config(
    page_title="Editor - AI Subtitle Studio", page_icon=":material/edit:", layout="wide"
)
st.title("Subtitle Editor")

repo = JobRepository()
done_jobs = [j for j in repo.list_all() if j.status == JobStatus.DONE]

if not done_jobs:
    st.info("Chưa có job nào hoàn thành. Vào trang Upload để tạo job mới.")
    st.page_link("pages/1_Upload.py", label="Upload video/audio", icon=":material/upload:")
    st.stop()

job_options = {f"{j.filename} ({j.id[:8]})": j for j in done_jobs}
selected_label = st.selectbox("Chọn job", list(job_options.keys()))
job = job_options[selected_label]

output_dir = Path(job.output_dir)
input_path = Path(job.input_path)
json_path = output_dir / f"{input_path.stem}.json"

if not json_path.exists():
    st.error(f"Không tìm thấy file kết quả: {json_path}")
    st.stop()

with open(json_path, encoding="utf-8") as f:
    raw_segments = json.load(f)

tab_edit, tab_translate, tab_dub = st.tabs(
    ["Chỉnh sửa phụ đề", "Dịch phụ đề", "Lồng tiếng lại"]
)

with tab_edit:
    col_video, col_editor = st.columns([2, 3])

    with col_video:
        st.caption("Video/audio gốc")
        if input_path.suffix.lower() in {".mp4", ".mkv", ".mov"}:
            st.video(str(input_path))
        else:
            st.audio(str(input_path))

    with col_editor:
        edited_df = st.data_editor(
            pd.DataFrame(raw_segments),
            column_config={
                "start": st.column_config.NumberColumn("Bắt đầu (s)", format="%.2f"),
                "end": st.column_config.NumberColumn("Kết thúc (s)", format="%.2f"),
                "text": st.column_config.TextColumn("Nội dung", width="large"),
                "speaker": st.column_config.TextColumn("Người nói"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor-{job.id}",
        )

        def _clean_speaker(value) -> str | None:
            return None if pd.isna(value) else str(value)

        if st.button("Lưu và xuất lại file", type="primary", icon=":material/save:"):
            edited_segments = [
                SubtitleSegment(
                    start=float(row["start"]),
                    end=float(row["end"]),
                    text=str(row["text"]),
                    speaker=_clean_speaker(row.get("speaker")),
                )
                for _, row in edited_df.iterrows()
            ]
            for fmt, writer in FORMAT_WRITERS.items():
                (output_dir / f"{input_path.stem}.{fmt}").write_text(
                    writer(edited_segments), encoding="utf-8"
                )
            st.success("Đã lưu và xuất lại file phụ đề.")

with tab_translate:
    st.caption(
        "Chỉ xuất phụ đề đã dịch (không tạo audio). File kết quả có hậu tố "
        "ngôn ngữ, ví dụ video.vi.srt."
    )
    target_language = st.selectbox("Ngôn ngữ dịch", SUPPORTED_LANGUAGES, key="translate-language")
    if st.button("Dịch và xuất file mới", icon=":material/translate:"):
        translate_job.delay(job.id, target_language)
        st.info(
            f"Đã gửi yêu cầu dịch sang '{target_language}'. File sẽ xuất hiện "
            f"trong Dashboard sau ít phút."
        )

with tab_dub:
    st.caption(
        "Upload đã tự lồng tiếng theo lựa chọn lúc tạo job. Dùng tab này để làm "
        "lại với ngôn ngữ/giọng/chế độ khác - hệ thống tự dịch nếu chưa có bản "
        "dịch. Giọng đọc là giọng chuẩn, chưa hỗ trợ clone giọng gốc."
    )
    col_lang, col_voice = st.columns(2)
    dub_target_language = col_lang.selectbox(
        "Ngôn ngữ lồng tiếng", SUPPORTED_LANGUAGES, key="dub-language"
    )
    dub_voice_label = col_voice.selectbox(
        "Giọng đọc", list(VOICE_OPTIONS[dub_target_language].keys()), key="dub-voice"
    )
    dub_voice = VOICE_OPTIONS[dub_target_language][dub_voice_label]

    DUB_AUDIO_MODE_REPLACE = "Xóa tiếng gốc (chỉ còn tiếng dịch)"
    DUB_AUDIO_MODE_KEEP = "Giữ tiếng gốc giảm 70% + tiếng dịch lên trên (kiểu thuyết minh)"
    dub_audio_mode = st.radio(
        "Xử lý tiếng gốc",
        [DUB_AUDIO_MODE_REPLACE, DUB_AUDIO_MODE_KEEP],
        key="dub-audio-mode",
    )
    dub_keep_original = dub_audio_mode == DUB_AUDIO_MODE_KEEP

    if st.button("Dịch + Lồng tiếng", type="primary", icon=":material/record_voice_over:"):
        dub_job.delay(job.id, dub_target_language, dub_voice, dub_keep_original)
        st.info(
            "Đã gửi yêu cầu dịch + lồng tiếng (chạy ngầm, có thể mất vài phút). "
            f"File kết quả: {input_path.stem}.{dub_target_language}.dubbed.mp4"
        )

    dubbed_video_path = output_dir / f"{input_path.stem}.{dub_target_language}.dubbed.mp4"
    if dubbed_video_path.exists():
        st.video(str(dubbed_video_path))
        st.download_button(
            "Tải video đã lồng tiếng",
            data=dubbed_video_path.read_bytes(),
            file_name=dubbed_video_path.name,
            icon=":material/download:",
        )
