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
    st.info("Chua co job nao hoan thanh. Vao trang Upload de tao job moi.")
    st.page_link("pages/1_Upload.py", label="Upload video/audio", icon=":material/upload:")
    st.stop()

job_options = {f"{j.filename} ({j.id[:8]})": j for j in done_jobs}
selected_label = st.selectbox("Chon job", list(job_options.keys()))
job = job_options[selected_label]

output_dir = Path(job.output_dir)
input_path = Path(job.input_path)
json_path = output_dir / f"{input_path.stem}.json"

if not json_path.exists():
    st.error(f"Khong tim thay file ket qua: {json_path}")
    st.stop()

with open(json_path, encoding="utf-8") as f:
    raw_segments = json.load(f)

tab_edit, tab_translate, tab_dub = st.tabs(
    ["Chinh sua phu de", "Dich phu de", "Long tieng lai"]
)

with tab_edit:
    col_video, col_editor = st.columns([2, 3])

    with col_video:
        st.caption("Video/audio goc")
        if input_path.suffix.lower() in {".mp4", ".mkv", ".mov"}:
            st.video(str(input_path))
        else:
            st.audio(str(input_path))

    with col_editor:
        edited_df = st.data_editor(
            pd.DataFrame(raw_segments),
            column_config={
                "start": st.column_config.NumberColumn("Bat dau (s)", format="%.2f"),
                "end": st.column_config.NumberColumn("Ket thuc (s)", format="%.2f"),
                "text": st.column_config.TextColumn("Noi dung", width="large"),
                "speaker": st.column_config.TextColumn("Nguoi noi"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor-{job.id}",
        )

        def _clean_speaker(value) -> str | None:
            return None if pd.isna(value) else str(value)

        if st.button("Luu va xuat lai file", type="primary", icon=":material/save:"):
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
            st.success("Da luu va xuat lai file phu de.")

with tab_translate:
    st.caption(
        "Chi xuat phu de da dich (khong tao audio). File ket qua co hau to "
        "ngon ngu, vd. video.vi.srt."
    )
    target_language = st.selectbox("Ngon ngu dich", SUPPORTED_LANGUAGES, key="translate-language")
    if st.button("Dich va xuat file moi", icon=":material/translate:"):
        translate_job.delay(job.id, target_language)
        st.info(
            f"Da gui yeu cau dich sang '{target_language}'. File se xuat hien "
            f"trong Dashboard sau it phut."
        )

with tab_dub:
    st.caption(
        "Upload da tu long tieng theo lua chon luc tao job. Dung tab nay de lam "
        "lai voi ngon ngu/giong/che do khac - he thong tu dich neu chua co ban "
        "dich. Giong doc la giong chuan, chua ho tro clone giong goc."
    )
    col_lang, col_voice = st.columns(2)
    dub_target_language = col_lang.selectbox(
        "Ngon ngu long tieng", SUPPORTED_LANGUAGES, key="dub-language"
    )
    dub_voice_label = col_voice.selectbox(
        "Giong doc", list(VOICE_OPTIONS[dub_target_language].keys()), key="dub-voice"
    )
    dub_voice = VOICE_OPTIONS[dub_target_language][dub_voice_label]

    DUB_AUDIO_MODE_REPLACE = "Xoa tieng goc (chi con tieng dich)"
    DUB_AUDIO_MODE_KEEP = "Giu tieng goc giam 70% + tieng dich len tren (kieu thuyet minh)"
    dub_audio_mode = st.radio(
        "Xu ly tieng goc",
        [DUB_AUDIO_MODE_REPLACE, DUB_AUDIO_MODE_KEEP],
        key="dub-audio-mode",
    )
    dub_keep_original = dub_audio_mode == DUB_AUDIO_MODE_KEEP

    if st.button("Dich + Long tieng", type="primary", icon=":material/record_voice_over:"):
        dub_job.delay(job.id, dub_target_language, dub_voice, dub_keep_original)
        st.info(
            "Da gui yeu cau dich + long tieng (chay ngam, co the mat vai phut). "
            f"File ket qua: {input_path.stem}.{dub_target_language}.dubbed.mp4"
        )

    dubbed_video_path = output_dir / f"{input_path.stem}.{dub_target_language}.dubbed.mp4"
    if dubbed_video_path.exists():
        st.video(str(dubbed_video_path))
        st.download_button(
            "Tai video da long tieng",
            data=dubbed_video_path.read_bytes(),
            file_name=dubbed_video_path.name,
            icon=":material/download:",
        )
