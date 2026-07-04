"""Test glossary mask/restore - ham thuan, khong can model dich that."""

from subtitle_pipeline.application.glossary import mask_terms, parse_glossary, restore_terms


def test_parse_skips_invalid_lines_and_sorts_longest_first():
    text = "SQL = SQL\nkhong co dau bang\nSQL Server = SQL Server\n = rong\n"

    glossary = parse_glossary(text)

    assert glossary == [("SQL Server", "SQL Server"), ("SQL", "SQL")]


def test_mask_then_restore_roundtrip():
    glossary = parse_glossary("machine learning = học máy")

    masked = mask_terms("I love machine learning today", glossary)
    assert "machine learning" not in masked
    assert "<<T0>>" in masked

    restored = restore_terms(masked, glossary)
    assert restored == "I love học máy today"


def test_mask_is_case_insensitive():
    glossary = parse_glossary("GPU = GPU")

    masked = mask_terms("the gpu and the GPU", glossary)

    assert masked == "the <<T0>> and the <<T0>>"


def test_longer_term_masked_before_shorter_substring():
    glossary = parse_glossary("SQL = A\nSQL Server = B")

    masked = mask_terms("SQL Server uses SQL", glossary)
    restored = restore_terms(masked, glossary)

    assert restored == "B uses A"


def test_restore_tolerates_spaces_inside_token():
    glossary = parse_glossary("CPU = CPU")

    # Model dich co the chen khoang trang vao giua token.
    assert restore_terms("dung << T 0 >> nhe", glossary) == "dung CPU nhe"


def test_word_boundary_prevents_partial_match():
    glossary = parse_glossary("AI = trí tuệ nhân tạo")

    masked = mask_terms("PAINT is not AI", glossary)

    assert masked == "PAINT is not <<T0>>"
