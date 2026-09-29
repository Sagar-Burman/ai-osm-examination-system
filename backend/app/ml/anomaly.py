from __future__ import annotations

from statistics import mean, stdev
from typing import Iterable


def z_score(value: float, values: Iterable[float]) -> float | None:
    numbers = [float(v) for v in values]
    if len(numbers) < 2:
        return None

    deviation = stdev(numbers)
    if deviation == 0:
        return 0.0

    return (float(value) - mean(numbers)) / deviation


def outlier(value: float, values: Iterable[float], threshold: float) -> float | None:
    score = z_score(value, values)
    if score is None:
        return None
    return score if abs(score) > threshold else None
