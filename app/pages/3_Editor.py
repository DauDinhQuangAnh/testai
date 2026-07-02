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

from app.auth.streamlit_helpers import require_login
from app.db.models import JobStatus
from app.jobs.repository import JobRepository
from app.jobs.tasks import translate_job
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS

SUPPORTED_TRANSLATION_LANGUAGES = ["en", "vi", "zh", "ja", "ko", "fr", "es"]

st.set_page_config(page_title="Editor - AI Subtitle Studio")
user = require_login()
st.title("Subtitle Editor")

repo = JobRepository()
done_jobs = [j for j in repo.list_by_user(user.id) if j.status == JobStatus.DONE]

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
target_language = st.selectbox("Ngon ngu dich", SUPPORTED_TRANSLATION_LANGUAGES)
if st.button("Dich va xuat file moi"):
    translate_job.delay(job.id, target_language)
    st.info(
        f"Da gui yeu cau dich sang '{target_language}'. File ket qua se co hau to "
        f"ngon ngu (vd. {input_path.stem}.{target_language}.srt) sau it phut."
    )
