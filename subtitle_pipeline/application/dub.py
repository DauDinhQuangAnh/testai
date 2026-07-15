"""Dieu phoi long tieng (dubbing): synthesize giong doc cho tung segment DA
DICH, dat clip vao dung timeline, roi mux (ghep) vao video goc thay the
audio cu. Clip TTS dai hon khoang trong toi cau ke tiep se duoc TANG TOC CO
GIOI HAN (ffmpeg atempo, toi da MAX_TEMPO_FACTOR) de giam chong lan/troi dan
ve sau - xem _fit_target_duration. Khac voi co che stretch cu (da bo
2026-07-03 vi ep khop CUNG [start, end] lam giong nghe do): chi tang toc khi
THUC SU tran sang cau sau, va khong bao gio vuot nguong nghe tu nhien.

Mac dinh dung giong co san (edge-tts, khong clone) - neu video co
nhieu nguoi noi (`SubtitleSegment.speaker` tu diarization), TU DONG gan moi
nguoi noi 1 giong khac nhau (xem `_build_speaker_voice_map`) thay vi ca video
dung chung 1 giong. Neu `DubRenderOptions.custom_voice_ref_audio` duoc dat
(giong nguoi dung tu clone o trang "Giong cua toi" - xem HANDOFF.md muc 6p),
dung 1 giong CLONE DUY NHAT (VieNeu-TTS, tts_vieneu.py) cho TOAN BO video
thay the hoan toan co che nhieu-giong o tren. Buoc nay chay SAU buoc dich
(application/translate.py), tach rieng vi la hanh dong tuy chon nguoi dung
kich hoat tu Editor (xem app/jobs/tasks.py: dub_job).

Sau khi mux xong, XOA toan bo `work_dir` (audio trung gian cua ca buoc
transcribe lan cac clip TTS/track am thanh tam) - chi giu lai file ket qua
trong `out_dir` (phu de + video da long tieng). Xem HANDOFF.md Phase 5b,
quyet dinh don file 2026-07-03.
"""

import shutil
import time
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from subtitle_pipeline.application.pronunciation import apply_pronunciation
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import SubtitleStyle, to_ass
from subtitle_pipeline.infrastructure.audio_mux import (
    build_dub_track,
    burn_subtitles,
    mux_audio_into_video,
)
from subtitle_pipeline.infrastructure.audio_timing import (
    probe_duration_seconds,
    time_stretch_to_duration,
)
from subtitle_pipeline.infrastructure.tts_edge import (
    OUTPUT_SAMPLE_RATE,
    VOICE_OPTIONS,
    EdgeTTSSynthesizer,
    default_voice,
)
from subtitle_pipeline.infrastructure.tts_vieneu import VieNeuCloneSynthesizer

MAX_SYNTHESIZE_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2.0

# Chi tang toc clip khi tran qua khoang trong QUA nguong nay (tranh re-encode
# vo ich cho phan tran vai chuc ms khong ai nghe thay).
FIT_TOLERANCE = 1.05
# Tran nguong tang toc nghe con tu nhien - vuot nguong nay tha chap nhan
# chong lan con lai (duoc tron cong trong build_dub_track) con hon giong doc
# nhanh bat thuong (ly do co che stretch cu bi bo, xem HANDOFF.md 2026-07-03).
MAX_TEMPO_FACTOR = 1.3


@dataclass
class DubRenderOptions:
    """Toan bo tuy chon render cua buoc long tieng - gom tu wizard Upload
    (giong/toc do/cao do o buoc Giong doc, am luong/ducking o buoc Am thanh,
    hardsub o buoc Phu de, dinh dang o buoc Xuat). Mac dinh = hanh vi cu
    (giong mac dinh, xoa tieng goc, khong hardsub, mp4).
    """

    voice: str | None = None
    rate_percent: int = 0
    pitch_hz: int = 0
    original_volume: float = 0.0  # 0 = xoa tieng goc hoan toan
    dub_volume: float = 1.0
    ducking: bool = False
    output_format: str = "mp4"  # mp4 | mkv
    burn_subtitles: bool = False
    subtitle_style: SubtitleStyle = field(default_factory=SubtitleStyle)
    render_quality: str = "balanced"  # fast | balanced | high (chi khi hardsub)
    # Tu = cach doc rieng cho TTS (vd. "SQL" -> "ét quy eo") - CHI anh huong
    # audio, khong doi phu de xuat ra. Da gop san mac dinh JSON + override
    # rieng cua job (xem application/pronunciation.py, app/jobs/tasks.py).
    pronunciation: dict[str, str] = field(default_factory=dict)
    # Neu co, dung VieNeu-TTS (tts_vieneu.py) CLONE giong tu file audio nay
    # cho TOAN BO video thay vi edge-tts (bo qua voice/rate_percent/pitch_hz
    # va co che nhieu-giong-theo-nguoi-noi o tren - clone hien chi ho tro 1
    # giong duy nhat/video, xem HANDOFF.md muc 6p).
    custom_voice_ref_audio: Path | None = None


def _total_duration(work_dir: Path, source_video: Path) -> float:
    denoised_audio = work_dir / "audio_denoised.wav"
    if denoised_audio.exists():
        import soundfile as sf

        info = sf.info(str(denoised_audio))
        return info.frames / info.samplerate
    return probe_duration_seconds(source_video)


def _clean_text_for_speech(text: str) -> str:
    """`optimize_segments()` (application/optimize.py) chen `\\n` vao text de
    ngat dong HIEN THI tren phu de (vd. toi da 42 ky tu/dong) - dua thang
    chuoi co `\\n` do vao TTS lam giong doc bi ngat quang/loi giua chung. TTS
    chi can 1 cau lien tuc, khong lien quan gi toi cach ngat dong phu de.
    """
    return " ".join(text.split())


def _build_speaker_voice_map(
    segments: list[SubtitleSegment], language: str, voice: str | None
) -> dict[str | None, str]:
    """Gan 1 giong doc rieng cho tung nguoi noi (speaker) khac nhau trong
    video - neu khong, ca video (du bao nhieu nguoi noi) se dung chung 1
    giong (xem HANDOFF.md). Nguoi noi xuat hien DAU TIEN dung dung `voice`
    (giong nguoi dung chon o Upload/Editor, hoac giong mac dinh cua ngon ngu
    neu khong chon) - giu dung ky vong "chon giong X" cua nguoi dung. Cac
    nguoi noi tiep theo lan luot nhan 1 giong KHAC trong VOICE_OPTIONS cua
    ngon ngu do, xoay vong neu nhieu nguoi noi hon so giong co san. Neu
    khong co diarization (moi segment `speaker=None`), ca video van dung 1
    giong duy nhat - dung hanh vi cu.
    """
    resolved_default = voice or default_voice(language)
    other_voices = [v for v in VOICE_OPTIONS[language].values() if v != resolved_default]

    voice_by_speaker: dict[str | None, str] = {}
    for seg in segments:
        if seg.speaker in voice_by_speaker:
            continue
        if not voice_by_speaker:
            voice_by_speaker[seg.speaker] = resolved_default
        elif other_voices:
            index = (len(voice_by_speaker) - 1) % len(other_voices)
            voice_by_speaker[seg.speaker] = other_voices[index]
        else:
            voice_by_speaker[seg.speaker] = resolved_default
    return voice_by_speaker


def _clip_duration_seconds(path: Path) -> float:
    import soundfile as sf

    info = sf.info(str(path))
    return info.frames / info.samplerate


def _fit_target_duration(clip_duration: float, window_seconds: float) -> float | None:
    """Tinh thoi luong muc tieu de tang toc 1 clip TTS cho vua khoang trong
    toi cau ke tiep. Tra None neu khong can dung gi (clip da vua, hoac chi
    tran trong nguong FIT_TOLERANCE). Neu can tang toc qua MAX_TEMPO_FACTOR
    moi vua, chi tang toi da MAX_TEMPO_FACTOR (chap nhan chong lan con lai) -
    giu giong doc trong nguong nghe tu nhien. Ham thuan, test duoc rieng.
    """
    if window_seconds <= 0 or clip_duration <= window_seconds * FIT_TOLERANCE:
        return None
    return max(window_seconds, clip_duration / MAX_TEMPO_FACTOR)


def _fit_clips_to_timeline(
    clips: list[tuple[int, SubtitleSegment, Path]], total_duration: float
) -> list[tuple[float, Path]]:
    """Tang toc (co gioi han) cac clip TTS dai hon khoang trong den cau ke
    tiep de giam chong lan giua cac cau va troi dan ve sau trong video dai.
    Khoang trong tinh toi START cua clip ke tiep (khong ep khop [start, end]
    cua chinh segment - cau sau cach xa thi cau truoc duoc noi thong tha).
    Loi ffmpeg khi stretch chi lam mat toi uu cua 1 clip (dung ban raw),
    khong lam fail ca job.
    """
    fitted: list[tuple[float, Path]] = []
    overflow_count = 0
    for index, (i, seg, clip_path) in enumerate(clips):
        next_start = clips[index + 1][1].start if index + 1 < len(clips) else total_duration
        window = next_start - seg.start
        clip_duration = _clip_duration_seconds(clip_path)
        target = _fit_target_duration(clip_duration, window)
        if target is not None:
            fit_path = clip_path.with_name(f"{i:05d}_fit.wav")
            try:
                time_stretch_to_duration(clip_path, fit_path, target)
                clip_path = fit_path
            except Exception as exc:
                print(f"[dub] Khong tang toc duoc clip {i}: {exc}")
            if target > window:
                overflow_count += 1
        fitted.append((seg.start, clip_path))
    if overflow_count:
        print(
            f"[dub] Canh bao: {overflow_count} cau van dai hon khoang trong du da "
            f"tang toc {MAX_TEMPO_FACTOR}x - phan tran se chong lan cau ke tiep."
        )
    return fitted


def _synthesize_with_retry(tts: EdgeTTSSynthesizer, text: str, output_path: Path) -> bool:
    """edge-tts thinh thoang loi mang/API thoang qua (xem HANDOFF.md Phase
    5b) - thu lai toi da MAX_SYNTHESIZE_ATTEMPTS lan truoc khi bo qua han
    segment nay (de lai khoang lang thay vi lam that bai ca job).
    """
    for attempt in range(1, MAX_SYNTHESIZE_ATTEMPTS + 1):
        try:
            tts.synthesize(text, output_path)
            return True
        except Exception as exc:
            if attempt == MAX_SYNTHESIZE_ATTEMPTS:
                print(f"[dub] Bo qua segment sau {attempt} lan loi: {exc}")
                return False
            time.sleep(RETRY_BACKOFF_SECONDS)
    return False


def dub_and_export(
    segments: list[SubtitleSegment],
    target_language: str,
    source_video: Path,
    work_dir: Path,
    out_dir: Path,
    stem: str,
    options: DubRenderOptions | None = None,
) -> Path:
    options = options or DubRenderOptions()
    segment_dir = work_dir / f"dub_{target_language}_segments"
    segment_dir.mkdir(parents=True, exist_ok=True)

    use_cloned_voice = options.custom_voice_ref_audio is not None
    voice_by_speaker = (
        {}
        if use_cloned_voice
        else _build_speaker_voice_map(segments, target_language, options.voice)
    )

    raw_clips: list[tuple[int, SubtitleSegment, Path]] = []
    with ExitStack() as stack:
        synthesizers: dict[str, EdgeTTSSynthesizer] = {}
        cloned_tts = (
            stack.enter_context(VieNeuCloneSynthesizer(options.custom_voice_ref_audio))
            if use_cloned_voice
            else None
        )
        for i, seg in enumerate(segments):
            text = _clean_text_for_speech(seg.text)
            if options.pronunciation:
                text = apply_pronunciation(text, options.pronunciation)
            if not text:
                continue

            if cloned_tts is not None:
                tts = cloned_tts
            else:
                seg_voice = voice_by_speaker[seg.speaker]
                if seg_voice not in synthesizers:
                    synthesizers[seg_voice] = stack.enter_context(
                        EdgeTTSSynthesizer(
                            target_language,
                            voice=seg_voice,
                            rate_percent=options.rate_percent,
                            pitch_hz=options.pitch_hz,
                        )
                    )
                tts = synthesizers[seg_voice]

            raw_clip = segment_dir / f"{i:05d}_raw.wav"
            if not _synthesize_with_retry(tts, text, raw_clip):
                continue

            raw_clips.append((i, seg, raw_clip))

    total_duration = _total_duration(work_dir, source_video)
    fitted_clips = _fit_clips_to_timeline(raw_clips, total_duration)
    dub_track_path = work_dir / f"dub_track_{target_language}.wav"
    build_dub_track(fitted_clips, total_duration, OUTPUT_SAMPLE_RATE, dub_track_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{stem}.{target_language}.dubbed.{options.output_format}"

    if options.burn_subtitles:
        # Mux ra file trung gian trong work_dir, roi gan cung phu de (styled
        # ASS sinh tu chinh segments da dich) vao file cuoi cung - buoc nay
        # re-encode video nen cham hon han mux thuong.
        intermediate = work_dir / f"dubbed_nosub.{options.output_format}"
        mux_audio_into_video(
            source_video,
            dub_track_path,
            intermediate,
            original_volume=options.original_volume,
            dub_volume=options.dub_volume,
            ducking=options.ducking,
        )
        ass_path = work_dir / f"burn_{target_language}.ass"
        ass_path.write_text(to_ass(segments, options.subtitle_style), encoding="utf-8")
        burn_subtitles(intermediate, ass_path, output_path, quality=options.render_quality)
    else:
        mux_audio_into_video(
            source_video,
            dub_track_path,
            output_path,
            original_volume=options.original_volume,
            dub_volume=options.dub_volume,
            ducking=options.ducking,
        )

    shutil.rmtree(work_dir, ignore_errors=True)
    return output_path
