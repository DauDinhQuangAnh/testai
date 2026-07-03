"""Trang editor: chinh sua text/timing/speaker cua 1 job da hoan thanh, xuat lai
file phu de, va (tuy chon) dich sang ngon ngu khac.

Ban v1 dung widget Streamlit thuan (st.data_editor) thay vi Custom Streamlit
Component (React) nhu phac thao ban dau trong roadmap. Ly do doi huong: xay
mot Streamlit Component that can Node.js/npm de build va kiem thu bundle JS -
moi truong viet code hien tai khong co cong cu do (tuong tu ly do khong co
Python that - xem docs/memory/dev-machine-rtx4050.md), nen code React chua tung
duoc build la rui ro cao hon han Python. Nang cap len timeline/waveform keo-tha
that su la viec lam sau, khi co moi truong build/test JS ro rang.
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

st.set_page_config(page_title="Editor - AI Subtitle Studio")
st.title("Subtitle Editor")

repo = JobRepository()
done_jobs = [j for j in repo.list_all() if j.status == JobStatus.DONE]

if not done_jobs:
    st.info("Chua co job nao hoan thanh. Vao trang Upload de tao job moi.")
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

st.caption("Video/audio goc:")
if input_path.suffix.lower() in {".mp4", ".mkv", ".mov"}:
    st.video(str(input_path))
else:
    st.audio(str(input_path))

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


if st.button("Luu va xuat lai file"):
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

st.divider()
st.subheader("Dich sang ngon ngu khac")
target_language = st.selectbox("Ngon ngu dich", SUPPORTED_LANGUAGES)
if st.button("Dich va xuat file moi"):
    translate_job.delay(job.id, target_language)
    st.info(
        f"Da gui yeu cau dich sang '{target_language}'. File ket qua se co hau to "
        f"ngon ngu (vd. {input_path.stem}.{target_language}.srt) sau it phut."
    )

st.divider()
st.subheader("Long tieng (lam lai hoac doi sang ngon ngu khac)")
st.caption(
    "Upload da tu chay long tieng theo ngon ngu chon luc tao job. Dung khoi "
    "nay neu muon lam lai hoac long tieng sang ngon ngu khac. Chi can chon "
    "ngon ngu va bam 1 nut - he thong tu dich (neu chua dich) roi long tieng. "
    "Giong doc la giong chuan (chua ho tro clone giong goc trong ban nay - "
    "xem HANDOFF.md Phase 5b)."
)
dub_target_language = st.selectbox("Ngon ngu long tieng", SUPPORTED_LANGUAGES, key="dub-language")
dub_voice_label = st.selectbox(
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
if st.button("Dich + Long tieng"):
    dub_job.delay(job.id, dub_target_language, dub_voice, dub_keep_original)
    st.info(
        "Da gui yeu cau dich + long tieng. Qua trinh chay ngam (dich roi long "
        f"tieng) co the mat vai phut. File ket qua: "
        f"{input_path.stem}.{dub_target_language}.dubbed.mp4"
    )

dubbed_video_path = output_dir / f"{input_path.stem}.{dub_target_language}.dubbed.mp4"
if dubbed_video_path.exists():
    st.video(str(dubbed_video_path))
    st.download_button(
        "Tai video da long tieng",
        data=dubbed_video_path.read_bytes(),
        file_name=dubbed_video_path.name,
    )
