"""Test bang phat am TTS (application/pronunciation.py) - ham thuan, khong
can model TTS that. Xac nhan file mac dinh JSON co that + duoc doc dung.
"""

from subtitle_pipeline.application.pronunciation import (
    apply_pronunciation,
    load_default_pronunciation,
    parse_pronunciation_overrides,
    resolve_pronunciation_glossary,
)


def test_load_default_pronunciation_has_sql_seed_entry_for_vietnamese():
    glossary = load_default_pronunciation("vi")

    assert glossary.get("SQL") == "ét quy eo"


def test_load_default_pronunciation_returns_empty_for_unknown_language():
    assert load_default_pronunciation("xx") == {}


def test_parse_pronunciation_overrides_skips_invalid_lines():
    text = "SQL = ét quy eo\nkhong co dau bang\n = rong\nAPI = ây pi ai"

    overrides = parse_pronunciation_overrides(text)

    assert overrides == {"SQL": "ét quy eo", "API": "ây pi ai"}


def test_resolve_merges_default_and_job_overrides():
    glossary = resolve_pronunciation_glossary("vi", "API = ây pi ai")

    assert glossary["sql"] == "ét quy eo"
    assert glossary["api"] == "ây pi ai"


def test_resolve_job_override_replaces_default_entry():
    glossary = resolve_pronunciation_glossary("vi", "SQL = ét quy lờ")

    assert glossary["sql"] == "ét quy lờ"


def test_apply_pronunciation_replaces_whole_word_case_insensitively():
    glossary = resolve_pronunciation_glossary("vi")

    result = apply_pronunciation("Học SQL và sql server rất vui", glossary)

    assert result == "Học ét quy eo và ét quy eo server rất vui"


def test_apply_pronunciation_does_not_touch_partial_word():
    glossary = {"ai": "trí tuệ nhân tạo"}

    result = apply_pronunciation("PAINT khong phai la AI", glossary)

    assert result == "PAINT khong phai la trí tuệ nhân tạo"
