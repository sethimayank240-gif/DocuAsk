from app.ingestion import clean_text, extract_pages


def test_private_use_bullets_become_visible_bullets():
    assert clean_text("a\uf0a7 b \uf0b7 c") == "a\u2022 b \u2022 c"
    assert clean_text("normal text 123") == "normal text 123"


def test_txt_is_cleaned_too():
    assert extract_pages("n.txt", "x \uf0a7 y".encode("utf-8")) == ["x \u2022 y"]