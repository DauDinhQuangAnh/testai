"""CLI de chay pipeline tu dau den cuoi: video/audio -> file subtitle.

Chay: python -m subtitle_pipeline.cli input.mp4 --out-dir output --formats srt,vtt
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

from subtitle_pipeline.application.pipeline import TranscriptionPipeline
from subtitle_pipeline.config import PipelineConfig
from subtitle_pipeline.export.formats import FORMAT_WRITERS

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Duong dan video/audio dau vao")
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--formats", default="srt,vtt,ass,txt,json")
    parser.add_argument("--language", default=None)
    parser.add_argument(
        "--work-dir", default=None, help="Thu muc luu file trung gian (audio da tach/khu on)"
    )
    args = parser.parse_args()

    config = PipelineConfig.from_env()
    if args.language:
        config.language = args.language

    input_path = Path(args.input)
    out_dir = Path(args.out_dir)
    work_dir = Path(args.work_dir) if args.work_dir else out_dir / "_work"

    pipeline = TranscriptionPipeline(config=config, work_dir=work_dir)
    segments = pipeline.run(input_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    for fmt in args.formats.split(","):
        fmt = fmt.strip()
        writer = FORMAT_WRITERS[fmt]
        out_path = out_dir / f"{stem}.{fmt}"
        out_path.write_text(writer(segments), encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
