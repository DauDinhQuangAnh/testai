"""Kieu du lieu thuan (khong phu thuoc thu vien AI nao), dai dien cho du lieu di
chuyen qua cac buoc cua pipeline. Vi khong import torch/whisper/..., cac module
dung kieu nay (application/, export/) test duoc ma khong can cai dat AI libs.
"""
from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class SpeakerTurn:
    start: float
    end: float
    speaker: str


@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None
