"""Quy tac phat am tuy chinh cho giong doc long tieng (TTS) - CHI anh huong
audio, KHONG doi chu hien thi tren phu de xuat ra. Khac voi bang thuat ngu
dich (application/glossary.py) von giu nguyen CHU VIET khi dich - module nay
doi CACH DOC cua 1 tu truoc khi dua vao TTS (vd. "SQL" doc thanh "ét quy eo"
thay vi giong TTS tu danh van tung chu cai kieu tieng Anh).

Nguon quy tac gom 2 lop, lop sau ghi de neu trung tu (khong phan biet hoa
thuong):
1. File JSON mac dinh (infrastructure/pronunciation_glossary.json) - nguoi
   dung tu mo sua/them truc tiep de dung lau dai, khong can qua UI moi lan.
2. Textarea "Bang phat am" nguoi dung nhap rieng cho 1 job (wizard buoc
   Dich, frontend/src/pages/NewJob.tsx) - chi ap dung cho job do.
"""

import json
import re
from pathlib import Path

_DEFAULT_GLOSSARY_PATH = Path(__file__).resolve().parent.parent / (
    "infrastructure/pronunciation_glossary.json"
)


def load_default_pronunciation(language: str) -> dict[str, str]:
    """Doc bang phat am mac dinh cho 1 ngon ngu tu file JSON. Tra ve {} neu
    file khong ton tai hoac ngon ngu chua co quy tac nao (vd. hien chi 'vi'
    co du lieu).
    """
    if not _DEFAULT_GLOSSARY_PATH.exists():
        return {}
    data = json.loads(_DEFAULT_GLOSSARY_PATH.read_text(encoding="utf-8"))
    return dict(data.get(language, {}))


def parse_pronunciation_overrides(text: str) -> dict[str, str]:
    """Parse textarea nguoi dung nhap rieng cho 1 job, moi dong `tu = cach
    doc` - cung format voi bang thuat ngu dich (application/glossary.py) de
    nhat quan trai nghiem, nhung day la 1 truong du lieu hoan toan tach
    biet (khong di qua NLLB, chi dung truoc TTS).
    """
    overrides: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        term, _, pronunciation = line.partition("=")
        term, pronunciation = term.strip(), pronunciation.strip()
        if term and pronunciation:
            overrides[term] = pronunciation
    return overrides


def resolve_pronunciation_glossary(language: str, overrides_text: str = "") -> dict[str, str]:
    """Gop bang mac dinh (JSON) + override rieng cua job (textarea) - entry
    tu textarea ghi de entry JSON trung tu (khong phan biet hoa thuong).
    """
    merged = {k.lower(): v for k, v in load_default_pronunciation(language).items()}
    merged.update({k.lower(): v for k, v in parse_pronunciation_overrides(overrides_text).items()})
    return merged


def apply_pronunciation(text: str, glossary: dict[str, str]) -> str:
    """Thay tu (khop nguyen tu, khong phan biet hoa thuong) bang cach phat am
    tuy chinh - CHI goi truoc khi dua text vao TTS, KHONG dung cho phu de
    xuat ra. Sap xep tu dai truoc de tu dai (vd. "SQL Server") khong bi tu
    ngan (vd. "SQL") an mat 1 phan khi thay the.
    """
    for term, pronunciation in sorted(glossary.items(), key=lambda kv: len(kv[0]), reverse=True):
        pattern = r"\b" + re.escape(term) + r"\b"
        text = re.sub(pattern, pronunciation, text, flags=re.IGNORECASE)
    return text
