import numpy as np

from app.services.qc_service import (
    calculate_brightness,
    calculate_contrast,
    calculate_ink_ratio,
)


def test_white_page_metrics():
    image = np.full((100, 100), 255, dtype=np.uint8)

    assert calculate_brightness(image) == 255.0
    assert calculate_contrast(image) == 0.0
    assert calculate_ink_ratio(image) == 0.0


def test_black_page_metrics():
    image = np.zeros((100, 100), dtype=np.uint8)

    assert calculate_brightness(image) == 0.0
    assert calculate_ink_ratio(image) == 1.0
