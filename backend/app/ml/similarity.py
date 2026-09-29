from __future__ import annotations

import re
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


MIN_TOKENS = 40
SIMILARITY_THRESHOLD = 0.85


def clean_text(text: str | None) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_count(text: str | None) -> int:
    return len(clean_text(text).split())


def find_similar_pairs(
    texts: Iterable[tuple[int, str]],
    *,
    threshold: float = SIMILARITY_THRESHOLD,
    min_tokens: int = MIN_TOKENS,
) -> list[dict]:
    """
    Compare answer text for the SAME question across sheets.

    `texts` contains one combined answer string per sheet for one question.
    """
    items = [
        (sheet_id, clean_text(text))
        for sheet_id, text in texts
        if token_count(text) >= min_tokens
    ]

    if len(items) < 2:
        return []

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([text for _, text in items])
    scores = cosine_similarity(matrix)

    pairs: list[dict] = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            score = float(scores[i, j])

            if score >= threshold:
                pairs.append(
                    {
                        "sheet_id": items[i][0],
                        "related_sheet_id": items[j][0],
                        "similarity": score,
                        "token_count_a": token_count(items[i][1]),
                        "token_count_b": token_count(items[j][1]),
                    }
                )

    return pairs
