"""Trang tao video theo wizard 6 buoc (kieu VietDub): Nguon -> Giong doc ->
Dich -> Phu de -> Am thanh & Xuat -> Xem lai. Dung `st.tabs` (moi tab 1 buoc,
tat ca render cung luc nen bien cua tab truoc dung duoc o tab sau) thay vi
fake-stepper session_state - ben hon nhieu khi Streamlit rerun.

Toan bo lua chon gom vao 1 dict `options` truyen cho Celery task
`process_video_job(job_id, options)` va luu `job_config.json` vao thu muc job
(de trace + nut "Tao lai voi cau hinh nay" o Dashboard).
"""

import json
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
from subtitle_pipeline.infrastructure.translator_nllb import (
    NLLB_LANGUAGE_CODES,
    SUPPORTED_LANGUAGES,
)
from subtitle_pipeline.infrastructure.tts_edge import synthesize_sample, voice_catalog

ALLOWED_EXTENSIONS = {"mp4", "mkv", "mov", "wav", "mp3", "m4a"}
MAX_FILE_SIZE_MB = 500

TRIM_CHOICES = {"Toàn bộ video": None, "Chạy thử 60 giây đầu": 60, "Chạy thử 120 giây đầu": 120}
QUALITY_CHOICES = {"Ổn định 720p (nhẹ, nhanh)": "720p", "Tốt nhất có sẵn": "best"}
TRANSLATE_PRESETS = {
    "Cân bằng (mặc định)": (42, 2),
    "Súc tích (dòng ngắn, dễ đọc nhanh)": (32, 1),
    "Thoải mái (dòng dài, ít ngắt)": (50, 2),
}
POSITION_CHOICES = {"Dưới": "bottom", "Giữa": "middle", "Trên": "top"}
FORMAT_CHOICES = ["mp4", "mkv"]
RENDER_QUALITY_CHOICES = {"Cân bằng": "balanced", "Nhanh": "fast", "Cao": "high"}
FONT_CHOICES = ["Arial", "Segoe UI", "Tahoma", "Verdana", "Roboto", "Times New Roman"]

st.set_page_config(
    page_title="Tạo video - AI Subtitle Studio", page_icon=":material/movie:", layout="wide"
)
st.title("Tạo video")
st.caption("Đi qua 6 bước bên dưới rồi bấm **Tạo và khởi chạy** ở bước Xem lại.")

config = AppConfig.from_env()

(tab_source, tab_voice, tab_translate, tab_subtitle, tab_audio, tab_review) = st.tabs(
    [
        "1 · Nguồn",
        "2 · Giọng đọc",
        "3 · Dịch",
        "4 · Phụ đề",
        "5 · Âm thanh & Xuất",
        "6 · Xem lại",
    ]
)

# ---------------------------------------------------------------- 1 · Nguồn
with tab_source:
    st.subheader("Chọn nguồn video")
    source_kind = st.radio(
        "Nguồn",
        ["Dán URL (YouTube/Douyin/TikTok...)", "Tải file lên"],
        horizontal=True,
        label_visibility="collapsed",
    )
    use_url = source_kind.startswith("Dán URL")

    source_url = ""
    uploaded_file = None
    file_valid = False

    if use_url:
        source_url = st.text_input(
            "URL video", placeholder="https://www.youtube.com/watch?v=... hoặc link Douyin"
        )
        quality_label = st.selectbox("Chất lượng tải xuống", list(QUALITY_CHOICES.keys()))
        download_quality = QUALITY_CHOICES[quality_label]
        file_valid = bool(source_url.strip())
    else:
        download_quality = "720p"
        uploaded_file = st.file_uploader("Video/audio đầu vào", type=sorted(ALLOWED_EXTENSIONS))
        if uploaded_file is not None:
            size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            col_name, col_size = st.columns(2)
            col_name.metric("Tên file", uploaded_file.name)
            col_size.metric("Kích thước", f"{size_mb:.1f} MB")
            if size_mb > MAX_FILE_SIZE_MB:
                st.error(f"File quá lớn ({size_mb:.0f} MB), giới hạn {MAX_FILE_SIZE_MB} MB.")
            else:
                file_valid = True

    col_trim, col_srclang = st.columns(2)
    trim_label = col_trim.selectbox(
        "Kiểm thử (chạy thử đoạn ngắn)",
        list(TRIM_CHOICES.keys()),
        help="Chạy thử đoạn đầu để xem trước giọng/bản dịch trước khi chạy cả video dài.",
    )
    trim_seconds = TRIM_CHOICES[trim_label]

    source_lang_options = ["Tự phát hiện (khuyên dùng)", *sorted(NLLB_LANGUAGE_CODES.keys())]
    source_lang_label = col_srclang.selectbox(
        "Ngôn ngữ nguồn",
        source_lang_options,
        help="Chỉ ép cứng khi auto-detect đoán sai (video lẫn nhiều thứ tiếng).",
    )
    source_language = None if source_lang_label.startswith("Tự phát hiện") else source_lang_label

# ------------------------------------------------------------ 2 · Giọng đọc
with tab_voice:
    st.subheader("Giọng đọc và cách diễn đạt")
    dubbing_enabled = st.toggle(
        "Lồng tiếng tự động sau khi tạo phụ đề",
        value=True,
        help="Tắt nếu chỉ cần phụ đề (job nhanh hơn, không cần internet cho TTS).",
    )

    target_language = "vi"
    voice = None
    rate_percent = 0
    pitch_hz = 0
    if dubbing_enabled:
        col_lang, col_voice = st.columns(2)
        target_language = col_lang.selectbox(
            "Ngôn ngữ lồng tiếng",
            SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index("vi"),
        )
        catalog = voice_catalog(target_language)
        voice_labels = {
            (":star: " if v["recommended"] else "") + f"{v['label']} · {v['style']}": v["id"]
            for v in catalog
        }
        voice_label = col_voice.selectbox(
            "Giọng đọc",
            list(voice_labels.keys()),
            help=(
                "⭐ = giọng bản địa, phát âm chuẩn nhất. Áp dụng cho người nói đầu "
                "tiên; video nhiều người nói sẽ tự gán thêm giọng khác nhau."
            ),
        )
        voice = voice_labels[voice_label]

        col_rate, col_pitch = st.columns(2)
        rate_percent = col_rate.slider(
            "Tốc độ nói", min_value=-50, max_value=50, value=0, format="%d%%"
        )
        pitch_hz = col_pitch.slider("Cao độ", min_value=-20, max_value=20, value=0, format="%dHz")

        if st.button("Nghe thử giọng này", icon=":material/play_circle:"):
            cache_key = f"sample-{voice}-{rate_percent}-{pitch_hz}"
            if cache_key not in st.session_state:
                try:
                    with st.spinner("Đang tạo mẫu giọng..."):
                        st.session_state[cache_key] = synthesize_sample(
                            target_language, voice, rate_percent, pitch_hz
                        )
                except Exception as exc:
                    st.error(f"Không tạo được mẫu giọng (cần internet): {exc}")
            if cache_key in st.session_state:
                st.audio(st.session_state[cache_key], format="audio/mp3")

# ----------------------------------------------------------------- 3 · Dịch
with tab_translate:
    st.subheader("Mục đích dịch")
    preset_label = st.segmented_control(
        "Kiểu trình bày bản dịch",
        options=list(TRANSLATE_PRESETS.keys()),
        default=list(TRANSLATE_PRESETS.keys())[0],
    )
    max_chars_per_line, max_lines = TRANSLATE_PRESETS[
        preset_label or list(TRANSLATE_PRESETS.keys())[0]
    ]

    glossary_text = st.text_area(
        "Bảng thuật ngữ",
        placeholder="CPU = CPU\nSQL Server = SQL Server\nmachine learning = học máy",
        help=(
            "Mỗi dòng một cặp `nguồn = đích` - ép giữ đúng thuật ngữ khi dịch "
            "(tên riêng, từ chuyên ngành không muốn bị dịch sai)."
        ),
        height=120,
    )
    st.caption(
        "Dịch theo ngữ cảnh sâu (giọng điệu, hướng dẫn tự do) cần model LLM - "
        "sẽ bổ sung sau. Hiện tại engine dịch là NLLB chạy local."
    )

# --------------------------------------------------------------- 4 · Phụ đề
with tab_subtitle:
    st.subheader("Kiểu dáng phụ đề")
    burn_in = st.toggle(
        "Gắn phụ đề vào video (hardsub)",
        value=False,
        help=(
            "Bật: chữ được vẽ cứng vào hình (xem được ở mọi trình phát, nhưng "
            "render lâu hơn vì phải encode lại video). Tắt: chỉ xuất file phụ đề rời."
        ),
    )

    col_style_left, col_style_right = st.columns(2)
    with col_style_left:
        sub_font = st.selectbox("Phông chữ", FONT_CHOICES)
        sub_size = st.slider("Cỡ chữ", 24, 96, 48)
        sub_position_label = st.radio(
            "Vị trí", list(POSITION_CHOICES.keys()), index=0, horizontal=True
        )
    with col_style_right:
        sub_text_color = st.color_picker("Màu chữ", "#FFFFFF")
        sub_outline_color = st.color_picker("Màu viền", "#000000")
        sub_outline_width = st.slider("Độ dày viền", 0.0, 6.0, 2.0, step=0.5)
        sub_opaque_box = st.toggle("Hộp nền đặc sau chữ", value=False)

    # Xem truoc tinh bang HTML/CSS mo phong style da chon (khong can ffmpeg).
    position_css = {"Dưới": "flex-end", "Giữa": "center", "Trên": "flex-start"}[sub_position_label]
    box_css = "background: rgba(0,0,0,0.75); padding: 4px 12px; border-radius: 4px;"
    preview_shadow = (
        f"text-shadow: 0 0 {max(sub_outline_width, 0.5)}px {sub_outline_color}, "
        f"0 0 {max(sub_outline_width, 0.5) * 2}px {sub_outline_color};"
    )
    st.markdown(
        f"""
        <div style="width:100%; aspect-ratio:16/6; background:
            linear-gradient(135deg,#31343C,#16181D); border-radius:8px;
            display:flex; align-items:{position_css}; justify-content:center;
            padding:18px;">
          <span style="font-family:'{sub_font}',sans-serif;
              font-size:{max(14, sub_size // 3)}px; color:{sub_text_color};
              {preview_shadow} {box_css if sub_opaque_box else ""}">
            Bản dịch giữ đúng ngữ cảnh và vừa khung hình.
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------ 5 · Âm thanh & Xuất
with tab_audio:
    col_mix, col_out = st.columns(2)
    with col_mix:
        st.subheader("Phối âm")
        original_volume_pct = st.slider(
            "Âm lượng âm gốc",
            0,
            100,
            0,
            format="%d%%",
            help=(
                "0% = xóa hẳn tiếng gốc. >0% = giữ nhạc nền/hiệu ứng ở mức này (kiểu thuyết minh)."
            ),
        )
        dub_volume_pct = st.slider("Âm lượng giọng lồng tiếng", 50, 150, 100, format="%d%%")
        ducking = st.toggle(
            "Giảm âm gốc khi có lời thoại",
            value=False,
            disabled=original_volume_pct == 0,
            help="Chỉ giảm track gốc trong khi giọng lồng tiếng đang hoạt động (sidechain).",
        )
        st.caption(f"🔉 Gốc {original_volume_pct}% · Giọng {dub_volume_pct}%")
    with col_out:
        st.subheader("Đầu ra")
        output_format = st.selectbox("Định dạng", FORMAT_CHOICES)
        render_quality_label = st.selectbox(
            "Chất lượng dựng",
            list(RENDER_QUALITY_CHOICES.keys()),
            help=(
                "Chỉ áp dụng khi gắn phụ đề cứng (phải encode lại). Không "
                "hardsub thì video copy nguyên vẹn, luôn nhanh."
            ),
        )
        render_quality = RENDER_QUALITY_CHOICES[render_quality_label]

# -------------------------------------------------------------- 6 · Xem lại
with tab_review:
    st.subheader("Xem lại cấu hình đã xác nhận")

    options = {
        "source": {
            "url": source_url.strip() or None if use_url else None,
            "quality": download_quality,
            "trim_seconds": trim_seconds,
            "source_language": source_language,
        },
        "dubbing": {
            "enabled": dubbing_enabled,
            "target_language": target_language,
            "voice": voice,
            "rate_percent": rate_percent,
            "pitch_hz": pitch_hz,
        },
        "translation": {
            "glossary": glossary_text,
            "max_chars_per_line": max_chars_per_line,
            "max_lines": max_lines,
        },
        "subtitle": {
            "burn_in": burn_in,
            "style": {
                "font": sub_font,
                "font_size": sub_size,
                "text_color": sub_text_color,
                "outline_color": sub_outline_color,
                "outline_width": sub_outline_width,
                "position": POSITION_CHOICES[sub_position_label],
                "opaque_box": sub_opaque_box,
            },
        },
        "audio": {
            "original_volume": original_volume_pct / 100,
            "dub_volume": dub_volume_pct / 100,
            "ducking": ducking and original_volume_pct > 0,
        },
        "output": {"format": output_format, "quality": render_quality},
    }

    col1, col2 = st.columns(2)
    with col1.container(border=True):
        st.markdown("**NGUỒN**")
        source_desc = source_url or (uploaded_file.name if uploaded_file else "(chưa chọn)")
        st.write(source_desc)
        st.caption(
            f"{source_lang_label} → {target_language if dubbing_enabled else 'chỉ phụ đề'}"
            f" · {trim_label}"
        )
    with col2.container(border=True):
        st.markdown("**GIỌNG ĐỌC**")
        st.write(voice or "(tắt lồng tiếng)")
        st.caption(f"Tốc độ {rate_percent:+d}% · Cao độ {pitch_hz:+d}Hz")

    col3, col4 = st.columns(2)
    with col3.container(border=True):
        st.markdown("**DỊCH**")
        st.write(preset_label or "Cân bằng")
        glossary_count = sum(1 for line in glossary_text.splitlines() if "=" in line)
        st.caption(f"Bảng thuật ngữ: {glossary_count} mục")
    with col4.container(border=True):
        st.markdown("**PHỤ ĐỀ**")
        st.write("Gắn cứng vào video" if burn_in else "Xuất file rời")
        st.caption(f"{sub_font} {sub_size}px · {sub_position_label} · viền {sub_outline_width:g}px")

    with st.container(border=True):
        st.markdown("**ÂM THANH & ĐẦU RA**")
        st.write(f"Gốc {original_volume_pct}% / Giọng {dub_volume_pct}%")
        st.caption(
            f"{'Ducking bật · ' if options['audio']['ducking'] else ''}"
            f"{output_format.upper()} · Dựng: {render_quality_label}"
        )

    st.divider()
    if not file_valid:
        st.warning("Chưa có nguồn hợp lệ - quay lại bước 1 để chọn file hoặc dán URL.")
    elif st.button("Tạo và khởi chạy", type="primary", icon=":material/rocket_launch:"):
        job_id = str(uuid.uuid4())
        job_dir = config.storage_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        if use_url:
            filename = source_url.strip()
            input_path = job_dir / "download_pending"  # worker cap nhat sau khi tai
        else:
            filename = uploaded_file.name
            input_path = job_dir / uploaded_file.name
            input_path.write_bytes(uploaded_file.getvalue())

        (job_dir / "job_config.json").write_text(
            json.dumps(options, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        job = JobRepository().create(
            filename=filename,
            input_path=input_path,
            output_dir=job_dir / "output",
            job_id=job_id,
        )
        process_video_job.delay(job.id, options)

        st.success(f"Đã tạo job `{job.id[:8]}` và khởi chạy.")
        st.page_link(
            "pages/2_Dashboard.py", label="Xem tiến độ ở Dashboard", icon=":material/monitoring:"
        )
