"""Bang thuat ngu (glossary) cho buoc dich: ep NLLB giu dung thuat ngu nguoi
dung chi dinh bang ky thuat mask/restore - thay term nguon bang token trung
gian TRUOC khi dich (NLLB giu nguyen token la), roi thay token bang term dich
SAU khi dich. Day la cach kha thi duy nhat voi model dich thuan nhu NLLB
(khong nhan duoc chi dan kieu LLM - xem HANDOFF.md).

LUU Y RUI RO: chua verify tren may that viec NLLB giu nguyen token qua buoc
dich - neu model "dich" ca token (hiem nhung co the), restore se khong khop
va term dich khong duoc chen vao. `restore_terms` dung regex chiu duoc
khoang trang chen giua de giam rui ro nay.
"""

import re

# Token dang <<T0>>, <<T1>>... - chuoi ASCII la (khong phai tu co nghia) de
# NLLB co xu huong giu nguyen thay vi dich.
_TOKEN_TEMPLATE = "<<T{index}>>"
_TOKEN_PATTERN_TEMPLATE = r"<<\s*T\s*{index}\s*>>"


def parse_glossary(text: str) -> list[tuple[str, str]]:
    """Parse textarea nguoi dung nhap, moi dong `nguon = dich`. Dong khong co
    dau `=` hoac term rong bi bo qua. Sap xep term nguon DAI truoc de khi
    mask khong bi term ngan "an" mat 1 phan term dai (vd. "SQL Server" phai
    duoc mask truoc "SQL").
    """
    entries = []
    for line in text.splitlines():
        if "=" not in line:
            continue
        source, _, target = line.partition("=")
        source, target = source.strip(), target.strip()
        if source and target:
            entries.append((source, target))
    return sorted(entries, key=lambda e: len(e[0]), reverse=True)


def mask_terms(text: str, glossary: list[tuple[str, str]]) -> str:
    """Thay term nguon (khong phan biet hoa thuong, chi khop nguyen tu) bang
    token thu tu - index token = vi tri entry trong glossary de restore_terms
    tra nguoc dung term dich.
    """
    for index, (source, _target) in enumerate(glossary):
        token = _TOKEN_TEMPLATE.format(index=index)
        pattern = r"\b" + re.escape(source) + r"\b"
        text = re.sub(pattern, token, text, flags=re.IGNORECASE)
    return text


def restore_terms(text: str, glossary: list[tuple[str, str]]) -> str:
    for index, (_source, target) in enumerate(glossary):
        pattern = _TOKEN_PATTERN_TEMPLATE.format(index=index)
        text = re.sub(pattern, target, text)
    return text
