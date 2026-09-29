from app.ml.similarity import (
    SIMILARITY_THRESHOLD,
    clean_text,
    find_similar_pairs,
    token_count,
)


def test_clean_text_and_token_count():
    text = "Machine-Learning!!!  HELPS\nSYSTEMS."

    assert clean_text(text) == "machine learning helps systems"
    assert token_count(text) == 4


def test_short_answers_are_ignored():
    result = find_similar_pairs(
        [
            (1, "one two three"),
            (2, "one two three"),
        ]
    )

    assert result == []


def test_identical_long_answers_are_flagged_as_similar():
    answer = (
        "machine learning allows systems to learn patterns from data and "
        "make predictions or decisions without explicit programming. "
    ) * 4

    result = find_similar_pairs(
        [(16, answer), (17, answer)],
        threshold=SIMILARITY_THRESHOLD,
    )

    assert len(result) == 1
    assert result[0]["sheet_id"] == 16
    assert result[0]["related_sheet_id"] == 17
    assert result[0]["similarity"] >= SIMILARITY_THRESHOLD
    assert result[0]["token_count_a"] >= 40
    assert result[0]["token_count_b"] >= 40
